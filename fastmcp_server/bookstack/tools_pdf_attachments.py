"""Safe, read-only BookStack attachment and PDF tools.

These tools fetch attachments through the authenticated BookStack API only
(GET /api/attachments/{id}), decode the base64 "content" field, and restrict
every file input/output path to /data. No write/delete BookStack API calls are
made and subprocess execution never uses shell=True.
"""

from __future__ import annotations

import base64
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from .api_client import _bookstack_request

_ALLOWED_ROOT = Path("/data")
_PDF_MAGIC = b"%PDF"

# Matches embedded attachment references in page html/markdown, e.g.
#   /attachments/12
#   file=%2Fattachments%2F12
#   file=/attachments/12
_ATTACHMENT_REF_PATTERNS = [
    re.compile(r"/attachments/(\d+)"),
    re.compile(r"file=%2[Ff]attachments%2[Ff](\d+)"),
    re.compile(r"file=/attachments/(\d+)"),
]


def _safe_output_path(path_str: str, field_name: str, *, must_exist: bool = False) -> Path:
    """Resolve a file path and require it to be under /data."""
    path = Path(path_str).resolve()
    allowed_root = _ALLOWED_ROOT.resolve()

    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError(f"{field_name} must be under /data")

    if must_exist and not path.is_file():
        raise FileNotFoundError(f"File does not exist: {path}")

    return path


def _safe_output_dir(path_str: str, field_name: str) -> Path:
    """Resolve a directory path under /data, creating it if necessary."""
    path = Path(path_str).resolve()
    allowed_root = _ALLOWED_ROOT.resolve()

    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError(f"{field_name} must be under /data")

    path.mkdir(parents=True, exist_ok=True)

    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    return path


def _get_attachment(attachment_id: int) -> tuple[dict[str, Any], bytes]:
    """Fetch an attachment via GET /api/attachments/{id} and decode its content.

    Returns a tuple of (attachment metadata dict, raw decoded bytes).
    """
    data = _bookstack_request("GET", f"/api/attachments/{attachment_id}")

    if not isinstance(data, dict):
        raise RuntimeError(f"Attachment {attachment_id} returned unexpected JSON")

    content = data.get("content")
    if content is None:
        raise RuntimeError(
            f"Attachment {attachment_id} response missing 'content' field "
            "(is it a link attachment rather than an uploaded file?)"
        )

    try:
        raw = base64.b64decode(content, validate=False)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to base64-decode content for attachment {attachment_id}: {exc}"
        ) from exc

    return data, raw


def _run_pdftotext(pdf_path: Path, txt_path: Path) -> list[str]:
    """Run pdftotext without shell=True. Returns the command that was executed."""
    command = ["pdftotext", str(pdf_path), str(txt_path)]
    try:
        subprocess.run(
            command,
            shell=False,
            check=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pdftotext binary not found (poppler-utils must be installed)"
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        raise RuntimeError(f"pdftotext failed: {stderr.strip()}") from exc

    return command


def _pdf_page_count(pdf_path: Path) -> Optional[int]:
    """Return the number of pages in a PDF, or None if it cannot be determined."""
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass

    # Fallback to poppler's pdfinfo if pypdf is unavailable or fails.
    try:
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)],
            shell=False,
            check=True,
            capture_output=True,
        )
        for line in result.stdout.decode("utf-8", errors="replace").splitlines():
            if line.lower().startswith("pages:"):
                return int(line.split(":", 1)[1].strip())
    except Exception:
        pass

    return None


def _extract_pdf_and_text(
    attachment_id: int,
    pdf_path: Path,
    txt_path: Path,
) -> dict[str, Any]:
    """Shared internal: fetch a PDF attachment, write PDF + extracted text.

    Assumes pdf_path and txt_path have already been validated under /data.
    Raises if the attachment does not look like a PDF.
    """
    meta, raw = _get_attachment(attachment_id)

    if not raw.startswith(_PDF_MAGIC):
        raise ValueError(
            f"Attachment {attachment_id} does not look like a PDF "
            f"(first bytes: {raw[:8].hex()})"
        )

    pdf_bytes = pdf_path.write_bytes(raw)
    command = _run_pdftotext(pdf_path, txt_path)
    text_bytes = txt_path.stat().st_size
    page_count = _pdf_page_count(pdf_path)

    return {
        "attachment_id": attachment_id,
        "name": meta.get("name"),
        "pdf_path": str(pdf_path),
        "text_path": str(txt_path),
        "pdf_bytes": pdf_bytes,
        "text_bytes": text_bytes,
        "page_count": page_count,
        "command": command,
    }


def _find_embedded_attachment_ids(*sources: Optional[str]) -> list[int]:
    """Extract and de-duplicate attachment IDs from html/markdown sources."""
    seen: dict[int, None] = {}
    for source in sources:
        if not source:
            continue
        for pattern in _ATTACHMENT_REF_PATTERNS:
            for match in pattern.finditer(source):
                seen.setdefault(int(match.group(1)), None)
    return list(seen.keys())


def register_pdf_attachment_tools(mcp) -> None:
    @mcp.tool()
    def bookstack_get_attachment_to_file(
        attachment_id: int,
        output_path: str,
    ) -> dict[str, Any]:
        """
        Download a BookStack attachment to a file under /data.

        Fetches GET /api/attachments/{attachment_id}, base64-decodes the JSON
        "content" field, and writes the raw bytes to output_path.
        """
        path = _safe_output_path(output_path, "output_path")
        meta, raw = _get_attachment(attachment_id)

        path.parent.mkdir(parents=True, exist_ok=True)
        bytes_written = path.write_bytes(raw)

        return {
            "attachment_id": attachment_id,
            "name": meta.get("name"),
            "extension": meta.get("extension"),
            "uploaded_to": meta.get("uploaded_to"),
            "output_path": str(path),
            "bytes_written": bytes_written,
            "first_bytes_hex": raw[:16].hex(),
        }

    @mcp.tool()
    def bookstack_extract_pdf_attachment_text_to_file(
        attachment_id: int,
        output_path: str,
        pdf_output_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Extract text from a PDF attachment to a file under /data.

        Fetches the attachment, confirms it is a PDF, writes the PDF (to
        pdf_output_path if provided, otherwise a derived /data filename), and
        runs pdftotext to produce output_path.
        """
        text_path = _safe_output_path(output_path, "output_path")

        if pdf_output_path is not None:
            pdf_path = _safe_output_path(pdf_output_path, "pdf_output_path")
        else:
            pdf_path = _safe_output_path(
                str(_ALLOWED_ROOT / f"bookstack-attachment-{attachment_id}.pdf"),
                "pdf_output_path",
            )

        text_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        return _extract_pdf_and_text(attachment_id, pdf_path, text_path)

    @mcp.tool()
    def bookstack_extract_embedded_page_pdfs(
        page_id: int,
        output_dir: str,
    ) -> dict[str, Any]:
        """
        Extract all embedded PDF attachments from a BookStack page.

        Reads GET /api/pages/{page_id}, scans html/markdown for embedded
        attachment references, and for each PDF attachment writes a PDF and
        extracted text file under output_dir using deterministic names.
        """
        out_dir = _safe_output_dir(output_dir, "output_dir")

        page = _bookstack_request("GET", f"/api/pages/{page_id}")
        if not isinstance(page, dict):
            raise RuntimeError(f"Page {page_id} returned unexpected JSON")

        attachment_ids = _find_embedded_attachment_ids(
            page.get("html"),
            page.get("markdown"),
            page.get("raw_html"),
        )

        outputs: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        for attachment_id in attachment_ids:
            pdf_path = out_dir / f"bookstack-page-{page_id}-attachment-{attachment_id}.pdf"
            txt_path = out_dir / f"bookstack-page-{page_id}-attachment-{attachment_id}.txt"
            try:
                outputs.append(_extract_pdf_and_text(attachment_id, pdf_path, txt_path))
            except Exception as exc:
                skipped.append(
                    {
                        "attachment_id": attachment_id,
                        "reason": str(exc),
                    }
                )

        return {
            "page_id": page_id,
            "attachment_ids": attachment_ids,
            "outputs": outputs,
            "skipped": skipped,
        }

    @mcp.tool()
    def bookstack_append_pdf_text_page(
        input_pdf_path: str,
        output_pdf_path: str,
        title: str,
        bullet_items: list[str],
    ) -> dict[str, Any]:
        """
        Append a final text page (title + bullet points) to a PDF under /data.

        Reads input_pdf_path, builds a new final page with reportlab, merges it
        onto the original with pypdf, and writes output_pdf_path.
        """
        from io import BytesIO

        from pypdf import PdfReader, PdfWriter
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        in_path = _safe_output_path(input_pdf_path, "input_pdf_path", must_exist=True)
        out_path = _safe_output_path(output_pdf_path, "output_pdf_path")

        with in_path.open("rb") as handle:
            if handle.read(4) != _PDF_MAGIC:
                raise ValueError(f"{in_path} does not begin with %PDF")

        reader = PdfReader(str(in_path))
        original_page_count = len(reader.pages)

        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        y = height - inch
        pdf_canvas.setFont("Helvetica-Bold", 16)
        pdf_canvas.drawString(inch, y, title)

        y -= 0.5 * inch
        pdf_canvas.setFont("Helvetica", 11)
        for item in bullet_items:
            if y < inch:
                pdf_canvas.showPage()
                pdf_canvas.setFont("Helvetica", 11)
                y = height - inch
            pdf_canvas.drawString(inch, y, f"\u2022 {item}")
            y -= 0.3 * inch

        pdf_canvas.showPage()
        pdf_canvas.save()
        buffer.seek(0)

        overlay_reader = PdfReader(buffer)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in overlay_reader.pages:
            writer.add_page(page)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as handle:
            writer.write(handle)

        bytes_written = out_path.stat().st_size
        output_page_count = len(PdfReader(str(out_path)).pages)

        return {
            "input_pdf_path": str(in_path),
            "output_pdf_path": str(out_path),
            "original_page_count": original_page_count,
            "output_page_count": output_page_count,
            "bytes_written": bytes_written,
        }
