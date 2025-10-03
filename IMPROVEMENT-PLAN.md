# BookStack MCP Server - Comprehensive Improvement Plan

**Last Updated**: 2025-10-03  
**Status**: Proposed Enhancements

---

## 🎯 Executive Summary

This document outlines strategic improvements to enhance the BookStack MCP server's performance, capabilities, and developer experience. Improvements are categorized by priority and impact.

---

## 1. Advanced MCP Features

### 1.1 Resources Support ⭐⭐⭐
**Priority**: HIGH | **Effort**: MEDIUM | **Impact**: HIGH

Add MCP Resources for read-only data access, complementing existing Tools.

**Implementation**:
```python
# In fastmcp_server/bookstack/resources.py

@mcp.resource("bookstack://book/{book_id}")
async def get_book_resource(book_id: int) -> str:
    """Expose books as MCP resources for context loading."""
    response = _bookstack_request("GET", f"/api/books/{book_id}")
    return json.dumps(response, indent=2)

@mcp.resource("bookstack://page/{page_id}")
async def get_page_resource(page_id: int) -> str:
    """Expose page content as resource."""
    response = _bookstack_request("GET", f"/api/pages/{page_id}")
    return json.dumps(response, indent=2)

@mcp.resource("bookstack://search")
async def search_resource(uri: str) -> str:
    """Expose search results as resources.
    URI format: bookstack://search?q=query&type=pages
    """
    # Parse query parameters from URI
    # Execute search and return results
```

**Benefits**:
- LLMs can load book/page content directly into context
- Better separation between read (resources) and write (tools)
- Improved performance for read-heavy workflows
- Enables context-aware AI interactions

**Files to Create**:
- `fastmcp_server/bookstack/resources.py`
- `fastmcp_server/bookstack/resource_templates.py`

---

### 1.2 Prompts Support ⭐⭐
**Priority**: MEDIUM | **Effort**: LOW | **Impact**: MEDIUM

Create reusable prompt templates for common BookStack workflows.

**Implementation**:
```python
# In fastmcp_server/bookstack/prompts.py

@mcp.prompt()
def create_documentation_page(topic: str, audience: str = "developers") -> list:
    """Generate a structured documentation page."""
    return [
        {
            "role": "user",
            "content": f"""Create a comprehensive documentation page about {topic} for {audience}.

Include:
1. Overview and introduction
2. Key concepts and terminology
3. Step-by-step examples
4. Best practices
5. Common pitfalls
6. Related resources

Format in Markdown."""
        }
    ]

@mcp.prompt()
def summarize_book(book_id: int) -> list:
    """Generate a summary of a BookStack book."""
    # Fetch book content
    book = _bookstack_request("GET", f"/api/books/{book_id}")
    
    return [
        {
            "role": "user",
            "content": f"Summarize this book: {json.dumps(book)}"
        }
    ]

@mcp.prompt()
def refactor_page_content(page_id: int, style: str = "technical") -> list:
    """Refactor page content with specific style."""
    # Implementation
```

**Benefits**:
- Standardized workflows for common tasks
- Improved consistency in generated content
- Easier onboarding for new users
- Reusable templates across projects

---

## 2. Performance & Scalability

### 2.1 Advanced Caching Layer ⭐⭐⭐
**Priority**: HIGH | **Effort**: MEDIUM | **Impact**: HIGH

**Status**: ✅ **IMPLEMENTED** - See `fastmcp_server/bookstack/cache.py`

Implement intelligent caching with:
- LRU eviction policy
- TTL-based expiration
- Cache statistics and monitoring
- Entity-specific cache invalidation

**Integration Example**:
```python
from .cache import cached, bookstack_cache

@cached(ttl=600, key_prefix="books")
def _bookstack_request_cached(method: str, path: str, **kwargs):
    """Cached version of BookStack API requests."""
    return _bookstack_request(method, path, **kwargs)

# Invalidate cache on mutations
def bookstack_manage_content(...):
    result = _bookstack_request(...)
    
    # Invalidate relevant caches
    if operation in ["create", "update", "delete"]:
        bookstack_cache.invalidate_entity(entity_type, entity_id)
    
    return result
```

**Benefits**:
- Reduced API calls to BookStack
- Faster response times for repeated queries
- Lower server load
- Better user experience

**Next Steps**:
1. Integrate cache into existing tools
2. Add cache warming for frequently accessed data
3. Implement cache metrics endpoint
4. Add cache configuration via environment variables

---

### 2.2 Connection Pooling ⭐⭐
**Priority**: MEDIUM | **Effort**: LOW | **Impact**: MEDIUM

Replace `requests` with `httpx` for async support and connection pooling.

**Implementation**:
```python
import httpx
from contextlib import asynccontextmanager

class BookStackClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
            ),
        )
    
    async def request(self, method: str, path: str, **kwargs):
        """Async HTTP request with connection pooling."""
        # Implementation
```

**Benefits**:
- Better resource utilization
- Improved concurrent request handling
- Reduced latency
- Support for async operations

---

### 2.3 Batch Request Optimization ⭐⭐
**Priority**: MEDIUM | **Effort**: MEDIUM | **Impact**: MEDIUM

Optimize batch operations with parallel execution.

**Current**: Sequential processing  
**Proposed**: Parallel processing with configurable concurrency

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def bookstack_batch_operations(...):
    """Execute batch operations with parallel processing."""
    
    async def process_item(item):
        # Process single item
        pass
    
    # Process items in parallel with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def bounded_process(item):
        async with semaphore:
            return await process_item(item)
    
    results = await asyncio.gather(
        *[bounded_process(item) for item in items],
        return_exceptions=True
    )
```

**Benefits**:
- 5-10x faster batch operations
- Better resource utilization
- Configurable concurrency limits

---

## 3. Enhanced Error Handling & Observability

### 3.1 Structured Logging ⭐⭐⭐
**Priority**: HIGH | **Effort**: LOW | **Impact**: HIGH

Replace print statements with structured logging.

**Implementation**:
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(self._json_formatter())
        self.logger.addHandler(handler)
    
    def _json_formatter(self):
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                }
                if hasattr(record, "context"):
                    log_data["context"] = record.context
                return json.dumps(log_data)
        return JSONFormatter()
    
    def info(self, message: str, **context):
        self.logger.info(message, extra={"context": context})
    
    def error(self, message: str, **context):
        self.logger.error(message, extra={"context": context})

# Usage
logger = StructuredLogger("bookstack.tools")
logger.info("Processing request", operation="create", entity_type="page")
```

---

### 3.2 Metrics & Monitoring ⭐⭐
**Priority**: MEDIUM | **Effort**: MEDIUM | **Impact**: MEDIUM

Add Prometheus-compatible metrics.

**Implementation**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter(
    "bookstack_requests_total",
    "Total BookStack API requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "bookstack_request_duration_seconds",
    "BookStack API request duration",
    ["method", "endpoint"]
)

cache_hits = Counter(
    "bookstack_cache_hits_total",
    "Cache hits",
    ["cache_type"]
)

# Expose metrics endpoint
@mcp.tool()
def get_metrics() -> str:
    """Get server metrics."""
    from prometheus_client import generate_latest
    return generate_latest().decode()
```

---

## 4. Developer Experience

### 4.1 Interactive CLI ⭐⭐
**Priority**: MEDIUM | **Effort**: MEDIUM | **Impact**: MEDIUM

Add interactive CLI for testing and development.

```bash
# Interactive mode
bookstack-mcp shell

# Execute single command
bookstack-mcp exec "list books --count 10"

# Test tool
bookstack-mcp test bookstack_manage_content --operation read --entity_type book --id 1
```

---

### 4.2 OpenAPI/Swagger Documentation ⭐⭐
**Priority**: MEDIUM | **Effort**: LOW | **Impact**: MEDIUM

Auto-generate API documentation from tool schemas.

```python
@mcp.tool()
def generate_openapi_spec() -> dict:
    """Generate OpenAPI specification for all tools."""
    # Convert MCP tool schemas to OpenAPI format
```

---

## 5. Security Enhancements

### 5.1 Rate Limiting ⭐⭐⭐
**Priority**: HIGH | **Effort**: LOW | **Impact**: HIGH

```python
from fastmcp import RateLimiter

rate_limiter = RateLimiter(
    max_requests=100,
    window_seconds=60
)

@mcp.tool()
@rate_limiter.limit
def bookstack_search(...):
    # Implementation
```

---

### 5.2 Input Validation & Sanitization ⭐⭐⭐
**Priority**: HIGH | **Effort**: MEDIUM | **Impact**: HIGH

Enhanced validation for all inputs:
- SQL injection prevention
- XSS protection
- Path traversal prevention
- Size limits enforcement

---

## 6. Advanced Features

### 6.1 Webhook Support ⭐
**Priority**: LOW | **Effort**: HIGH | **Impact**: MEDIUM

Listen to BookStack webhooks for real-time updates.

### 6.2 Export/Import Tools ⭐⭐
**Priority**: MEDIUM | **Effort**: MEDIUM | **Impact**: MEDIUM

Bulk export/import of BookStack content.

### 6.3 Version Control Integration ⭐
**Priority**: LOW | **Effort**: HIGH | **Impact**: LOW

Track changes and enable rollback.

---

## Implementation Roadmap

### Phase 1 (Weeks 1-2): Foundation
- ✅ Caching layer
- Structured logging
- Rate limiting
- Input validation

### Phase 2 (Weeks 3-4): Performance
- Connection pooling
- Batch optimization
- Metrics & monitoring

### Phase 3 (Weeks 5-6): Features
- Resources support
- Prompts support
- Interactive CLI

### Phase 4 (Weeks 7-8): Polish
- OpenAPI documentation
- Advanced error handling
- Testing & benchmarks

---

## Success Metrics

- **Performance**: 50% reduction in average response time
- **Reliability**: 99.9% uptime
- **Cache Hit Rate**: >70% for read operations
- **Error Rate**: <1% of requests
- **Test Coverage**: >90%

---

## Next Steps

1. Review and prioritize improvements
2. Create GitHub issues for each enhancement
3. Assign owners and timelines
4. Begin Phase 1 implementation
5. Set up monitoring and metrics

