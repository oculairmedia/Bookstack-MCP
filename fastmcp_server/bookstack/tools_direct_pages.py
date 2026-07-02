from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from .api_client import _bookstack_request, _invalidate_entity_cache


# Matches an embedded PDF data URL in any of its plain or URL-encoded forms,
# e.g. data:application/pdf;base64 or file=data%3Aapplication%2Fpdf%3Bbase64
# (including mixed encodings). Embedding PDF bytes in page content is forbidden;
# PDFs must be uploaded as BookStack attachments and referenced by /attachments/{id}.
_PDF_DATA_URL_RE = re.compile(
    r"data(?::|%3a)application(?:/|%2f)pdf(?:;|%3b)base64",
    re.IGNORECASE,
)
_PDF_DATA_URL_MSG = (
    "Refusing to update BookStack page with embedded PDF data URL. "
    "Upload the PDF as a BookStack attachment and embed /attachments/{id} instead."
)


def _reject_pdf_data_url(content: str) -> None:
    """Raise if page content embeds a PDF as a data URL instead of an attachment."""
    if content and _PDF_DATA_URL_RE.search(content):
        raise ValueError(_PDF_DATA_URL_MSG)


def _safe_markdown_path(markdown_path: str) -> Path:
    path = Path(markdown_path).resolve()
    allowed_root = Path("/data").resolve()

    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError("markdown_path must be under /data")

    if not path.is_file():
        raise FileNotFoundError(f"Markdown file does not exist: {path}")

    return path


def _created_page_id(response: Any) -> Optional[int]:
    if isinstance(response, dict) and isinstance(response.get("id"), int):
        return response["id"]
    return None


def register_direct_page_tools(mcp) -> None:
    @mcp.tool()
    def bookstack_create_page_direct(
        name: str,
        book_id: int,
        markdown: str,
        chapter_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Create a BookStack page using direct typed arguments.

        Prefer this over manage_content/bookstack_content_crud for page creation.
        """
        _reject_pdf_data_url(markdown)
        payload: dict[str, Any] = {
            "name": name,
            "book_id": book_id,
            "markdown": markdown,
        }

        if chapter_id is not None:
            payload["chapter_id"] = chapter_id

        response = _bookstack_request("POST", "/api/pages", json=payload)
        _invalidate_entity_cache("page", _created_page_id(response))
        return response

    @mcp.tool()
    def bookstack_update_page_direct(
        page_id: int,
        name: str,
        markdown: str,
    ) -> dict[str, Any]:
        """
        Update a BookStack page using direct typed arguments.

        This replaces the entire page body with `markdown`. For large edits
        (roughly > 50 KB of markdown), prefer `bookstack_update_page_from_file`:
        write the content to a file under /data and pass its path. That avoids
        embedding a huge string in the tool call (which some MCP clients
        truncate or reject) and is more reliable for big pages.
        """
        _reject_pdf_data_url(markdown)
        payload = {
            "name": name,
            "markdown": markdown,
        }

        response = _bookstack_request("PUT", f"/api/pages/{page_id}", json=payload)
        _invalidate_entity_cache("page", page_id)
        return response

    @mcp.tool()
    def bookstack_create_page_from_file(
        name: str,
        book_id: int,
        markdown_path: str,
        chapter_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Create a BookStack page from a Markdown file under /data.

        Use this for long operational documentation.
        """
        path = _safe_markdown_path(markdown_path)
        markdown = path.read_text(encoding="utf-8")
        _reject_pdf_data_url(markdown)

        payload: dict[str, Any] = {
            "name": name,
            "book_id": book_id,
            "markdown": markdown,
        }

        if chapter_id is not None:
            payload["chapter_id"] = chapter_id

        response = _bookstack_request("POST", "/api/pages", json=payload)
        _invalidate_entity_cache("page", _created_page_id(response))
        return response

    @mcp.tool()
    def bookstack_update_page_from_file(
        page_id: int,
        name: str,
        markdown_path: str,
    ) -> dict[str, Any]:
        """
        Update a BookStack page from a Markdown file under /data.

        Preferred for large page edits: the content is read from disk instead of
        being passed inline, so there is no tool-call payload size limit. Write
        the new markdown to a file under /data first, then pass its path here.
        """
        path = _safe_markdown_path(markdown_path)
        markdown = path.read_text(encoding="utf-8")
        _reject_pdf_data_url(markdown)

        payload = {
            "name": name,
            "markdown": markdown,
        }

        response = _bookstack_request("PUT", f"/api/pages/{page_id}", json=payload)
        _invalidate_entity_cache("page", page_id)
        return response
