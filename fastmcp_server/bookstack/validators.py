"""Enhanced input validation and sanitization for BookStack MCP server."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """Comprehensive input validation for BookStack operations."""
    
    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b.*=.*|1\s*=\s*1)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.\\",
    ]
    
    # Size limits
    MAX_STRING_LENGTH = 100_000  # 100KB
    MAX_ARRAY_LENGTH = 10_000
    MAX_OBJECT_DEPTH = 10
    
    @classmethod
    def validate_string(
        cls,
        value: str,
        field_name: str,
        *,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        allow_empty: bool = False,
        check_sql_injection: bool = True,
        check_xss: bool = True,
        check_path_traversal: bool = False,
    ) -> str:
        """Validate and sanitize string input."""
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")
        
        if not allow_empty and not value.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        
        # Length validation
        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"{field_name} must be at most {max_length} characters")
        
        if len(value) > cls.MAX_STRING_LENGTH:
            raise ValidationError(f"{field_name} exceeds maximum length of {cls.MAX_STRING_LENGTH}")
        
        # Pattern validation
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"{field_name} does not match required pattern")
        
        # Security checks
        if check_sql_injection:
            for sql_pattern in cls.SQL_INJECTION_PATTERNS:
                if re.search(sql_pattern, value, re.IGNORECASE):
                    raise ValidationError(f"{field_name} contains potentially malicious SQL patterns")
        
        if check_xss:
            for xss_pattern in cls.XSS_PATTERNS:
                if re.search(xss_pattern, value, re.IGNORECASE):
                    raise ValidationError(f"{field_name} contains potentially malicious XSS patterns")
        
        if check_path_traversal:
            for path_pattern in cls.PATH_TRAVERSAL_PATTERNS:
                if re.search(path_pattern, value, re.IGNORECASE):
                    raise ValidationError(f"{field_name} contains path traversal patterns")
        
        return value
    
    @classmethod
    def validate_integer(
        cls,
        value: Any,
        field_name: str,
        *,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        allow_none: bool = False,
    ) -> Optional[int]:
        """Validate integer input."""
        
        if value is None:
            if allow_none:
                return None
            raise ValidationError(f"{field_name} cannot be None")
        
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError(f"{field_name} must be an integer, got {type(value).__name__}")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
        
        return value
    
    @classmethod
    def validate_url(
        cls,
        value: str,
        field_name: str,
        *,
        allowed_schemes: Optional[List[str]] = None,
        allow_localhost: bool = False,
    ) -> str:
        """Validate URL input."""
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        try:
            parsed = urlparse(value)
        except Exception as e:
            raise ValidationError(f"{field_name} is not a valid URL: {e}")
        
        if not parsed.scheme:
            raise ValidationError(f"{field_name} must include a scheme (http/https)")
        
        if allowed_schemes and parsed.scheme not in allowed_schemes:
            raise ValidationError(
                f"{field_name} scheme must be one of {allowed_schemes}, got {parsed.scheme}"
            )
        
        if not allow_localhost and parsed.hostname in ["localhost", "127.0.0.1", "::1"]:
            raise ValidationError(f"{field_name} cannot point to localhost")
        
        return value
    
    @classmethod
    def validate_array(
        cls,
        value: Any,
        field_name: str,
        *,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        item_validator: Optional[callable] = None,
    ) -> List[Any]:
        """Validate array input."""
        
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"{field_name} must be an array, got {type(value).__name__}")
        
        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"{field_name} must have at least {min_length} items")
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"{field_name} must have at most {max_length} items")
        
        if len(value) > cls.MAX_ARRAY_LENGTH:
            raise ValidationError(f"{field_name} exceeds maximum length of {cls.MAX_ARRAY_LENGTH}")
        
        # Validate each item
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_items.append(item_validator(item, f"{field_name}[{i}]"))
                except ValidationError as e:
                    raise ValidationError(f"Invalid item at {field_name}[{i}]: {e}")
            return validated_items
        
        return list(value)
    
    @classmethod
    def validate_object(
        cls,
        value: Any,
        field_name: str,
        *,
        required_keys: Optional[List[str]] = None,
        allowed_keys: Optional[List[str]] = None,
        max_depth: int = MAX_OBJECT_DEPTH,
        current_depth: int = 0,
    ) -> Dict[str, Any]:
        """Validate object/dictionary input."""
        
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name} must be an object, got {type(value).__name__}")
        
        if current_depth > max_depth:
            raise ValidationError(f"{field_name} exceeds maximum nesting depth of {max_depth}")
        
        # Check required keys
        if required_keys:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValidationError(f"{field_name} missing required keys: {missing_keys}")
        
        # Check allowed keys
        if allowed_keys:
            extra_keys = set(value.keys()) - set(allowed_keys)
            if extra_keys:
                raise ValidationError(f"{field_name} contains unexpected keys: {extra_keys}")
        
        # Recursively validate nested objects
        validated = {}
        for key, val in value.items():
            if isinstance(val, dict):
                validated[key] = cls.validate_object(
                    val,
                    f"{field_name}.{key}",
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                )
            else:
                validated[key] = val
        
        return validated
    
    @classmethod
    def sanitize_html(cls, value: str, field_name: str) -> str:
        """Sanitize HTML content (basic implementation)."""
        
        # Remove script tags
        value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        value = re.sub(r"\son\w+\s*=\s*[\"'][^\"']*[\"']", "", value, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)
        
        return value
    
    @classmethod
    def validate_markdown(cls, value: str, field_name: str) -> str:
        """Validate markdown content."""
        
        # Basic validation - markdown is generally safe
        # but we still check for XSS in embedded HTML
        
        # Extract HTML blocks
        html_blocks = re.findall(r"<[^>]+>", value)
        for html in html_blocks:
            # Check for dangerous patterns
            for xss_pattern in cls.XSS_PATTERNS:
                if re.search(xss_pattern, html, re.IGNORECASE):
                    raise ValidationError(f"{field_name} contains potentially malicious HTML")
        
        return value


class BookStackValidator:
    """Specialized validators for BookStack entities."""
    
    @staticmethod
    def validate_entity_id(entity_id: Any, entity_type: str) -> int:
        """Validate entity ID."""
        return InputValidator.validate_integer(
            entity_id,
            f"{entity_type}_id",
            min_value=1,
        )
    
    @staticmethod
    def validate_entity_name(name: str, entity_type: str) -> str:
        """Validate entity name."""
        return InputValidator.validate_string(
            name,
            f"{entity_type}_name",
            min_length=1,
            max_length=500,
            check_sql_injection=True,
            check_xss=True,
        )
    
    @staticmethod
    def validate_tags(tags: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate tag array."""
        
        def validate_tag(tag: Dict[str, str], field_name: str) -> Dict[str, str]:
            validated = InputValidator.validate_object(
                tag,
                field_name,
                required_keys=["name", "value"],
                allowed_keys=["name", "value"],
            )
            
            validated["name"] = InputValidator.validate_string(
                validated["name"],
                f"{field_name}.name",
                min_length=1,
                max_length=100,
            )
            
            validated["value"] = InputValidator.validate_string(
                validated["value"],
                f"{field_name}.value",
                max_length=500,
                allow_empty=True,
            )
            
            return validated
        
        return InputValidator.validate_array(
            tags,
            "tags",
            max_length=100,
            item_validator=validate_tag,
        )

