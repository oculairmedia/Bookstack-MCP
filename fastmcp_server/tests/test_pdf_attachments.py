"""Tests for the PDF/attachment tools (fastmcp_server.bookstack.tools_pdf_attachments)."""
from __future__ import annotations

import asyncio
import base64
import shutil
from io import BytesIO

import pytest
from fastmcp import FastMCP

import fastmcp_server.bookstack.tools_pdf_attachments as pdf
from fastmcp_server.bookstack.tools_pdf_attachments import register_pdf_attachment_tools


HAS_PDFTOTEXT = shutil.which("pdftotext") is not None


def _make_pdf_bytes(pages: int = 1) -> bytes:
    """Build a tiny valid PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    for i in range(pages):
        c.drawString(72, 720, f"Sample page {i + 1}")
        c.showPage()
    c.save()
    return buffer.getvalue()


def _tool_fns(mcp: FastMCP) -> dict:
    tools = asyncio.run(mcp.get_tools())
    return {name: t.fn for name, t in tools.items()}


@pytest.fixture()
def tools(monkeypatch, tmp_path):
    """Register PDF tools with /data redirected to a temp dir."""
    monkeypatch.setattr(pdf, "_ALLOWED_ROOT", tmp_path)
    mcp = FastMCP("test")
    register_pdf_attachment_tools(mcp)
    return _tool_fns(mcp), tmp_path


# --- path sandbox -----------------------------------------------------------

def test_safe_output_path_rejects_outside_root(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "_ALLOWED_ROOT", tmp_path)
    with pytest.raises(ValueError):
        pdf._safe_output_path("/etc/passwd", "output_path")


def test_safe_output_path_allows_within_root(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "_ALLOWED_ROOT", tmp_path)
    result = pdf._safe_output_path(str(tmp_path / "sub" / "file.pdf"), "output_path")
    assert str(result).startswith(str(tmp_path))


def test_safe_output_dir_creates_and_validates(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf, "_ALLOWED_ROOT", tmp_path)
    out = pdf._safe_output_dir(str(tmp_path / "nested"), "output_dir")
    assert out.is_dir()


# --- embedded attachment reference parsing ----------------------------------

def test_find_embedded_attachment_ids_dedup_and_variants():
    html = '<a href="/attachments/1">x</a> file=%2Fattachments%2F2 file=/attachments/1'
    markdown = "see /attachments/3 and /attachments/2"
    ids = pdf._find_embedded_attachment_ids(html, markdown, None)
    assert ids == [1, 2, 3]


# --- attachment fetch/decode ------------------------------------------------

def test_get_attachment_decodes_content(monkeypatch):
    raw = b"%PDF-1.4 fake"
    payload = {"id": 1, "name": "doc.pdf", "content": base64.b64encode(raw).decode()}
    monkeypatch.setattr(pdf, "_bookstack_request", lambda method, path: payload)
    meta, decoded = pdf._get_attachment(1)
    assert decoded == raw
    assert meta["name"] == "doc.pdf"


def test_get_attachment_missing_content_raises(monkeypatch):
    monkeypatch.setattr(pdf, "_bookstack_request", lambda method, path: {"id": 1})
    with pytest.raises(RuntimeError):
        pdf._get_attachment(1)


# --- tool: get_attachment_to_file -------------------------------------------

def test_get_attachment_to_file_writes_binary(tools, monkeypatch):
    fns, tmp_path = tools
    raw = _make_pdf_bytes()
    payload = {
        "id": 1,
        "name": "handbook.pdf",
        "extension": "pdf",
        "uploaded_to": 6,
        "content": base64.b64encode(raw).decode(),
    }
    monkeypatch.setattr(pdf, "_bookstack_request", lambda method, path: payload)

    out = str(tmp_path / "out" / "handbook.pdf")
    result = fns["bookstack_get_attachment_to_file"](attachment_id=1, output_path=out)

    assert result["bytes_written"] == len(raw)
    assert result["name"] == "handbook.pdf"
    assert (tmp_path / "out" / "handbook.pdf").read_bytes() == raw


def test_get_attachment_to_file_rejects_outside_data(tools, monkeypatch):
    fns, _ = tools
    monkeypatch.setattr(pdf, "_bookstack_request", lambda method, path: {})
    with pytest.raises(ValueError):
        fns["bookstack_get_attachment_to_file"](attachment_id=1, output_path="/etc/evil.pdf")


# --- tool: append_pdf_text_page ---------------------------------------------

def test_append_pdf_text_page_adds_one_page(tools):
    fns, tmp_path = tools
    src = tmp_path / "in.pdf"
    src.write_bytes(_make_pdf_bytes(pages=2))
    out = tmp_path / "out.pdf"

    result = fns["bookstack_append_pdf_text_page"](
        input_pdf_path=str(src),
        output_pdf_path=str(out),
        title="Summary",
        bullet_items=["a", "b", "c"],
    )
    assert result["original_page_count"] == 2
    assert result["output_page_count"] == 3
    assert out.exists()


def test_append_pdf_text_page_rejects_non_pdf(tools):
    fns, tmp_path = tools
    src = tmp_path / "notpdf.pdf"
    src.write_bytes(b"not a pdf")
    with pytest.raises(ValueError):
        fns["bookstack_append_pdf_text_page"](
            input_pdf_path=str(src),
            output_pdf_path=str(tmp_path / "out.pdf"),
            title="t",
            bullet_items=["x"],
        )


# --- pdftotext-dependent paths (skipped if poppler missing) -----------------

@pytest.mark.skipif(not HAS_PDFTOTEXT, reason="pdftotext (poppler-utils) not installed")
def test_extract_pdf_attachment_text_to_file(tools, monkeypatch):
    fns, tmp_path = tools
    raw = _make_pdf_bytes()
    payload = {"id": 1, "name": "doc.pdf", "content": base64.b64encode(raw).decode()}
    monkeypatch.setattr(pdf, "_bookstack_request", lambda method, path: payload)

    result = fns["bookstack_extract_pdf_attachment_text_to_file"](
        attachment_id=1,
        output_path=str(tmp_path / "doc.txt"),
        pdf_output_path=str(tmp_path / "doc.pdf"),
    )
    assert result["page_count"] == 1
    assert (tmp_path / "doc.txt").exists()
    assert (tmp_path / "doc.pdf").read_bytes() == raw
