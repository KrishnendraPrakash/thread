"""Native Windows core and frozen protocol fixtures; no VS Code UI or real model."""

import json
import os
import subprocess
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from thread_agent.domain.records import AgentError
from thread_agent.editor.documents import extract
from thread_agent.editor.proposals import proposal, validate
from thread_agent.editor.workspace import Repository


@unittest.skipUnless(os.name == "nt", "Requires real Windows handle semantics")
class WindowsEditorFixtures(unittest.TestCase):
    def test_document_ranges_and_linked_documents_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "notes.md"
            path.write_text("one\ntwo\nthree\n", encoding="utf-8")
            self.assertEqual(extract(str(path), "2-3")[0][0]["text"], "two\nthree")
            os.link(path, root / "linked.md")
            with self.assertRaises(AgentError):
                extract(str(path))

    def test_reserved_creation_and_stale_proposals_never_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "app.py"
            path.write_text("value = 1\n")
            repository = Repository(str(root))
            repository.scan()
            sources = repository.retrieve("value")
            for name in ("CON.py", "name:stream.py", "../outside.py"):
                with self.assertRaises(AgentError):
                    proposal(
                        repository, [{"path": name, "old_text": "", "new_text": "x=1"}], sources
                    )
            value = proposal(
                repository,
                [{"path": "app.py", "old_text": "value = 1", "new_text": "value = 2"}],
                sources,
            )
            self.assertTrue(validate(str(root), value)["valid"])
            self.assertEqual(path.read_text(), "value = 1\n")
            path.write_text("value = 3\n")
            with self.assertRaises(AgentError):
                validate(str(root), value)
            self.assertEqual(path.read_text(), "value = 3\n")


@unittest.skipUnless(
    os.environ.get("THREAD_NATIVE_EDITOR_TEST_EXE"),
    "Requires an explicitly selected built native backend",
)
class NativeEditorProtocolFixtures(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.calls = []
        calls = self.calls

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                self.respond(
                    {"models": [{"name": "fixture:local", "digest": "synthetic"}]}
                    if self.path == "/api/tags"
                    else {"version": "synthetic"}
                )

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/api/show":
                    self.respond({"capabilities": ["completion"], "template": ""})
                    return
                context = json.loads(request["messages"][1]["content"])
                calls.append(context)
                source = context["sources"][0]
                changes = (
                    [{"path": "app.py", "old_text": "return a - b", "new_text": "return a + b"}]
                    if context["mode"] == "feature"
                    else []
                )
                answer = {
                    "claims": [{"text": source["text"], "source_ids": [source["id"]]}],
                    "uncertainties": ["Synthetic fixture response, not real inference."],
                    "suggested_checks": [],
                    "changes": changes,
                }
                self.respond(
                    {
                        "done": True,
                        "done_reason": "stop",
                        "message": {"content": json.dumps(answer)},
                    }
                )

            def respond(self, data):
                body = json.dumps(data).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def call(self, request):
        environment = {
            **os.environ,
            "PATH": "/nonexistent/thread-no-system-python",
            "PYTHONPATH": "/nonexistent",
            "PYTHONHOME": "/nonexistent",
        }
        process = subprocess.run(
            [os.environ["THREAD_NATIVE_EDITOR_TEST_EXE"]],
            input=json.dumps({"model": "fixture:local", "endpoint": self.endpoint, **request})
            + "\n",
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )
        envelope = json.loads(process.stdout)
        self.assertEqual(process.returncode == 0, envelope["ok"], process.stderr)
        return envelope

    def test_native_proposal_validation_and_staleness_have_no_effect(self):
        path = self.root / "app.py"
        content = "def add(a,b):\n    return a - b\n"
        path.write_text(content)
        (self.root / ".env").write_text("TOKEN=synthetic-secret-exclusion-fixture")
        envelope = self.call(
            {
                "operation": "run",
                "mode": "feature",
                "root": str(self.root),
                "active": str(path),
                "prompt": "Fix the subtraction in add.",
            }
        )
        self.assertTrue(envelope["ok"], envelope)
        value = envelope["result"]["proposal"]
        self.assertEqual(path.read_text(), content)
        self.assertNotIn("TOKEN", json.dumps(self.calls))
        self.assertTrue(
            self.call({"operation": "validate", "root": str(self.root), "proposal": value})["ok"]
        )
        path.write_text("changed after review\n")
        self.assertFalse(
            self.call({"operation": "validate", "root": str(self.root), "proposal": value})["ok"]
        )
        self.assertEqual(path.read_text(), "changed after review\n")

    def test_native_docx_summary_and_entity_rejection(self):
        path = self.root / "notes.docx"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Fixture document.</w:t></w:r></w:p></w:body></w:document>',
            )
        request = {
            "operation": "run",
            "mode": "summary",
            "document": str(path),
            "selection": "1-1",
            "prompt": "Summarize the selected paragraph.",
        }
        result = self.call(request)
        self.assertTrue(result["ok"], result)
        self.assertIn("Fixture document.", result["result"]["sources"][0]["text"])
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", '<!DOCTYPE x [<!ENTITY y "bad">]><x>&y;</x>')
        self.assertFalse(self.call(request)["ok"])

    def test_native_blank_pdf_and_remote_endpoint_rejection(self):
        from pypdf import PdfWriter

        path = self.root / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        writer.write(path)
        result = self.call(
            {
                "operation": "run",
                "mode": "summary",
                "document": str(path),
                "prompt": "Summarize this PDF.",
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("No text", result["error"])
        result = self.call({"operation": "models", "endpoint": "https://example.com"})
        self.assertFalse(result["ok"])
        self.assertIn("loopback", result["error"])
