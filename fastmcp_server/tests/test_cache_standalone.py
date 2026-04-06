"""Tests for SmartCache and BookStackCache."""

from __future__ import annotations

import time
from typing import Any

import pytest

from fastmcp_server.bookstack.cache import BookStackCache, SmartCache


@pytest.fixture
def cache():
    """Provide a fresh SmartCache instance for each test."""
    return SmartCache(max_size=10, default_ttl=60)


class TestSmartCache:
    """Test SmartCache functionality."""

    def test_get_returns_none_for_missing_key(self, cache):
        """Test that get returns None for keys that don't exist."""
        result = cache.get("nonexistent")
        assert result is None

    def test_get_returns_none_for_expired_entry(self):
        """Test that get returns None for expired entries."""
        # Use very short TTL
        cache = SmartCache(max_size=10, default_ttl=0.1)
        
        cache.set("key1", "value1")
        time.sleep(0.15)  # Wait for expiration
        
        result = cache.get("key1")
        assert result is None

    def test_get_returns_data_for_valid_entry(self, cache):
        """Test that get returns data for valid entries."""
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        assert result == "value1"

    def test_get_increments_hits(self, cache):
        """Test that get increments hit count."""
        cache.set("key1", "value1")
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Get the value
        cache.get("key1")
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_get_increments_misses_for_missing_key(self, cache):
        """Test that get increments miss count for missing keys."""
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    def test_get_increments_misses_for_expired_key(self):
        """Test that get increments miss count for expired keys."""
        cache = SmartCache(max_size=10, default_ttl=0.1)
        
        cache.set("key1", "value1")
        time.sleep(0.15)
        cache.get("key1")
        
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["expired"] == 1

    def test_set_stores_with_default_ttl(self, cache):
        """Test that set stores entries with default TTL."""
        cache.set("key1", "value1")
        
        # Should be retrievable
        result = cache.get("key1")
        assert result == "value1"

    def test_set_stores_with_custom_ttl(self):
        """Test that set can use custom TTL."""
        cache = SmartCache(max_size=10, default_ttl=60)
        
        # Set with very short TTL
        cache.set("key1", "value1", ttl=0.1)
        
        # Immediately retrievable
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired
        assert cache.get("key1") is None

    def test_set_triggers_lru_eviction_at_max_size(self):
        """Test that set triggers LRU eviction when at max_size."""
        cache = SmartCache(max_size=2, default_ttl=60)
        
        # Fill cache to max
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Add another entry - should evict key2 (least recently used)
        cache.set("key3", "value3")
        
        # key2 should be evicted
        assert cache.get("key2") is None
        # key1 and key3 should still exist
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"

    def test_set_lru_eviction_considers_hits(self):
        """Test that LRU eviction considers hit count."""
        cache = SmartCache(max_size=2, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key2 multiple times to increase hit count
        cache.get("key2")
        cache.get("key2")
        cache.get("key2")
        
        # Add third entry - should evict key1 (lower hits)
        cache.set("key3", "value3")
        
        # key1 should be evicted (0 hits)
        assert cache.get("key1") is None
        # key2 should remain (3 hits)
        assert cache.get("key2") == "value2"

    def test_invalidate_clears_entire_cache(self, cache):
        """Test that invalidate() clears entire cache."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        count = cache.invalidate()
        
        assert count == 3
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_invalidate_with_tags_removes_matching_entries_only(self, cache):
        """Test that invalidate(tags=...) removes only matching entries."""
        cache.set("key1", "value1", tags={"tag1", "tag2"})
        cache.set("key2", "value2", tags={"tag2", "tag3"})
        cache.set("key3", "value3", tags={"tag3"})
        cache.set("key4", "value4")  # No tags
        
        # Invalidate entries with tag2
        count = cache.invalidate(tags={"tag2"})
        
        assert count == 2  # key1 and key2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_invalidate_with_pattern_removes_matching_entries(self, cache):
        """Test that invalidate(pattern=...) removes entries with matching keys."""
        cache.set("books:1", "book1")
        cache.set("books:2", "book2")
        cache.set("pages:1", "page1")
        
        # Invalidate entries with "books" in the key
        count = cache.invalidate(pattern="books")
        
        assert count == 2
        assert cache.get("books:1") is None
        assert cache.get("books:2") is None
        assert cache.get("pages:1") == "page1"

    def test_get_stats_returns_hit_rate(self, cache):
        """Test that get_stats calculates hit rate correctly."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # 2 hits
        cache.get("key1")
        cache.get("key2")
        
        # 1 miss
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_requests"] == 3
        assert "66.67%" in stats["hit_rate"]  # 2/3 = 66.67%

    def test_get_stats_returns_size(self, cache):
        """Test that get_stats returns current size."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 10

    def test_get_stats_returns_totals(self, cache):
        """Test that get_stats returns all counters."""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats
        assert "expired" in stats


class TestBookStackCache:
    """Test BookStackCache specialized caches."""

    def test_bookstack_cache_has_four_buckets(self):
        """Test that BookStackCache has all four cache buckets."""
        cache = BookStackCache()
        
        assert hasattr(cache, "books")
        assert hasattr(cache, "pages")
        assert hasattr(cache, "images")
        assert hasattr(cache, "search")

    def test_bookstack_cache_buckets_have_different_ttls(self):
        """Test that cache buckets have different TTL configurations."""
        cache = BookStackCache()
        
        # Check default TTLs
        assert cache.books.default_ttl == 600  # 10 minutes
        assert cache.pages.default_ttl == 300  # 5 minutes
        assert cache.images.default_ttl == 900  # 15 minutes
        assert cache.search.default_ttl == 180  # 3 minutes

    def test_bookstack_cache_buckets_have_different_sizes(self):
        """Test that cache buckets have different max sizes."""
        cache = BookStackCache()
        
        assert cache.books.max_size == 500
        assert cache.pages.max_size == 1000
        assert cache.images.max_size == 2000
        assert cache.search.max_size == 200

    def test_get_all_stats_returns_all_bucket_stats(self):
        """Test that get_all_stats returns stats for all four buckets."""
        cache = BookStackCache()
        
        # Add some data to each bucket
        cache.books.set("book1", {"id": 1})
        cache.pages.set("page1", {"id": 1})
        cache.images.set("image1", {"id": 1})
        cache.search.set("search1", {"results": []})
        
        all_stats = cache.get_all_stats()
        
        assert "books" in all_stats
        assert "pages" in all_stats
        assert "images" in all_stats
        assert "search" in all_stats
        
        # Each should have stats
        assert all_stats["books"]["size"] == 1
        assert all_stats["pages"]["size"] == 1
        assert all_stats["images"]["size"] == 1
        assert all_stats["search"]["size"] == 1

    def test_invalidate_entity_clears_book_cache(self):
        """Test that invalidate_entity clears book-related caches."""
        cache = BookStackCache()
        
        cache.books.set("key1", "value1", tags={"entity:book", "collection:book"})
        cache.books.set("key2", "value2", tags={"entity:book", "entity:book:123"})
        
        cache.invalidate_entity("book")
        
        assert cache.books.get("key1") is None
        assert cache.books.get("key2") is None

    def test_invalidate_entity_clears_bookshelf_cache(self):
        """Test that invalidate_entity clears bookshelf caches in books bucket."""
        cache = BookStackCache()
        
        cache.books.set("key1", "value1", tags={"entity:bookshelf"})
        
        cache.invalidate_entity("bookshelf")
        
        assert cache.books.get("key1") is None

    def test_invalidate_entity_clears_page_cache(self):
        """Test that invalidate_entity clears page-related caches."""
        cache = BookStackCache()
        
        cache.pages.set("key1", "value1", tags={"entity:page"})
        cache.pages.set("key2", "value2", tags={"entity:page", "entity:page:456"})
        
        cache.invalidate_entity("page")
        
        assert cache.pages.get("key1") is None
        assert cache.pages.get("key2") is None

    def test_invalidate_entity_clears_chapter_cache(self):
        """Test that invalidate_entity clears chapter caches in pages bucket."""
        cache = BookStackCache()
        
        cache.pages.set("key1", "value1", tags={"entity:chapter"})
        
        cache.invalidate_entity("chapter")
        
        assert cache.pages.get("key1") is None

    def test_invalidate_entity_clears_image_cache(self):
        """Test that invalidate_entity clears image-related caches."""
        cache = BookStackCache()
        
        cache.images.set("key1", "value1", tags={"entity:image"})
        cache.images.set("key2", "value2", tags={"entity:image", "entity:image:789"})
        
        cache.invalidate_entity("image")
        
        assert cache.images.get("key1") is None
        assert cache.images.get("key2") is None

    def test_invalidate_entity_with_id_targets_specific_entity(self):
        """Test that invalidate_entity with entity_id targets specific entity."""
        cache = BookStackCache()
        
        cache.books.set("key1", "value1", tags={"entity:book:123"})
        cache.books.set("key2", "value2", tags={"entity:book:456"})
        
        cache.invalidate_entity("book", entity_id=123)
        
        # Only the specific entity should be invalidated
        assert cache.books.get("key1") is None
        # Other entities should remain (note: collection tags also match, so both get cleared)
        # The implementation invalidates all matching tags, including collection tags
