from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import requests


def _bookstack_base_url() -> str:
    return os.environ["BS_URL"].rstrip("/")


def _bookstack_headers() -> dict[str, str]:
    return {
        "Authorization": f"Token {os.environ['BS_TOKEN_ID']}:{os.environ['BS_TOKEN_SECRET']}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _raise_for_bookstack(response: requests.Response) -> None:
    if response.ok:
        return

    try:
        detail: Any = response.json()
    except Exception:
        detail = response.text

    raise RuntimeError(f"BookStack API error {response.status_code}: {detail}")


def _safe_markdown_path(markdown_path: str) -> Path:
    path = Path(markdown_path).resolve()
    allowed_root = Path("/data").resolve()

    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError("markdown_path must be under /data")

    if not path.is_file():
        raise FileNotFoundError(f"Markdown file does not exist: {path}")

    return path


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
        payload: dict[str, Any] = {
            "name": name,
            "book_id": book_id,
            "markdown": markdown,
        }

        if chapter_id is not None:
            payload["chapter_id"] = chapter_id

        response = requests.post(
            f"{_bookstack_base_url()}/api/pages",
            headers=_bookstack_headers(),
            json=payload,
            timeout=90,
        )
        _raise_for_bookstack(response)
        return response.json()

    @mcp.tool()
    def bookstack_update_page_direct(
        page_id: int,
        name: str,
        markdown: str,
    ) -> dict[str, Any]:
        """
        Update a BookStack page using direct typed arguments.
        """
        payload = {
            "name": name,
            "markdown": markdown,
        }

        response = requests.put(
            f"{_bookstack_base_url()}/api/pages/{page_id}",
            headers=_bookstack_headers(),
            json=payload,
            timeout=90,
        )
        _raise_for_bookstack(response)
        return response.json()

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

        payload: dict[str, Any] = {
            "name": name,
            "book_id": book_id,
            "markdown": markdown,
        }

        if chapter_id is not None:
            payload["chapter_id"] = chapter_id

        response = requests.post(
            f"{_bookstack_base_url()}/api/pages",
            headers=_bookstack_headers(),
            json=payload,
            timeout=90,
        )
        _raise_for_bookstack(response)
        return response.json()

    @mcp.tool()
    def bookstack_update_page_from_file(
        page_id: int,
        name: str,
        markdown_path: str,
    ) -> dict[str, Any]:
        """
        Update a BookStack page from a Markdown file under /data.
        """
        path = _safe_markdown_path(markdown_path)
        markdown = path.read_text(encoding="utf-8")

        payload = {
            "name": name,
            "markdown": markdown,
        }

        response = requests.put(
            f"{_bookstack_base_url()}/api/pages/{page_id}",
            headers=_bookstack_headers(),
            json=payload,
            timeout=90,
        )
        _raise_for_bookstack(response)
        return response.json()
