# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update \
    && apt-get install -y --no-install-recommends \
      poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better Docker layer caching
COPY fastmcp_server/requirements.txt ./fastmcp_server/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r fastmcp_server/requirements.txt

# Copy application source
COPY fastmcp_server ./fastmcp_server
COPY docs ./docs

# Add the app directory to PYTHONPATH so fastmcp_server module can be imported
ENV PYTHONPATH=/app

# Default environment variables (override at runtime as needed)
ENV PORT=3054 \
    TRANSPORT=http

# Run as an unprivileged user. The app only needs read access to /app; writable
# runtime paths (e.g. /data) are provided via mounted volumes.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 3054

# Application-level healthcheck: any HTTP response from the MCP endpoint proves
# the server is serving (not just that the TCP port is open).
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD ["python", "/app/fastmcp_server/healthcheck.py"]

CMD ["/bin/sh", "-c", "cd /app && fastmcp run fastmcp_server/my_server.py:mcp --transport http --host 0.0.0.0 --port ${PORT:-3054}"]
