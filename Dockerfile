FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better Docker layer caching
COPY fastmcp_server/requirements.txt ./fastmcp_server/requirements.txt
RUN pip install --no-cache-dir -r fastmcp_server/requirements.txt

# Copy application source
COPY fastmcp_server ./fastmcp_server
COPY docs ./docs

# Add the app directory to PYTHONPATH so fastmcp_server module can be imported
ENV PYTHONPATH=/app

# Default environment variables (override at runtime as needed)
ENV PORT=3054 \
    TRANSPORT=http

EXPOSE 3054

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import socket; s=socket.create_connection(('localhost', int('${PORT}')), 5); s.close()"

CMD ["/bin/sh", "-c", "cd /app && fastmcp run fastmcp_server/my_server.py:mcp --transport http --host 0.0.0.0 --port 3054"]
