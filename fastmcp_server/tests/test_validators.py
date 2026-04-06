"""Comprehensive tests for input validation and sanitization."""
from __future__ import annotations

from typing import Any, Dict

import pytest

from fastmcp_server.bookstack.validators import (
    BookStackValidator,
    InputValidator,
    ValidationError,
)


class TestInputValidatorString:
    """Test InputValidator.validate_string method."""

    def test_validate_string_accepts_valid_input(self) -> None:
        result = InputValidator.validate_string("Hello World", "test_field")
        assert result == "Hello World"

    def test_validate_string_rejects_non_string(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string(123, "test_field")
        assert "must be a string" in str(exc.value)
        assert "got int" in str(exc.value)

    def test_validate_string_rejects_empty_when_not_allowed(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("   ", "test_field", allow_empty=False)
        assert "cannot be empty" in str(exc.value)

    def test_validate_string_accepts_empty_when_allowed(self) -> None:
        result = InputValidator.validate_string("   ", "test_field", allow_empty=True)
        assert result == "   "

    def test_validate_string_enforces_min_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("Hi", "test_field", min_length=5)
        assert "must be at least 5 characters" in str(exc.value)

    def test_validate_string_enforces_max_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("Hello", "test_field", max_length=3)
        assert "must be at most 3 characters" in str(exc.value)

    def test_validate_string_enforces_absolute_max_length(self) -> None:
        huge_string = "x" * (InputValidator.MAX_STRING_LENGTH + 1)
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string(huge_string, "test_field")
        assert "exceeds maximum length" in str(exc.value)

    def test_validate_string_pattern_matching(self) -> None:
        # Valid pattern
        result = InputValidator.validate_string("abc123", "test_field", pattern=r"^[a-z0-9]+$")
        assert result == "abc123"

        # Invalid pattern
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("ABC!", "test_field", pattern=r"^[a-z0-9]+$")
        assert "does not match required pattern" in str(exc.value)


class TestInputValidatorSQLInjection:
    """Test SQL injection detection patterns."""

    def test_detects_select_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test' OR 1=1; SELECT * FROM users--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_drop_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("'; DROP TABLE users;--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_insert_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; INSERT INTO admin VALUES('hacker', 'pass');--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_update_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; UPDATE users SET admin=1;--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_delete_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; DELETE FROM users;--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_create_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; CREATE TABLE hacked (id INT);--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_alter_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; ALTER TABLE users ADD COLUMN hacked INT;--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_exec_statement_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'; EXEC sp_executesql @sql;--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_sql_comment_patterns_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("test'--", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_detects_sql_or_equals_pattern_when_enabled(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("admin' OR '1'='1", "test_field", check_sql_injection=True)
        assert "malicious SQL patterns" in str(exc.value)

    def test_sql_keywords_allowed_by_default(self) -> None:
        result = InputValidator.validate_string(
            "How to SELECT data from a database", "test_field"
        )
        assert result == "How to SELECT data from a database"


class TestInputValidatorXSS:
    """Test XSS pattern detection."""

    def test_detects_script_tags(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("<script>alert('xss')</script>", "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_detects_javascript_protocol(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<a href="javascript:alert(1)">click</a>', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_detects_event_handlers(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<img src=x onerror=alert(1)>', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<div onclick="malicious()">Click me</div>', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_detects_iframe_tags(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<iframe src="evil.com"></iframe>', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_detects_object_tags(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<object data="evil.swf"></object>', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_detects_embed_tags(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string('<embed src="evil.swf">', "test_field")
        assert "malicious XSS patterns" in str(exc.value)

    def test_xss_check_can_be_disabled(self) -> None:
        result = InputValidator.validate_string(
            "<script>console.log('dev')</script>", "test_field", check_xss=False
        )
        assert result == "<script>console.log('dev')</script>"


class TestInputValidatorPathTraversal:
    """Test path traversal detection."""

    def test_detects_dotdot_slash(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("../../etc/passwd", "test_field", check_path_traversal=True)
        assert "path traversal patterns" in str(exc.value)

    def test_detects_dotdot_alone(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("files/..", "test_field", check_path_traversal=True)
        assert "path traversal patterns" in str(exc.value)

    def test_detects_url_encoded_dotdot(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("files/%2e%2e/secret", "test_field", check_path_traversal=True)
        assert "path traversal patterns" in str(exc.value)

    def test_detects_backslash_dotdot(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_string("..\\windows\\system32", "test_field", check_path_traversal=True)
        assert "path traversal patterns" in str(exc.value)

    def test_path_traversal_check_disabled_by_default(self) -> None:
        result = InputValidator.validate_string("../../etc/passwd", "test_field")
        assert result == "../../etc/passwd"


class TestInputValidatorInteger:
    """Test InputValidator.validate_integer method."""

    def test_validate_integer_accepts_valid_int(self) -> None:
        result = InputValidator.validate_integer(42, "test_field")
        assert result == 42

    def test_validate_integer_rejects_non_int(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer("42", "test_field")
        assert "must be an integer" in str(exc.value)
        assert "got str" in str(exc.value)

    def test_validate_integer_rejects_bool(self) -> None:
        # Python bools are technically ints, but we explicitly reject them
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer(True, "test_field")
        assert "must be an integer" in str(exc.value)

    def test_validate_integer_enforces_min_value(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer(5, "test_field", min_value=10)
        assert "must be at least 10" in str(exc.value)

    def test_validate_integer_enforces_max_value(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer(100, "test_field", max_value=50)
        assert "must be at most 50" in str(exc.value)

    def test_validate_integer_handles_none_when_not_allowed(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_integer(None, "test_field", allow_none=False)
        assert "cannot be None" in str(exc.value)

    def test_validate_integer_handles_none_when_allowed(self) -> None:
        result = InputValidator.validate_integer(None, "test_field", allow_none=True)
        assert result is None


class TestInputValidatorArray:
    """Test InputValidator.validate_array method."""

    def test_validate_array_accepts_list(self) -> None:
        result = InputValidator.validate_array([1, 2, 3], "test_field")
        assert result == [1, 2, 3]

    def test_validate_array_accepts_tuple(self) -> None:
        result = InputValidator.validate_array((1, 2, 3), "test_field")
        assert result == [1, 2, 3]

    def test_validate_array_rejects_non_array(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_array("not an array", "test_field")
        assert "must be an array" in str(exc.value)
        assert "got str" in str(exc.value)

    def test_validate_array_enforces_min_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_array([1, 2], "test_field", min_length=5)
        assert "must have at least 5 items" in str(exc.value)

    def test_validate_array_enforces_max_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_array([1, 2, 3, 4, 5], "test_field", max_length=3)
        assert "must have at most 3 items" in str(exc.value)

    def test_validate_array_enforces_absolute_max_length(self) -> None:
        huge_array = list(range(InputValidator.MAX_ARRAY_LENGTH + 1))
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_array(huge_array, "test_field")
        assert "exceeds maximum length" in str(exc.value)

    def test_validate_array_with_item_validator(self) -> None:
        def validate_positive_int(value: Any, field_name: str) -> int:
            if not isinstance(value, int) or value <= 0:
                raise ValidationError(f"{field_name} must be a positive integer")
            return value

        result = InputValidator.validate_array(
            [1, 2, 3], "test_field", item_validator=validate_positive_int
        )
        assert result == [1, 2, 3]

    def test_validate_array_item_validator_rejects_invalid(self) -> None:
        def validate_positive_int(value: Any, field_name: str) -> int:
            if not isinstance(value, int) or value <= 0:
                raise ValidationError(f"{field_name} must be a positive integer")
            return value

        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_array(
                [1, -2, 3], "test_field", item_validator=validate_positive_int
            )
        assert "Invalid item at test_field[1]" in str(exc.value)


class TestInputValidatorObject:
    """Test InputValidator.validate_object method."""

    def test_validate_object_accepts_dict(self) -> None:
        result = InputValidator.validate_object({"key": "value"}, "test_field")
        assert result == {"key": "value"}

    def test_validate_object_rejects_non_dict(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_object("not a dict", "test_field")
        assert "must be an object" in str(exc.value)
        assert "got str" in str(exc.value)

    def test_validate_object_enforces_required_keys(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_object(
                {"name": "test"}, "test_field", required_keys=["name", "value"]
            )
        assert "missing required keys" in str(exc.value)
        assert "value" in str(exc.value)

    def test_validate_object_enforces_allowed_keys(self) -> None:
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_object(
                {"name": "test", "extra": "bad"}, "test_field", allowed_keys=["name", "value"]
            )
        assert "contains unexpected keys" in str(exc.value)
        assert "extra" in str(exc.value)

    def test_validate_object_enforces_max_depth(self) -> None:
        nested = {"level1": {"level2": {"level3": "value"}}}
        with pytest.raises(ValidationError) as exc:
            InputValidator.validate_object(nested, "test_field", max_depth=1)
        assert "exceeds maximum nesting depth" in str(exc.value)

    def test_validate_object_validates_nested_objects(self) -> None:
        nested = {"outer": {"inner": {"deep": "value"}}}
        result = InputValidator.validate_object(nested, "test_field", max_depth=10)
        assert result == nested


class TestBookStackValidatorEntityID:
    """Test BookStackValidator.validate_entity_id method."""

    def test_validate_entity_id_accepts_positive_int(self) -> None:
        result = BookStackValidator.validate_entity_id(42, "book")
        assert result == 42

    def test_validate_entity_id_rejects_zero(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_id(0, "book")
        assert "must be at least 1" in str(exc.value)

    def test_validate_entity_id_rejects_negative(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_id(-5, "page")
        assert "must be at least 1" in str(exc.value)

    def test_validate_entity_id_rejects_non_int(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_id("42", "chapter")
        assert "must be an integer" in str(exc.value)


class TestBookStackValidatorEntityName:
    """Test BookStackValidator.validate_entity_name method."""

    def test_validate_entity_name_accepts_valid_name(self) -> None:
        result = BookStackValidator.validate_entity_name("My Book Title", "book")
        assert result == "My Book Title"

    def test_validate_entity_name_enforces_min_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_name("", "book")
        assert "cannot be empty" in str(exc.value) or "must be at least 1 characters" in str(exc.value)

    def test_validate_entity_name_enforces_max_length(self) -> None:
        long_name = "x" * 501
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_name(long_name, "page")
        assert "must be at most 500 characters" in str(exc.value)

    def test_validate_entity_name_allows_sql_keywords(self) -> None:
        result = BookStackValidator.validate_entity_name("How to SELECT and DROP data", "book")
        assert result == "How to SELECT and DROP data"

    def test_validate_entity_name_checks_xss(self) -> None:
        with pytest.raises(ValidationError) as exc:
            BookStackValidator.validate_entity_name("<script>alert('xss')</script>", "book")
        assert "malicious XSS patterns" in str(exc.value)


class TestValidationError:
    """Test ValidationError is the correct exception type."""

    def test_validation_error_is_exception(self) -> None:
        err = ValidationError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"

    def test_validators_raise_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            InputValidator.validate_string(123, "test")

        with pytest.raises(ValidationError):
            InputValidator.validate_integer("not_int", "test")

        with pytest.raises(ValidationError):
            InputValidator.validate_array("not_array", "test")

        with pytest.raises(ValidationError):
            InputValidator.validate_object("not_object", "test")
