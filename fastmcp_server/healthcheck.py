"""Container healthcheck for the BookStack MCP HTTP server.

Unlike a bare TCP probe, this confirms the application layer is actually
serving HTTP. Any HTTP response (including 4xx from the MCP endpoint, which
expects specific headers) proves the server is up; only connection/timeout
failures are treated as unhealthy.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    port = os.environ.get("PORT", "3054")
    url = f"http://127.0.0.1:{port}/mcp/"
    try:
        urllib.request.urlopen(url, timeout=5)  # noqa: S310 - fixed localhost URL
    except urllib.error.HTTPError:
        return 0
    except Exception as exc:  # connection refused, timeout, DNS, etc.
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
