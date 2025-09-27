FROM node:20-slim

# Install Python and python-requests and curl for healthcheck
RUN apt-get update && apt-get install -y \
    python3 \
    python3-requests \
    curl \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies without running scripts
RUN npm install --ignore-scripts

# Copy source code and config files
COPY . .

# Install TypeScript globally to avoid permission issues
RUN npm install -g typescript

# Build the project separately
RUN npm run build

# Copy Python scripts to dist directory
RUN mkdir -p dist/tools && cp src/tools/*.py dist/tools/

EXPOSE 8080

# Default environment variables (can be overridden at build or runtime)
ARG PORT=8080
ARG NODE_ENV=production
ARG TRANSPORT=http
ENV PORT=${PORT}
ENV NODE_ENV=${NODE_ENV}
ENV TRANSPORT=${TRANSPORT}

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run server with configurable transport
CMD ["sh", "-c", "node ./dist/index.js --${TRANSPORT}"]