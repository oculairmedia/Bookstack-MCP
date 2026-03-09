# BookStack MCP Page Creation Investigation

**Date:** 2025-10-09
**Investigator:** Codex (OpenCode)

## Summary

Automated BookStack page creation requests sent through the MCP bridge fail for both the simplified `bookstack_content_crud` and `bookstack_batch_operations` tools. Failures manifest as Python keyword argument conflicts, missing required keyword-only parameters, and validator errors around `chapter_id`. The behavior reproduces consistently when attempting to create a page in book ID 85 ("Graphiti Architecture").

## Remediation Status (2025-10-10)

- Simplified helpers now normalise their payloads before delegating to `_build_content_operation`, preventing duplicate keyword injection and providing clearer `ToolError` hints when misused.
- Batch helpers pass the full keyword set (with sane defaults) to `_build_content_operation`, allowing validation to run and enabling book-only page creation in bulk flows.
- `_build_content_operation` accepts book-level page creation without placeholder chapter IDs by funnelling zero/blank IDs through `_normalise_optional_parent_id` prior to validation.
- Regression coverage in `fastmcp_server/tests/test_simplified_helpers.py` and `test_manage_content.py` ensures CRUD and batch helpers accept top-level book pages going forward.

## Key Findings

1. **Duplicate keyword assignment inside `bookstack_content_crud`.**
   - Location: `fastmcp_server/bookstack/tools_simplified.py:147-176`.
   - `_extract_known_fields(parsed_data)` injects `markdown`, `html`, `book_id`, etc. into `kwargs`.
   - The subsequent `_build_content_operation` invocation also passes `markdown=None`, `html=None`, etc. explicitly.
   - Python raises `TypeError: _build_content_operation() got multiple values for keyword argument 'markdown'` (or `html`) because the same keyword appears twice.
   - Removing either the explicit keyword arguments or filtering duplicate keys from `_extract_known_fields` will unblock page creation for the CRUD helper.

2. **Missing keyword-only defaults in `bookstack_batch_operations`.
   - Location: `fastmcp_server/bookstack/tools_simplified.py:303-327`.
   - `_build_content_operation` declares keyword-only parameters (`name`, `description`, `markdown`, `html`, `book_id`, `chapter_id`, etc.) with no defaults.
   - The batch helper forwards only the extracted payload fields, so many keyword-only arguments are omitted entirely.
   - Python raises `_build_content_operation() missing <n> required keyword-only arguments` before validation can run.
   - Fix by passing explicit `None` defaults for every keyword-only argument (consistent with `bookstack_manage_content`).

3. **`chapter_id` validator rejects zero even when a book ID is provided.**
   - `_optional_positive_int` forces integers to be strictly greater than zero.
   - When the batch helper injects `chapter_id: 0` (its placeholder for "no chapter"), `_build_content_operation` raises a validation error.
   - Pages in BookStack can belong directly to a book. The helper must refrain from adding `chapter_id` when the value is falsy, or `_optional_positive_int` should tolerate zero for book-level pages.

4. **Schema/docs diverge from actual behavior.**
   - The MCP schema advertises an object-style `data` payload but does not describe the duplicate keyword rule or the true required field set for page creation.
   - Error messages mirror Python internals ("multiple values for keyword argument") instead of user-friendly guidance.

## Recommended Remediation Steps

1. **Update `bookstack_content_crud` (simplified tool).**
   - Filter `_extract_known_fields` so it excludes keys already supplied via explicit arguments before invoking `_build_content_operation`.
   - Alternatively, remove explicit `markdown/html/book_id/...` arguments and rely on structured `kwargs` to avoid duplication.

2. **Update `bookstack_batch_operations` helper.**
   - Pass all keyword-only parameters with defaults when calling `_build_content_operation`, e.g. `name=kwargs.get("name")`, `markdown=kwargs.get("markdown")`, etc.
   - Strip placeholder fields such as `chapter_id: 0` so validators receive `None` instead of invalid values.

3. **Improve validators for top-level pages.**
   - Allow `_optional_positive_int` to accept zero (or add a wrapper) when `chapter_id` is optional.
   - Ensure `_build_content_operation` only enforces one of (`book_id`, `chapter_id`) rather than both.

4. **Revise MCP schemas and docs.**
   - Document that only one of `markdown/content` or `html` should be supplied.
   - Clarify required vs optional fields for `create_page`, including valid `chapter_id` semantics.
   - Add usage examples that match the fixed behavior.

5. **Enhance error messaging.**
   - Catch `TypeError` in simplified helpers and rethrow as `ToolError` with actionable hints (e.g. "Move `markdown` out of the top-level arguments when using data payloads").

## Next Steps for Developers

1. Patch `tools_simplified.py` per the recommendations and add regression tests that call `bookstack_content_crud` and `bookstack_batch_operations` to create pages using markdown-only payloads.
2. Consider adding higher-level TypeScript coverage (`src/bookstack/BookstackTool.ts`) once the server helpers are corrected.
3. Once fixes land, run the existing `fastmcp_server/tests/test_manage_content.py` (or add a new test) to cover book-level page creation without chapters.
4. Update runtime documentation (`docs/`, README sections, or tool annotations) so downstream agents know which parameters to send.

## Validation Checklist for Fix

- [ ] `bookstack_content_crud` accepts `book_id + markdown` payload and reaches the BookStack API without Python keyword errors.
- [ ] `bookstack_batch_operations` can `bulk_create` a page with only `name`, `book_id`, and `markdown`.
- [ ] Creating a page under a book (no chapter) works by omitting `chapter_id` entirely.
- [ ] Errors about duplicate `markdown/html` inputs are user-facing `ToolError`s instead of raw Python tracebacks.
- [ ] Documentation/examples reflect the updated signatures.
