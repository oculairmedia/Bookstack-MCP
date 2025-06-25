FROM node:20-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Default environment variables (can be overridden at build or runtime)
ARG PORT=3054
ARG NODE_ENV=production
ARG TRANSPORT=http
ENV PORT=${PORT}
ENV NODE_ENV=${NODE_ENV}
ENV TRANSPORT=${TRANSPORT}

# Expose port
EXPOSE ${PORT}

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run server with configurable transport
CMD ["sh", "-c", "node src/index.js --${TRANSPORT}"]