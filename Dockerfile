FROM node:20-slim

# Install Python and python-requests
RUN apt-get update && apt-get install -y \
    python3 \
    python3-requests \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies without running scripts
RUN npm install --ignore-scripts

# Copy source code and config files
COPY . .

# Build the project separately
RUN npm run build

# Copy Python scripts to dist directory
RUN mkdir -p dist/tools && cp src/tools/*.py dist/tools/

EXPOSE 8080

# Start with SSE transport
CMD ["node", "dist/index.js", "--transport", "sse"]