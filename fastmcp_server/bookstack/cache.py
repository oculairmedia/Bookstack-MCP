"""Advanced caching layer for BookStack MCP server."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Set
from functools import wraps
import threading


@dataclass
class CacheEntry:
    """Cached response with metadata."""

    data: Any
    timestamp: float
    ttl: float
    hits: int = 0
    tags: Set[str] | None = None

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl

    def increment_hits(self) -> None:
        """Track cache hit count."""
        self.hits += 1


class SmartCache:
    """Thread-safe LRU cache with TTL and statistics."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0,
        }
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if valid."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None
            
            entry.increment_hits()
            self._stats["hits"] += 1
            return entry.data
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        *,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """Store value in cache with TTL."""
        with self._lock:
            # Evict oldest entry if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl,
                tags=set(tags or ()),
            )
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest timestamp and lowest hits
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].timestamp)
        )
        del self._cache[lru_key]
        self._stats["evictions"] += 1
    
    def invalidate(
        self,
        pattern: Optional[str] = None,
        *,
        tags: Optional[Set[str]] = None,
    ) -> int:
        """Invalidate cache entries matching a pattern or tag set."""
        with self._lock:
            if pattern is None and not tags:
                count = len(self._cache)
                self._cache.clear()
                return count

            keys_to_delete = []
            for key, entry in self._cache.items():
                pattern_match = pattern is not None and pattern in key
                tag_match = bool(tags and entry.tags and entry.tags.intersection(tags))
                if pattern_match or tag_match:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": f"{hit_rate:.2f}%",
                "total_requests": total_requests,
            }


# Global cache instance
_global_cache = SmartCache(max_size=1000, default_ttl=300)


def cached(ttl: Optional[float] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{_global_cache._make_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl)
            return result
        
        # Add cache control methods
        wrapper.cache_invalidate = lambda: _global_cache.invalidate(f"{key_prefix}:{func.__name__}")  # type: ignore[attr-defined]
        wrapper.cache_stats = lambda: _global_cache.get_stats()  # type: ignore[attr-defined]
        
        return wrapper
    
    return decorator


def get_cache() -> SmartCache:
    """Get global cache instance."""
    return _global_cache


# Specialized caches for different data types
class BookStackCache:
    """Specialized cache for BookStack entities."""
    
    def __init__(self):
        import os
        self.books = SmartCache(max_size=500, default_ttl=int(os.environ.get("BS_CACHE_BOOKS_TTL", "600")))  # 10 minutes
        self.pages = SmartCache(max_size=1000, default_ttl=int(os.environ.get("BS_CACHE_PAGES_TTL", "300")))  # 5 minutes
        self.images = SmartCache(max_size=2000, default_ttl=int(os.environ.get("BS_CACHE_IMAGES_TTL", "900")))  # 15 minutes
        self.search = SmartCache(max_size=200, default_ttl=int(os.environ.get("BS_CACHE_SEARCH_TTL", "180")))  # 3 minutes
    
    def invalidate_entity(self, entity_type: str, entity_id: Optional[int] = None) -> None:
        """Invalidate cache for specific entity type."""
        cache_map = {
            "book": self.books,
            "bookshelf": self.books,
            "page": self.pages,
            "chapter": self.pages,
            "image": self.images,
        }
        
        cache = cache_map.get(entity_type)
        if cache:
            invalidate_tags = {f"entity:{entity_type}", f"collection:{entity_type}"}
            if entity_id:
                invalidate_tags.add(f"entity:{entity_type}:{entity_id}")
            cache.invalidate(tags=invalidate_tags)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return {
            "books": self.books.get_stats(),
            "pages": self.pages.get_stats(),
            "images": self.images.get_stats(),
            "search": self.search.get_stats(),
        }


# Global BookStack cache
bookstack_cache = BookStackCache()
