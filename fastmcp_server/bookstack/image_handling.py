"""Image handling, SSRF protection, and gallery helpers for BookStack tools."""

from __future__ import annotations

import base64
import binascii
import hashlib
import ipaddress
import json
import mimetypes
import re
import socket
import tempfile
from typing import Any, Dict, Optional, Sequence, Tuple
from urllib.parse import unquote, urljoin, urlparse

import requests

from .api_client import (
    ToolError,
    _bookstack_base_url,
    _bookstack_request,
    _tool_error,
    logger,
)
from .cache import bookstack_cache
from .schemas import (
    CacheEntry,
    PreparedImage,
    _ALLOWED_MIME_TYPES,
    _ALLOWED_URL_SCHEMES,
    _DATA_URL_RE,
    _DEFAULT_MIME_TYPE,
    _FALLBACK_FILE_NAME,
    _MAX_IMAGE_SIZE_BYTES,
    _MAX_URL_REDIRECTS,
    _REQUEST_TIMEOUT_SECONDS,
)


# ============================================================================
# Helper functions used by image-related code
# These are duplicated here until content_operations.py is created
# ============================================================================

def _validate_positive_int(value: Optional[Any], label: str) -> int:
    """Ensure a positive integer value is provided."""
    if value is None:
        raise _tool_error(
            f"{label} is required",
            hint=f"Provide a numeric value for {label}.",
        )
    try:
        int_value = int(value)
    except (TypeError, ValueError) as exc:
        raise _tool_error(
            f"{label} must be a positive integer",
            hint=f"Provide a numeric value greater than zero for {label}.",
            context={"received": value},
        ) from exc
    if int_value <= 0:
        raise _tool_error(
            f"{label} must be a positive integer",
            hint=f"Provide a numeric value greater than zero for {label}.",
            context={"received": value},
        )
    return int_value


def _normalise_str(value: Optional[str]) -> Optional[str]:
    """Strip surrounding whitespace and return None when a string is empty."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# ============================================================================
# URL/base64 utilities
# ============================================================================

def _is_url(value: str) -> bool:
    """Check if a string is a valid HTTP/HTTPS URL."""
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme.lower() in _ALLOWED_URL_SCHEMES and bool(parsed.netloc)
    except Exception as exc:
        logger.debug("_is_url: failed to parse %r: %s", value[:200], exc)
        return False


def _extract_filename_from_url(url: str, fallback: str) -> str:
    """Extract a sensible filename from a URL."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path and "." in path:
            filename = path.split("/")[-1]
            # Sanitize filename - remove special characters
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            if filename and len(filename) <= 255:
                return filename
    except Exception as exc:
        logger.debug("_extract_filename_from_url: failed for %r: %s", url[:200], exc)
    return fallback


def _decode_base64_string(payload: str) -> bytes:
    try:
        cleaned = re.sub(r"\s+", "", payload)
        return base64.b64decode(cleaned, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _tool_error(
            "Failed to decode base64 image data",
            hint="Verify the string is base64 encoded without extra whitespace or URL encoding.",
            context={"error": str(exc)},
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise _tool_error(
            "Unexpected error while decoding base64 image data",
            context={"error": str(exc)},
        ) from exc


# ============================================================================
# SSRF protection
# ============================================================================

def _classify_disallowed_ip(ip_text: str) -> Optional[str]:
    """Return the reason an IP target is unsafe for outbound fetches."""
    ip_addr = ipaddress.ip_address(ip_text)

    if ip_addr.is_loopback:
        return "loopback"
    if ip_addr.is_private:
        return "private"
    if ip_addr.is_link_local:
        return "link-local"
    if ip_addr.is_multicast:
        return "multicast"
    if ip_addr.is_reserved:
        return "reserved"
    if ip_addr.is_unspecified:
        return "unspecified"
    return None


def _resolve_url_targets(url: str) -> Sequence[str]:
    """Resolve a URL hostname to concrete IP addresses."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise _tool_error(
            "Invalid URL format",
            hint="Provide a valid HTTP or HTTPS URL with a hostname.",
            context={"url": url},
        )

    try:
        addrinfo = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise _tool_error(
            "Failed to resolve image host",
            hint="Verify the hostname is correct and publicly reachable.",
            context={"url": url, "hostname": hostname},
        ) from exc

    resolved_ips: list[str] = []
    for entry in addrinfo:
        ip_text = str(entry[4][0])
        if ip_text not in resolved_ips:
            resolved_ips.append(ip_text)

    if not resolved_ips:
        raise _tool_error(
            "Failed to resolve image host",
            hint="Verify the hostname is correct and publicly reachable.",
            context={"url": url, "hostname": hostname},
        )

    return resolved_ips


def _validate_remote_image_target(url: str) -> None:
    """Reject URLs that resolve to internal or otherwise unsafe IP ranges."""
    blocked_targets = []
    for ip_text in _resolve_url_targets(url):
        reason = _classify_disallowed_ip(ip_text)
        if reason:
            blocked_targets.append({"ip": ip_text, "reason": reason})

    if blocked_targets:
        raise _tool_error(
            "URL resolves to a disallowed network target",
            hint="Use a publicly reachable HTTP or HTTPS image URL.",
            context={"url": url, "blocked_targets": blocked_targets},
        )


# ============================================================================
# Image fetching
# ============================================================================

def _fetch_image_from_url(url: str, fallback_name: str) -> PreparedImage:
    """Fetch image data from HTTP/HTTPS URL with security controls."""

    if not _is_url(url):
        raise _tool_error(
            "Invalid URL format",
            hint="Provide a valid HTTP or HTTPS URL.",
            context={"url": url}
        )

    current_url = url
    response = None

    try:
        for redirect_count in range(_MAX_URL_REDIRECTS + 1):
            _validate_remote_image_target(current_url)

            # Redirects are validated hop-by-hop so internal targets cannot be reached.
            response = requests.get(
                current_url,
                timeout=_REQUEST_TIMEOUT_SECONDS,
                stream=True,
                allow_redirects=False,
                headers={
                    'User-Agent': 'BookStack-MCP/1.0',
                    'Accept': 'image/*'
                }
            )

            if 300 <= response.status_code < 400:
                location = response.headers.get("location")
                if not location:
                    raise _tool_error(
                        "Redirect response missing Location header",
                        context={"url": current_url, "status_code": response.status_code},
                    )
                if redirect_count >= _MAX_URL_REDIRECTS:
                    raise _tool_error(
                        "Too many redirects while fetching image",
                        hint=f"Limit redirects to {_MAX_URL_REDIRECTS} hops or use the final URL directly.",
                        context={"url": url},
                    )
                current_url = urljoin(current_url, location)
                if hasattr(response, "close"):
                    response.close()
                response = None
                continue

            response.raise_for_status()
            break
        else:  # pragma: no cover - defensive guard
            raise _tool_error("Too many redirects while fetching image", context={"url": url})

        # Check content length before downloading
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > _MAX_IMAGE_SIZE_BYTES:
            raise _tool_error(
                f"Image too large: {content_length} bytes exceeds {_MAX_IMAGE_SIZE_BYTES} byte limit",
                hint="Use a smaller image or increase the size limit.",
                context={"url": url, "size": content_length}
            )

        # Download with size limit using SpooledTemporaryFile for large images
        spool = tempfile.SpooledTemporaryFile(max_size=5*1024*1024)  # 5MB spill threshold
        try:
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                spool.write(chunk)
                total_size += len(chunk)
                if total_size > _MAX_IMAGE_SIZE_BYTES:
                    raise _tool_error(
                        f"Image download exceeded {_MAX_IMAGE_SIZE_BYTES} byte limit",
                        hint="Use a smaller image or increase the size limit.",
                        context={"url": url}
                    )
            
            # Read the final content
            spool.seek(0)
            content = spool.read()
        finally:
            spool.close()

        if not content:
            raise _tool_error(
                "Downloaded image is empty",
                hint="Verify the URL points to a valid image file.",
                context={"url": url}
            )

        # Determine MIME type
        mime_type = response.headers.get('content-type', '').split(';')[0].lower()
        guessed_type, _ = mimetypes.guess_type(current_url)

        if mime_type:
            if mime_type not in _ALLOWED_MIME_TYPES:
                raise _tool_error(
                    "Unsupported remote image MIME type",
                    hint="Use a URL that serves one of the supported image MIME types.",
                    context={
                        "url": current_url,
                        "content_type": mime_type,
                        "allowed_mime_types": sorted(_ALLOWED_MIME_TYPES),
                    },
                )
        elif guessed_type and guessed_type in _ALLOWED_MIME_TYPES:
            mime_type = guessed_type
        else:
            raise _tool_error(
                "Unable to determine a supported image MIME type",
                hint="Ensure the URL has a supported image extension or the server returns an image Content-Type header.",
                context={
                    "url": current_url,
                    "guessed_type": guessed_type,
                    "allowed_mime_types": sorted(_ALLOWED_MIME_TYPES),
                },
            )

        # Extract filename
        filename = _extract_filename_from_url(current_url, fallback_name)

        return PreparedImage(
            filename=filename,
            content=content,
            mime_type=mime_type
        )

    except requests.exceptions.Timeout as exc:
        raise _tool_error(
            f"Request timeout after {_REQUEST_TIMEOUT_SECONDS} seconds",
            hint="The image server may be slow or unreachable. Try again later.",
            context={"url": url}
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise _tool_error(
            "Failed to connect to image URL",
            hint="Check the URL and ensure the server is accessible.",
            context={"url": url}
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else "unknown"
        raise _tool_error(
            f"HTTP error {status_code} when fetching image",
            hint="Verify the URL is correct and the image is publicly accessible.",
            context={"url": url, "status_code": status_code}
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise _tool_error(
            "Failed to fetch image from URL",
            hint="Check the URL format and network connectivity.",
            context={"url": url, "error": str(exc)}
        ) from exc
    except ToolError:
        # Re-raise ToolErrors (e.g., from size limit checks) without wrapping
        raise
    except Exception as exc:  # pragma: no cover - defensive guard
        raise _tool_error(
            "Unexpected error while fetching image from URL",
            context={"url": url, "error": str(exc)}
        ) from exc
    finally:
        if response is not None and hasattr(response, "close"):
            response.close()


# ============================================================================
# Image preparation
# ============================================================================

def _prepare_image_payload(
    image: str,
    fallback_name: str,
    fallback_type: str = _DEFAULT_MIME_TYPE,
) -> PreparedImage:
    """Prepare image payload from base64, data URL, or HTTP/HTTPS URL."""

    value = image.strip()

    # Check if it looks like a URL (has scheme and netloc)
    try:
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            # It looks like a URL - check if it's allowed
            if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
                raise _tool_error(
                    f"URL scheme '{parsed.scheme}' is not supported",
                    hint="Only HTTP and HTTPS URLs are allowed for image fetching.",
                    context={"url": value, "scheme": parsed.scheme}
                )
            # It's a valid HTTP/HTTPS URL
            return _fetch_image_from_url(value, fallback_name)
    except ToolError:
        # Re-raise ToolErrors
        raise
    except Exception:
        # Not a valid URL, continue to other formats
        pass

    # Check if it's a data URL
    match = _DATA_URL_RE.match(value)
    if match:
        mime_type = match.group(1) or fallback_type
        is_base64 = bool(match.group(2))
        raw_payload = match.group(3) or ""
        if is_base64:
            content = _decode_base64_string(raw_payload)
        else:
            content = unquote(raw_payload).encode("utf-8")
        if not content:
            raise _tool_error(
                "Image payload is empty after decoding the provided data URL",
                hint="Ensure the data URL includes image bytes after the comma separator.",
            )
        return PreparedImage(filename=fallback_name, content=content, mime_type=mime_type)

    # Assume it's a base64 string
    content = _decode_base64_string(value)
    if not content:
        raise _tool_error(
            "Decoded image payload is empty",
            hint="Confirm the base64 string contains valid image data.",
        )
    return PreparedImage(filename=fallback_name, content=content, mime_type=fallback_type)


def _prepare_cover_image_from_gallery(
    image_id: Any,
    *,
    fallback_name: Optional[str],
) -> PreparedImage:
    """Fetch an existing gallery image and return it as a PreparedImage."""

    validated_id = _validate_positive_int(image_id, "'image_id'")
    metadata = _bookstack_request("GET", f"/api/image-gallery/{validated_id}")
    if not isinstance(metadata, dict):
        raise _tool_error(
            "Unexpected response when fetching gallery image metadata",
            hint="Ensure the image exists and the API token grants image permissions.",
            context={"image_id": validated_id, "payload_type": type(metadata).__name__},
        )

    raw_name = metadata.get("name")
    image_name = _normalise_str(raw_name) if isinstance(raw_name, str) else None

    image_url: Optional[str] = None
    raw_url = metadata.get("url")
    if isinstance(raw_url, str) and raw_url.strip():
        image_url = raw_url.strip()
    else:
        raw_path = metadata.get("path")
        if isinstance(raw_path, str) and raw_path.strip():
            image_url = f"{_bookstack_base_url()}{raw_path}"

    if not image_url:
        raise _tool_error(
            "Gallery image metadata did not include a usable URL",
            hint="Verify the image exists and is accessible via the BookStack instance.",
            context={"image_id": validated_id, "metadata_keys": list(metadata.keys())},
        )

    effective_name = image_name or fallback_name or f"book-cover-{validated_id}"
    return _fetch_image_from_url(image_url, effective_name)


def _prepare_form_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a JSON-style payload into form fields for multipart requests."""
    form_data: Dict[str, Any] = {}
    for key, value in payload.items():
        if value is None or key in {"image_id", "cover_image"}:
            continue
        if isinstance(value, (dict, list)):
            form_data[key] = json.dumps(value)
        else:
            form_data[key] = value if isinstance(value, str) else str(value)
    return form_data


# ============================================================================
# Image list helpers
# ============================================================================

def _normalize_image_list_response(
    api_response: Any,
    *,
    offset: int,
    count: int,
) -> Tuple[Any, Optional[Dict[str, Any]]]:
    if isinstance(api_response, dict) and isinstance(api_response.get("data"), list):
        images = api_response["data"]
        metadata: Dict[str, Any] = {}
        if isinstance(api_response.get("total"), int):
            metadata["total"] = api_response["total"]
        if isinstance(api_response.get("count"), int):
            metadata["count"] = api_response["count"]
        else:
            metadata["count"] = len(images)
        if isinstance(api_response.get("offset"), int):
            metadata["offset"] = api_response["offset"]
        else:
            metadata["offset"] = offset
        return images, metadata

    if isinstance(api_response, list):
        metadata = {"offset": offset, "count": len(api_response)}
        return api_response, metadata

    return api_response, None


def _build_list_cache_key(params: Dict[str, Any]) -> str:
    items: list[Tuple[str, Any]] = []
    for key, value in sorted(params.items()):
        if isinstance(value, list):
            items.append((key, tuple(value)))
        elif isinstance(value, dict):
            items.append((key, tuple(sorted(value.items()))))
        else:
            items.append((key, value))
    encoded = json.dumps(items, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _get_cached_list(cache_key: str) -> Optional[CacheEntry]:
    cached = bookstack_cache.images.get(cache_key)
    if cached is None:
        return None
    if isinstance(cached, dict):
        return CacheEntry(data=cached.get("data"), metadata=cached.get("metadata"))
    return CacheEntry(data=cached)


def _set_cached_list(cache_key: str, data: Any, metadata: Optional[Dict[str, Any]]) -> None:
    from .api_client import _cache_ttl_for
    bookstack_cache.images.set(cache_key, {"data": data, "metadata": metadata}, ttl=_cache_ttl_for("/api/image-gallery"))


def _invalidate_list_cache() -> None:
    bookstack_cache.images.invalidate()


def _ensure_iso8601(value: str, label: str):
    """Validate ISO 8601 datetime strings."""
    from datetime import datetime
    try:
        normalised = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise _tool_error(
            f"{label} must be an ISO-8601 datetime string",
            hint="Use formats like '2025-09-27T18:00:00Z' or '2025-09-27T18:00:00+00:00'.",
            context={"received": value},
        ) from exc
