# Changelog

All notable changes made in this fork (`jbyerline/Bookstack-MCP`) relative to the
upstream project ([`oculairmedia/Bookstack-MCP`](https://github.com/oculairmedia/Bookstack-MCP))
are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Fork baseline: upstream `master` @ `5c5875f` ("restore monkeypatch compatibility
after module extraction").

## [1.0.0] - Fork divergence from upstream

### Added

#### PDF & attachment tools (`tools_pdf_attachments.py`)
- `bookstack_get_attachment_to_file` — download a BookStack attachment via the
  authenticated API (`GET /api/attachments/{id}`), base64-decode it, and write it
  under `/data`.
- `bookstack_extract_pdf_attachment_text_to_file` — fetch a PDF attachment, verify
  the `%PDF` signature, and extract its text with `pdftotext` (no `shell=True`).
- `bookstack_extract_embedded_page_pdfs` — scan a page's HTML/markdown for embedded
  attachment references (`/attachments/<id>`, `file=/attachments/<id>`, URL-encoded
  variants), de-duplicate them, and extract PDF + text for each.
- `bookstack_append_pdf_text_page` — append a title/bullet summary page to an
  existing PDF using `pypdf` + `reportlab`.
- All file I/O is constrained to `/data`; no BookStack write/delete calls are made
  by these tools.

#### Direct page tools (`tools_direct_pages.py`)
- `bookstack_create_page_direct` / `bookstack_update_page_direct` — typed-argument
  page create/update that bypass the generic content validator for wiki markdown.
- `bookstack_create_page_from_file` / `bookstack_update_page_from_file` — read page
  content from a file under `/data`, the recommended path for large edits.

#### Operations & tooling
- `healthcheck.py` — application-level container healthcheck (HTTP probe of the MCP
  endpoint) used by the Docker `HEALTHCHECK`.
- `register_production_tools()` in `bookstack/__init__.py` — single entry point that
  registers the full production tool set (selective, simplified, direct-page, PDF),
  used by both `my_server.py` (HTTP) and `run_stdio.py` (Inspector).
- `requirements-dev.txt` separating dev/test dependencies from runtime.
- New tests: `test_pdf_attachments.py`, `test_direct_pages.py`,
  `test_production_registration.py`, `test_request_timeout.py`.
- CI: install `poppler-utils`, run pytest with coverage, and add a `pyright`
  type-check job.

### Changed

#### Large page edit stability & performance
- Shared `requests.Session` with connection pooling and `urllib3` retry/backoff for
  all BookStack API calls (configurable via `BS_HTTP_RETRIES`, `BS_HTTP_BACKOFF`,
  `BS_HTTP_POOL_SIZE`).
- Payload-aware timeouts: writes (`POST`/`PUT`/`DELETE`) use a higher base timeout
  (`BS_HTTP_WRITE_TIMEOUT`, default 120s) that scales with payload size, so large
  markdown edits don't hit premature read timeouts and trigger wasteful retries.
  Reads keep the shorter `BS_HTTP_TIMEOUT` (default 60s).
- Guidance in the page-update tool docstrings steering agents to file-based updates
  (`*_from_file`) for large content to avoid tool-call payload limits.

#### Caching correctness
- Cache invalidation now runs after simplified CRUD/batch operations and direct-page
  writes, preventing stale reads.
- Any content mutation also clears the search cache bucket.
- Cache TTLs are read from `BS_CACHE_*` environment variables and aligned across the
  request layer and cache module.

#### Architecture & maintainability
- Centralized HTTP/auth client logic in `api_client.py`; `tools_direct_pages.py` and
  `tools_pdf_attachments.py` now reuse `_bookstack_request` instead of duplicating
  request/auth/error handling.
- Deduplicated shared helpers (`_normalise_str`, `_validate_positive_int`) and
  renamed the conflicting `CacheEntry` schema to `ImageListCacheEntry`.
- `my_server.py` and Docker `CMD` honor the `PORT` environment variable (default
  3054).
- Consolidated Docker Compose configuration into `compose.yaml`.
- `pyproject.toml`: added `pypdf`/`reportlab` runtime deps, moved test deps to a
  `dev` extra, added package discovery, bumped `requires-python` to `>=3.11`, and
  set version to `1.0.0`.
- Updated `README.md` and `.env.example` to document the full tool set and all
  environment variables (HTTP tuning, cache TTLs, semantic-search URL).

### Fixed
- Metrics now record multipart/form (image upload) requests and no longer
  undercount error rates.

### Removed
- Dead code: unused `cached` decorator, `get_cache()`/`_global_cache`,
  `track_request` decorator, and `InputValidator.validate_url`.
- Redundant `docker-compose.yml` and `docker-compose.http.yml` (folded into
  `compose.yaml`).

### Security
- Error logs redact full request bodies, recording only field names to avoid
  leaking page content or PII.
- The semantic-search (Hayhooks) URL is strictly environment-driven; no hardcoded
  private-IP fallback.
- SSRF protection for remote image fetches, with an explicit exemption for the
  configured BookStack host (needed for gallery/cover images).
- Docker image runs as a non-root `appuser`.
