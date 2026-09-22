import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from thread_agent.domain.records import AgentError
from thread_agent.editor.documents import extract
from thread_agent.editor.engine import Analyst, run, validate_answer
from thread_agent.editor.proposals import proposal, validate
from thread_agent.editor.workspace import Repository, read_bytes


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "app.py").write_text("def add(a, b):\n    return a - b\n")

    def repository(self):
        repo = Repository(str(self.root))
        repo.scan()
        return repo

    def test_nested_ignore_negation_and_boundaries(self):
        (self.root / ".gitignore").write_text("ignored/\n*.log\n")
        (self.root / "ignored").mkdir()
        (self.root / "ignored/private.py").write_text("do not read")
        (self.root / "src").mkdir()
        (self.root / "src/.gitignore").write_text("*.py\n!keep.py\n")
        for name in ("drop.py", "keep.py"):
            (self.root / "src" / name).write_text("value = 1")
        (self.root / ".env").write_text("TOKEN=synthetic")
        (self.root / "credentials.json").write_text("{}")
        (self.root / "link.py").symlink_to(self.root / "app.py")
        repo = self.repository()
        self.assertEqual(set(repo.sources), {"app.py", "src/keep.py"})

    def test_hardlink_and_traversal_rejected(self):
        os.link(self.root / "app.py", self.root / "copy.py")
        for path in ("app.py", "../outside.py", "/tmp/outside.py"):
            with self.assertRaises(AgentError):
                read_bytes(self.root, path)

    def test_linked_ignore_fails_closed(self):
        (self.root / ".gitignore").symlink_to(self.root / "app.py")
        with self.assertRaises(AgentError):
            self.repository()

    def test_retrieval_has_exact_line_locators(self):
        repo = self.repository()
        sources = repo.retrieve("add subtraction bug", "app.py")
        source = sources[0]
        lines = repo.sources[source["path"]].text.splitlines()
        self.assertEqual(
            source["text"], "\n".join(lines[source["start_line"] - 1 : source["end_line"]])
        )

    def patch(self):
        repo = self.repository()
        sources = repo.retrieve("add")
        change = {"path": "app.py", "old_text": "return a - b", "new_text": "return a + b"}
        return proposal(repo, [change], sources)

    def test_proposal_never_writes_and_stale_rejected(self):
        value = self.patch()
        self.assertTrue(validate(str(self.root), value)["valid"])
        self.assertIn("return a - b", (self.root / "app.py").read_text())
        (self.root / "app.py").write_text("changed")
        with self.assertRaises(AgentError):
            validate(str(self.root), value)

    def test_changed_proposal_hash_rejected(self):
        value = self.patch()
        value["files"][0]["after"] = "unapproved"
        with self.assertRaises(AgentError):
            validate(str(self.root), value)

    def test_new_file_and_changed_ignore_rejected(self):
        repo = self.repository()
        value = proposal(
            repo,
            [{"path": "new.py", "old_text": "", "new_text": "value = 1\n"}],
            repo.retrieve("add"),
        )
        self.assertTrue(validate(str(self.root), value)["valid"])
        (self.root / ".gitignore").write_text("new.py\n")
        with self.assertRaises(AgentError):
            validate(str(self.root), value)

    def test_ignored_parent_cannot_be_reincluded_by_child_rule(self):
        (self.root / "ignored").mkdir()
        (self.root / ".gitignore").write_text("ignored/\n!ignored/new.py\n")
        (self.root / "ignored/.gitignore").write_text("!new.py\n")
        repo = self.repository()
        with self.assertRaises(AgentError):
            proposal(
                repo,
                [{"path": "ignored/new.py", "old_text": "", "new_text": "x = 1"}],
                repo.retrieve("add"),
            )

    def test_no_unseen_or_ambiguous_edit(self):
        repo = self.repository()
        for change in [
            {"path": "app.py", "old_text": "a", "new_text": "b"},
            {"path": "../evil.py", "old_text": "", "new_text": "x"},
            {"path": ".env", "old_text": "", "new_text": "x"},
        ]:
            with self.assertRaises(AgentError):
                proposal(repo, [change], repo.retrieve("add"))
        with self.assertRaises(AgentError):
            proposal(repo, [{"path": "app.py", "old_text": "return a - b", "new_text": "pass"}], [])

    def test_context_budget_removes_whole_excerpts_and_preserves_question(self):
        answer = {
            "claims": [{"text": "Unverified", "source_ids": ["S1"]}],
            "uncertainties": [],
            "suggested_checks": [],
            "changes": [],
        }

        class Client:
            def request(self, path, payload):
                data = {
                    "done": True,
                    "done_reason": "stop",
                    "message": {"content": json.dumps(answer)},
                }
                return data, json.dumps(data)

        analyst = Analyst.__new__(Analyst)
        analyst.client, analyst.model, analyst.template, analyst.trace = (
            Client(),
            "fake",
            "x" * 6500,
            [],
        )
        context = {
            "mode": "ask",
            "question": "Keep this exact question",
            "sources": [{"id": f"S{i}", "text": "a" * 2000} for i in range(1, 5)],
        }
        analyst.analyze(context)
        self.assertLess(len(context["sources"]), 4)
        self.assertGreaterEqual(len(context["sources"]), 1)
        recorded = json.loads(analyst.trace[0]["request"]["messages"][1]["content"])
        self.assertEqual(recorded["question"], "Keep this exact question")
        self.assertEqual(recorded["sources"], context["sources"])

    def test_source_ids_and_mode_are_enforced(self):
        answer = {
            "claims": [{"text": "Model interpretation", "source_ids": ["S1"]}],
            "uncertainties": [],
            "suggested_checks": [],
            "changes": [],
        }
        validate_answer(answer, [{"id": "S1"}], "ask")
        bad = copy.deepcopy(answer)
        bad["claims"][0]["source_ids"] = ["invented"]
        with self.assertRaises(AgentError):
            validate_answer(bad, [{"id": "S1"}], "ask")
        answer["changes"] = [{}]
        with self.assertRaises(AgentError):
            validate_answer(answer, [{"id": "S1"}], "ask")

    def test_mocked_repository_workflow_is_scoped_and_has_no_effect(self):
        class FakeAnalyst:
            def __init__(self, model):
                self.trace = [{"type": "synthetic", "model": model}]

            def analyze(self, context):
                return {
                    "claims": [{"text": "add subtracts its arguments.", "source_ids": ["S1"]}],
                    "uncertainties": ["Behavior not executed."],
                    "suggested_checks": ["Test add(2, 3)."],
                    "changes": [
                        {"path": "app.py", "old_text": "return a - b", "new_text": "return a + b"}
                    ],
                }

        result = run(
            {"root": str(self.root), "mode": "feature", "prompt": "Fix addition", "model": "fake"},
            FakeAnalyst,
        )
        self.assertEqual(result["decision"], "pending")
        self.assertIn("not independently verified", result["status"])
        self.assertIn("return a - b", (self.root / "app.py").read_text())

    def test_document_text_ranges_and_size(self):
        path = self.root / "notes.md"
        path.write_text("one\ntwo\nthree\n")
        sources, coverage = extract(str(path), "2-3")
        self.assertEqual(sources[0]["text"], "two\nthree")
        self.assertEqual(coverage["start"], 2)
        with self.assertRaises(AgentError):
            extract(str(path), "1-99")
        path.write_text("a" * 33000)
        with self.assertRaises(AgentError):
            extract(str(path))

    def test_docx_and_entity_rejection(self):
        path = self.root / "notes.docx"

        def write(xml):
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)

        write(
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello world.</w:t></w:r></w:p></w:body></w:document>'
        )
        self.assertEqual(extract(str(path))[0][0]["text"], "Hello world.")
        write('<!DOCTYPE x [<!ENTITY y "bad">]><x>&y;</x>')
        with self.assertRaises(AgentError):
            extract(str(path))

    def test_pdf_text_and_page_locator(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 20 250 Td (Thread fixture document) Tj ET")
        page[NameObject("/Contents")] = stream
        path = self.root / "text.pdf"
        writer.write(path)
        sources, coverage = extract(str(path), "1-1")
        self.assertIn("Thread fixture document", sources[0]["text"])
        self.assertEqual(sources[0]["unit"], "page")
        self.assertEqual(coverage["total"], 1)

    def test_blank_pdf_requires_ocr_and_bad_pdf_fails(self):
        from pypdf import PdfWriter

        path = self.root / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        stream = io.BytesIO()
        writer.write(stream)
        path.write_bytes(stream.getvalue())
        with self.assertRaisesRegex(AgentError, "No text"):
            extract(str(path))
        path.write_bytes(b"not a pdf")
        with self.assertRaisesRegex(AgentError, "extraction failed"):
            extract(str(path))

    def test_service_rejects_unknown_operation_without_model(self):
        proc = subprocess.run(
            [sys.executable, "-m", "thread_agent.editor.service"],
            input=json.dumps({"operation": "execute_shell"}) + "\n",
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(json.loads(proc.stdout)["ok"])
