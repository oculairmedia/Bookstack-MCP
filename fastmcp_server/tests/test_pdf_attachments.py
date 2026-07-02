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


# --- viewer/iframe builders -------------------------------------------------

def test_viewer_url_uses_attachment_path():
    url = pdf._viewer_url(42)
    assert url.endswith("?file=%2Fattachments%2F42")
    assert "data%3Aapplication" not in url


def test_build_iframe_block_references_attachment_never_data_url():
    block = pdf._build_iframe_block(42, "Reviewed copy")
    assert "src=\"" in block
    assert "%2Fattachments%2F42" in block
    assert "data:application/pdf;base64" not in block
    assert block.startswith("<p>Reviewed copy:</p>")


# --- tool: upload_attachment_from_file --------------------------------------

def test_upload_attachment_from_file(tools, monkeypatch):
    fns, tmp_path = tools
    captured = {}

    def fake_form(method, path, *, data=None, files=None):
        captured["method"] = method
        captured["path"] = path
        captured["data"] = data
        captured["files"] = files
        return {"id": 99, "name": "review.pdf", "extension": "pdf", "uploaded_to": 6}

    monkeypatch.setattr(pdf, "_bookstack_request_form", fake_form)
    monkeypatch.setattr(pdf, "_invalidate_entity_cache", lambda *a, **k: None)

    src = tmp_path / "review.pdf"
    src.write_bytes(_make_pdf_bytes())

    result = fns["bookstack_upload_attachment_from_file"](page_id=6, file_path=str(src))

    assert captured["method"] == "POST"
    assert captured["path"] == "/api/attachments"
    assert captured["data"] == {"name": "review", "uploaded_to": "6"}
    assert "file" in captured["files"]
    assert result["attachment_id"] == 99
    assert result["attachment_path"] == "/attachments/99"
    assert result["viewer_url"].endswith("%2Fattachments%2F99")


# --- tool: embed_pdf_attachment_on_page -------------------------------------

def _fake_page_request(page):
    """Return a _bookstack_request stand-in over a mutable page dict."""
    captured = {}

    def fake(method, path, *, params=None, json=None):
        if method == "GET":
            return page
        captured["put_payload"] = json
        return {"success": True}

    return fake, captured


def test_embed_requires_confirm_update(tools, monkeypatch):
    fns, _ = tools
    called = {"n": 0}
    monkeypatch.setattr(pdf, "_bookstack_request", lambda *a, **k: called.__setitem__("n", called["n"] + 1))

    result = fns["bookstack_embed_pdf_attachment_on_page"](page_id=6, attachment_id=99)
    assert result["updated"] is False
    assert "confirm_update" in result["error"]
    assert called["n"] == 0


def test_embed_appends_and_preserves_original(tools, monkeypatch):
    fns, _ = tools
    page = {"name": "Handbook", "markdown": "Intro\n\n/attachments/1 original"}
    fake, captured = _fake_page_request(page)
    monkeypatch.setattr(pdf, "_bookstack_request", fake)
    monkeypatch.setattr(pdf, "_invalidate_entity_cache", lambda *a, **k: None)

    result = fns["bookstack_embed_pdf_attachment_on_page"](
        page_id=6, attachment_id=99, confirm_update=True
    )

    put = captured["put_payload"]
    assert "markdown" in put  # preserved source field
    assert "%2Fattachments%2F99" in put["markdown"]
    assert "/attachments/1" in put["markdown"]  # original iframe preserved
    assert result["updated"] is True
    assert result["replaced_existing"] is False
    assert result["original_iframe_preserved"] is True


def test_embed_replace_existing_only_reviewed_section(tools, monkeypatch):
    fns, _ = tools
    label = "Reviewed copy with suggested changes appended"
    prior = (
        "<p>Original</p>\n"
        '<p><iframe src="https://x/viewer.html?file=%2Fattachments%2F1"></iframe></p>\n\n'
        + pdf._build_iframe_block(50, label)
    )
    page = {"name": "Handbook", "html": prior, "markdown": ""}
    fake, captured = _fake_page_request(page)
    monkeypatch.setattr(pdf, "_bookstack_request", fake)
    monkeypatch.setattr(pdf, "_invalidate_entity_cache", lambda *a, **k: None)

    result = fns["bookstack_embed_pdf_attachment_on_page"](
        page_id=6, attachment_id=99, replace_existing=True, confirm_update=True
    )

    put = captured["put_payload"]
    assert "html" in put
    assert "%2Fattachments%2F99" in put["html"]
    assert "%2Fattachments%2F50" not in put["html"]  # prior reviewed section replaced
    assert "%2Fattachments%2F1" in put["html"]  # original preserved
    assert result["replaced_existing"] is True
    assert result["original_iframe_preserved"] is True
