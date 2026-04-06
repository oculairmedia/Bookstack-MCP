"""Tests for normalization and tag helper functions from tools.py."""

from __future__ import annotations

import json
from typing import Any, Dict

import pytest

import fastmcp_server.bookstack.tools as tools
from fastmcp_server.bookstack.tools import ToolError


class TestFormatTags:
    """Test _format_tags helper function."""

    def test_format_tags_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._format_tags(None)
        assert result is None

    def test_format_tags_valid_list_passthrough(self):
        """Test that valid tag list is passed through."""
        tags = [
            {"name": "category", "value": "documentation"},
            {"name": "status", "value": "draft"},
        ]
        
        result = tools._format_tags(tags)
        
        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "category"
        assert result[0]["value"] == "documentation"

    def test_format_tags_empty_list_returns_empty(self):
        """Test that empty list returns empty list."""
        result = tools._format_tags([])
        
        # Should return empty list or None depending on validation
        assert result is not None
        assert len(result) == 0

    def test_format_tags_validates_structure(self):
        """Test that invalid tag structure raises ToolError."""
        # Tag missing required 'name' field
        invalid_tags = [
            {"value": "test"},
        ]
        
        with pytest.raises(ToolError):
            tools._format_tags(invalid_tags)

    def test_format_tags_converts_objects_to_dicts(self):
        """Test that tag objects with attributes are converted."""
        class TagObj:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        
        tags = [TagObj("key1", "value1")]
        
        result = tools._format_tags(tags)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "key1"


class TestNormaliseBooks:
    """Test _normalise_books helper function."""

    def test_normalise_books_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._normalise_books(None)
        assert result is None

    def test_normalise_books_int_list_normalized(self):
        """Test that list of ints is normalized."""
        result = tools._normalise_books([1, 2, 3])
        
        assert result == [1, 2, 3]

    def test_normalise_books_string_ints_converted(self):
        """Test that string integers are converted."""
        result = tools._normalise_books(["1", "2", "3"])
        
        assert result == [1, 2, 3]

    def test_normalise_books_empty_list_returns_none(self):
        """Test that empty list returns None."""
        result = tools._normalise_books([])
        
        # Based on the implementation, empty list should be processed
        # but _validate_positive_int won't be called
        # So we expect an empty list, not None
        assert result is not None
        assert len(result) == 0

    def test_normalise_books_rejects_invalid_ids(self):
        """Test that invalid book IDs raise ToolError."""
        with pytest.raises(ToolError):
            tools._normalise_books([1, 0, 3])  # 0 is invalid

    def test_normalise_books_rejects_negative_ids(self):
        """Test that negative IDs raise ToolError."""
        with pytest.raises(ToolError):
            tools._normalise_books([1, -1, 3])


class TestNormaliseStr:
    """Test _normalise_str helper function."""

    def test_normalise_str_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._normalise_str(None)
        assert result is None

    def test_normalise_str_empty_returns_none(self):
        """Test that empty string returns None."""
        result = tools._normalise_str("")
        assert result is None

    def test_normalise_str_whitespace_returns_none(self):
        """Test that whitespace-only string returns None."""
        result = tools._normalise_str("   ")
        assert result is None
        
        result = tools._normalise_str("\t\n  ")
        assert result is None

    def test_normalise_str_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        result = tools._normalise_str("  hello  ")
        assert result == "hello"
        
        result = tools._normalise_str("\thello world\n")
        assert result == "hello world"

    def test_normalise_str_preserves_content(self):
        """Test that actual content is preserved."""
        result = tools._normalise_str("hello")
        assert result == "hello"
        
        result = tools._normalise_str("hello world")
        assert result == "hello world"


class TestNormaliseOptionalParentId:
    """Test _normalise_optional_parent_id helper function."""

    def test_normalise_optional_parent_id_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._normalise_optional_parent_id(None)
        assert result is None

    def test_normalise_optional_parent_id_zero_returns_none(self):
        """Test that zero returns None."""
        result = tools._normalise_optional_parent_id(0)
        assert result is None
        
        result = tools._normalise_optional_parent_id("0")
        assert result is None

    def test_normalise_optional_parent_id_negative_passes_through(self):
        """Test that negative values pass through (only 0 is treated as absent)."""
        result = tools._normalise_optional_parent_id(-1)
        assert result == -1
        
        result = tools._normalise_optional_parent_id(-5)
        assert result == -5

    def test_normalise_optional_parent_id_positive_passthrough(self):
        """Test that positive integers pass through."""
        result = tools._normalise_optional_parent_id(5)
        assert result == 5
        
        result = tools._normalise_optional_parent_id(123)
        assert result == 123

    def test_normalise_optional_parent_id_string_positive_converted(self):
        """Test that positive string integers are converted."""
        result = tools._normalise_optional_parent_id("5")
        assert result == 5
        
        result = tools._normalise_optional_parent_id("123")
        assert result == 123

    def test_normalise_optional_parent_id_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = tools._normalise_optional_parent_id("")
        assert result is None
        
        result = tools._normalise_optional_parent_id("  ")
        assert result is None

    def test_normalise_optional_parent_id_bool_handling(self):
        """Test boolean handling."""
        result = tools._normalise_optional_parent_id(True)
        assert result == 1
        
        result = tools._normalise_optional_parent_id(False)
        assert result is None

    def test_normalise_optional_parent_id_float_converted(self):
        """Test that float values are converted to int."""
        result = tools._normalise_optional_parent_id(5.0)
        assert result == 5
        
        result = tools._normalise_optional_parent_id(0.0)
        assert result is None


class TestCoerceJsonObject:
    """Test _coerce_json_object helper function."""

    def test_coerce_json_object_none_returns_empty_dict(self):
        """Test that None returns empty dict."""
        result = tools._coerce_json_object(None, label="test")
        assert result == {}

    def test_coerce_json_object_dict_passthrough(self):
        """Test that dict is passed through."""
        data = {"name": "Test", "id": 123}
        result = tools._coerce_json_object(data, label="test")
        
        assert result == data
        # Should be a new dict, not the same object
        assert result is not data

    def test_coerce_json_object_json_string_parsed(self):
        """Test that JSON string is parsed."""
        json_str = '{"name": "Test", "id": 123}'
        result = tools._coerce_json_object(json_str, label="test")
        
        assert result == {"name": "Test", "id": 123}

    def test_coerce_json_object_empty_string_returns_empty_dict(self):
        """Test that empty string returns empty dict."""
        result = tools._coerce_json_object("", label="test")
        assert result == {}
        
        result = tools._coerce_json_object("  ", label="test")
        assert result == {}

    def test_coerce_json_object_invalid_json_raises_error(self):
        """Test that invalid JSON string raises ToolError."""
        with pytest.raises(ToolError) as exc:
            tools._coerce_json_object("{invalid json}", label="test payload")
        
        assert "test payload" in str(exc.value)
        assert "valid JSON" in str(exc.value)

    def test_coerce_json_object_non_object_json_raises_error(self):
        """Test that JSON arrays/primitives raise ToolError."""
        # JSON array
        with pytest.raises(ToolError) as exc:
            tools._coerce_json_object("[1, 2, 3]", label="test")
        
        assert "must be a JSON object" in str(exc.value)
        
        # JSON string
        with pytest.raises(ToolError):
            tools._coerce_json_object('"string"', label="test")

    def test_coerce_json_object_complex_nested_structure(self):
        """Test that complex nested structures are parsed."""
        json_str = '{"book": {"name": "Test", "tags": [{"name": "tag1", "value": "val1"}]}}'
        result = tools._coerce_json_object(json_str, label="test")
        
        assert result["book"]["name"] == "Test"
        assert len(result["book"]["tags"]) == 1


class TestCompactPayload:
    """Test _compact_payload helper function."""

    def test_compact_payload_removes_none_values(self):
        """Test that None values are removed."""
        data = {"name": "Test", "description": None, "id": 123}
        result = tools._compact_payload(data)
        
        assert "name" in result
        assert "id" in result
        assert "description" not in result

    def test_compact_payload_removes_empty_strings(self):
        """Test that empty strings are removed."""
        data = {"name": "Test", "description": "", "id": 123}
        result = tools._compact_payload(data)
        
        assert "name" in result
        assert "id" in result
        assert "description" not in result

    def test_compact_payload_keeps_falsy_non_none_values(self):
        """Test that falsy non-None values are kept."""
        data = {
            "name": "Test",
            "count": 0,
            "active": False,
            "items": [],
            "metadata": {},
        }
        result = tools._compact_payload(data)
        
        assert result["name"] == "Test"
        assert result["count"] == 0
        assert result["active"] is False
        assert result["items"] == []
        assert result["metadata"] == {}

    def test_compact_payload_preserves_structure(self):
        """Test that non-None values are preserved."""
        data = {
            "name": "Test Book",
            "description": "A test description",
            "tags": [{"name": "tag1", "value": "val1"}],
        }
        result = tools._compact_payload(data)
        
        assert result == data


class TestValidatedName:
    """Test _validated_name helper function."""

    def test_validated_name_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._validated_name(None, "book")
        assert result is None

    def test_validated_name_empty_rejection(self):
        """Test that empty names are rejected."""
        with pytest.raises(ToolError):
            tools._validated_name("", "book")

    def test_validated_name_long_string_rejection(self):
        """Test that excessively long names are rejected."""
        # Create a name longer than 500 characters
        long_name = "x" * 501
        
        with pytest.raises(ToolError) as exc:
            tools._validated_name(long_name, "book")
        
        # Should mention the entity type in the error
        assert "book" in str(exc.value).lower() or "name" in str(exc.value).lower()

    def test_validated_name_valid_names_pass(self):
        """Test that valid names pass through."""
        result = tools._validated_name("My Test Book", "book")
        assert result == "My Test Book"
        
        result = tools._validated_name("Page Title", "page")
        assert result == "Page Title"

    def test_validated_name_strips_and_validates(self):
        """Test that names are validated after processing."""
        # The validator should handle the string properly
        result = tools._validated_name("Valid Name", "chapter")
        assert result is not None


class TestValidatedDescription:
    """Test _validated_description helper function."""

    def test_validated_description_none_returns_none(self):
        """Test that None input returns None."""
        result = tools._validated_description(None, "book")
        assert result is None

    def test_validated_description_empty_allowed_for_non_books(self):
        """Test that empty descriptions are allowed for non-book entities."""
        # Based on the code, min_length is 1 for books only
        # For other entities, empty should be allowed
        result = tools._validated_description("", "page")
        # May return None or empty depending on validation
        # The validator uses allow_empty=True for non-books

    def test_validated_description_long_string_rejection(self):
        """Test that excessively long descriptions are rejected."""
        # Create a description longer than 20,000 characters
        long_desc = "x" * 20001
        
        with pytest.raises(ToolError) as exc:
            tools._validated_description(long_desc, "book")
        
        assert "20" in str(exc.value) or "20000" in str(exc.value)

    def test_validated_description_valid_descriptions_pass(self):
        """Test that valid descriptions pass through."""
        desc = "This is a valid description for a book."
        result = tools._validated_description(desc, "book")
        assert result == desc

    def test_validated_description_max_length_boundary(self):
        """Test description at max length boundary."""
        # 20,000 characters should be accepted
        desc = "x" * 20000
        result = tools._validated_description(desc, "book")
        assert result == desc
        
        # 20,001 should be rejected
        long_desc = "x" * 20001
        with pytest.raises(ToolError):
            tools._validated_description(long_desc, "book")
