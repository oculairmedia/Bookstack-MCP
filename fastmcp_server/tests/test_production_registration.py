"""Integration test for the production tool registration stack."""
from __future__ import annotations

import pytest
from fastmcp import FastMCP

from fastmcp_server.bookstack import register_production_tools


EXPECTED_TOOLS = {
    "bookstack_list_content",
    "bookstack_search",
    "bookstack_semantic_search",
    "bookstack_manage_images",
    "bookstack_search_images",
    "bookstack_get_metrics",
    "bookstack_health_check",
    "bookstack_dashboard",
    "bookstack_content_crud",
    "bookstack_batch_operations",
    "bookstack_create_page_direct",
    "bookstack_update_page_direct",
    "bookstack_create_page_from_file",
    "bookstack_update_page_from_file",
    "bookstack_get_attachment_to_file",
    "bookstack_extract_pdf_attachment_text_to_file",
    "bookstack_extract_embedded_page_pdfs",
    "bookstack_append_pdf_text_page",
    "bookstack_upload_attachment_from_file",
    "bookstack_embed_pdf_attachment_on_page",
    "bookstack_create_review_pdf_attachment_for_page",
}


@pytest.mark.asyncio
async def test_production_stack_registers_expected_tools() -> None:
    mcp = FastMCP("test")
    register_production_tools(mcp)
    names = {t.name for t in (await mcp.get_tools()).values()}
    assert EXPECTED_TOOLS <= names, f"Missing: {EXPECTED_TOOLS - names}"


@pytest.mark.asyncio
async def test_production_stack_has_no_collisions() -> None:
    mcp = FastMCP("test")
    register_production_tools(mcp)
    tools = await mcp.get_tools()
    # get_tools() returns a name-keyed dict, so also assert the large-schema
    # manage_content tool is excluded in favor of the simplified content_crud.
    assert "bookstack_manage_content" not in tools
    assert "bookstack_content_crud" in tools
    assert len(tools) == len(EXPECTED_TOOLS)
