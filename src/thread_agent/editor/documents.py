"""Explicit document ingestion; no OCR, macros, or external resource loading."""

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from thread_agent.domain.records import AgentError, digest
from thread_agent.editor.workspace import decode, read_bytes

MAX_DOCUMENT = 8 * 1024 * 1024
MAX_TEXT = 32000


def extract(filename: str, selection: str = "") -> tuple[list[dict], dict]:
    path = Path(filename)
    if not path.is_absolute() or path.is_symlink():
        raise AgentError("Choose an absolute, regular document path without symlinks.")
    # Resolve parents once for an explicitly selected document, then use no-follow reads.
    root = path.parent.resolve(strict=True)
    raw = read_bytes(root, path.name, MAX_DOCUMENT, internal=True)
    suffix = path.suffix.lower()
    units: list[str]
    unit = "line"
    notes = []
    if suffix == ".docx":
        unit = "paragraph"
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                info = archive.getinfo("word/document.xml")
                if info.file_size > 2 * 1024 * 1024:
                    raise AgentError("DOCX main content exceeds the 2 MiB extraction limit.")
                xml = archive.read(info)
            if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                raise AgentError("XML entities and document type declarations are not accepted.")
            tree = ElementTree.fromstring(xml)
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            units = [
                "".join(t.text or "" for t in p.iter(namespace + "t"))
                for p in tree.iter(namespace + "p")
            ]
            notes.append("DOCX main-body text only; headers, footnotes, images and layout omitted.")
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, RuntimeError) as exc:
            raise AgentError("Cannot extract this DOCX document.") from exc
    elif suffix == ".pdf":
        unit = "page"
        try:
            from pypdf import PdfReader, overwrite_configuration

            overwrite_configuration(
                maximum_declared_stream_length=2 * 1024 * 1024,
                array_based_stream_maximum_output_length=2 * 1024 * 1024,
                zlib_maximum_output_length=2 * 1024 * 1024,
                lzw_maximum_output_length=2 * 1024 * 1024,
                run_length_maximum_output_length=2 * 1024 * 1024,
                page_tree_maximum_entries=1000,
                xform_maximum_invocations_per_extraction=100,
                jbig2dec_binary=None,
                disable_legacy_handling=True,
            )
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted:
                raise AgentError("Encrypted PDFs are not supported.")
            if len(reader.pages) > 200:
                raise AgentError("PDF exceeds 200 pages; export a smaller document first.")
            start, end = selected_range(selection, len(reader.pages))
            units = []
            for index in range(start - 1, end):
                page = reader.pages[index]
                contents = page.get_contents()
                if contents is not None and len(contents.get_data()) > 2 * 1024 * 1024:
                    raise AgentError("A PDF page exceeds the extraction limit.")
                units.append(page.extract_text() or "")
                if sum(len(s.encode()) for s in units) > MAX_TEXT:
                    raise AgentError("Selected PDF text is too large; choose a smaller page range.")
            notes.append(
                "PDF extracted text only; no OCR, image interpretation or layout guarantee."
            )
            return chunks(units, path, digest(raw), unit, start, len(reader.pages), notes)
        except ImportError as exc:
            raise AgentError("Install the editor extra to extract PDFs.") from exc
        except AgentError:
            raise
        except Exception as exc:
            # The parser exposes several distinct malformed-document exception families.
            raise AgentError("PDF extraction failed; use a text export or a smaller PDF.") from exc
    else:
        if suffix not in {".txt", ".md", ".rst", ".csv", ".log", ".json", ".yaml", ".yml", ".toml"}:
            raise AgentError(
                "Supported documents: UTF-8 text/Markdown/CSV/log/config, PDF and DOCX."
            )
        units = decode(raw).splitlines()
    start, end = selected_range(selection, len(units))
    return chunks(units[start - 1 : end], path, digest(raw), unit, start, len(units), notes)


def selected_range(selection: str, total: int) -> tuple[int, int]:
    if total == 0:
        raise AgentError("Document has no extractable text.")
    if not selection:
        return 1, total
    match = re.fullmatch(r"([1-9][0-9]*)-([1-9][0-9]*)", selection)
    if not match:
        raise AgentError("Use a one-based inclusive range such as 1-10, or leave it empty.")
    start, end = map(int, match.groups())
    if not 1 <= start <= end <= total:
        raise AgentError(f"Range is outside this document's {total} units.")
    return start, end


def chunks(
    units: list[str], path: Path, sha: str, unit: str, start: int, total: int, notes: list[str]
) -> tuple[list[dict], dict]:
    if not any(text.strip() for text in units):
        raise AgentError("No text in the selected range; scanned PDFs need an external OCR export.")
    if sum(len(text.encode()) for text in units) > MAX_TEXT:
        raise AgentError("Selected text exceeds 32,000 bytes; choose a smaller range.")
    result = []
    for offset, text in enumerate(units):
        # Character splits stay below the byte budget even for four-byte Unicode.
        for index in range(0, len(text), 1000):
            part = text[index : index + 1000]
            number = start + offset
            if result and len((result[-1]["text"] + part).encode()) < 4500:
                result[-1]["text"] += "\n" + part
                result[-1]["end_unit"] = number
            else:
                result.append(
                    {
                        "id": f"D{len(result) + 1}",
                        "path": str(path),
                        "text": part,
                        "sha256": sha,
                        "unit": unit,
                        "start_unit": number,
                        "end_unit": number,
                    }
                )
    if len(result) > 12:
        raise AgentError("Document needs more than 12 summary sections; choose a smaller range.")
    return result, {
        "document": str(path),
        "unit": unit,
        "start": start,
        "end": start + len(units) - 1,
        "total": total,
        "notes": notes,
    }
