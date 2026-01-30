"""
Input validation utilities for Disease-Relater API.

Provides validation functions for ICD codes, numeric parameters, and other inputs.
All validation functions return boolean status and optional error messages.
"""

import re
from typing import Optional, Tuple, Union


# ICD-10 code pattern: letter followed by 2 digits, optional decimal and 1-2 digits
# Examples: E11, E11.9, I10, A01.01
ICD_CODE_PATTERN = re.compile(r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$")

# Chapter code pattern: Roman numerals or letters (I, II, X, IX, etc.)
CHAPTER_CODE_PATTERN = re.compile(
    r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|XXI|[A-Z])$"
)

# Age group pattern: ranges like "0-9", "10-19", "70-79"
AGE_GROUP_PATTERN = re.compile(r"^\d{1,2}-\d{1,2}$")

# Valid sex values
VALID_SEX_VALUES = {"Male", "Female", "All"}

# Valid relationship strengths
VALID_RELATIONSHIP_STRENGTHS = {"weak", "moderate", "strong", "very_strong"}


def validate_icd_code(code: str) -> Tuple[bool, Optional[str]]:
    """Validate ICD-10 code format.

    ICD-10 codes follow the pattern: Letter + 2 digits + optional decimal
    Examples: E11 (diabetes), I10 (hypertension), A01.01 (typhoid)

    Args:
        code: ICD-10 code string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if code format is valid
        - error_message: None if valid, error description if invalid

    Examples:
        >>> validate_icd_code("E11")
        (True, None)
        >>> validate_icd_code("E11.9")
        (True, None)
        >>> validate_icd_code("invalid")
        (False, "Invalid ICD-10 code format")
        >>> validate_icd_code("")
        (False, "ICD code cannot be empty")
    """
    if not code:
        return False, "ICD code cannot be empty"

    if not isinstance(code, str):
        return False, "ICD code must be a string"

    code = code.strip().upper()

    if len(code) < 3:
        return False, "ICD code must be at least 3 characters (e.g., E11)"

    if len(code) > 7:
        return False, "ICD code too long (max 7 characters)"

    if not ICD_CODE_PATTERN.match(code):
        return (
            False,
            "Invalid ICD-10 code format (expected: Letter + 2 digits + optional decimal, e.g., E11 or E11.9)",
        )

    return True, None


def validate_chapter_code(chapter: str) -> Tuple[bool, Optional[str]]:
    """Validate ICD chapter code format.

    Chapter codes are Roman numerals I-XXI or single letters.
    Examples: I (Infectious), IX (Circulatory), X (Respiratory)

    Args:
        chapter: Chapter code string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_chapter_code("IX")
        (True, None)
        >>> validate_chapter_code("X")
        (True, None)
        >>> validate_chapter_code("25")
        (False, "Invalid chapter code format")
    """
    if not chapter:
        return False, "Chapter code cannot be empty"

    if not isinstance(chapter, str):
        return False, "Chapter code must be a string"

    chapter = chapter.strip().upper()

    if not CHAPTER_CODE_PATTERN.match(chapter):
        return (
            False,
            "Invalid chapter code format (expected: Roman numeral I-XXI or single letter, e.g., IX, X, I)",
        )

    return True, None


def validate_limit(
    limit: Union[int, str], max_allowed: int = 1000
) -> Tuple[bool, Optional[str]]:
    """Validate pagination limit parameter.

    Args:
        limit: Limit value to validate
        max_allowed: Maximum allowed limit (default: 1000)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_limit(50)
        (True, None)
        >>> validate_limit(1001)
        (False, "Limit exceeds maximum allowed value")
        >>> validate_limit(-1)
        (False, "Limit must be a positive integer")
    """
    try:
        limit_val = int(limit)
    except (ValueError, TypeError):
        return False, "Limit must be a valid integer"

    if limit_val < 1:
        return False, "Limit must be a positive integer (minimum: 1)"

    if limit_val > max_allowed:
        return False, f"Limit exceeds maximum allowed value ({max_allowed})"

    return True, None


def validate_offset(offset: Union[int, str]) -> Tuple[bool, Optional[str]]:
    """Validate pagination offset parameter.

    Args:
        offset: Offset value to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_offset(0)
        (True, None)
        >>> validate_offset(100)
        (True, None)
        >>> validate_offset(-1)
        (False, "Offset must be non-negative")
    """
    try:
        offset_val = int(offset)
    except (ValueError, TypeError):
        return False, "Offset must be a valid integer"

    if offset_val < 0:
        return False, "Offset must be a non-negative integer (minimum: 0)"

    return True, None


def validate_odds_ratio(value: Union[float, str, int]) -> Tuple[bool, Optional[str]]:
    """Validate odds ratio parameter.

    Odds ratios must be positive numbers, typically > 1.0 for meaningful associations.

    Args:
        value: Odds ratio value to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_odds_ratio(1.5)
        (True, None)
        >>> validate_odds_ratio(0.5)
        (False, "Odds ratio must be >= 1.0")
        >>> validate_odds_ratio(-1)
        (False, "Odds ratio must be positive")
    """
    try:
        or_val = float(value)
    except (ValueError, TypeError):
        return False, "Odds ratio must be a valid number"

    if or_val <= 0:
        return False, "Odds ratio must be a positive number (> 0)"

    if or_val < 1.0:
        return False, "Odds ratio must be >= 1.0 for meaningful associations"

    return True, None


def validate_search_term(
    term: str, min_length: int = 2, max_length: int = 100
) -> Tuple[bool, Optional[str]]:
    """Validate disease search term.

    Args:
        term: Search term to validate
        min_length: Minimum search term length (default: 2)
        max_length: Maximum search term length (default: 100)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_search_term("diabetes")
        (True, None)
        >>> validate_search_term("ab")
        (True, None)
        >>> validate_search_term("a")
        (False, "Search term too short")
    """
    if not term:
        return False, "Search term cannot be empty"

    if not isinstance(term, str):
        return False, "Search term must be a string"

    term = term.strip()

    if len(term) < min_length:
        return False, f"Search term too short (minimum {min_length} characters)"

    if len(term) > max_length:
        return False, f"Search term too long (maximum {max_length} characters)"

    # Check for suspicious characters (basic SQL injection prevention)
    suspicious = [";", "--", "/*", "*/", "DROP", "DELETE", "INSERT", "UPDATE"]
    term_upper = term.upper()
    for char in suspicious:
        if char in term_upper:
            return False, "Search term contains invalid characters"

    return True, None


def validate_sex(value: str) -> Tuple[bool, Optional[str]]:
    """Validate sex parameter.

    Args:
        value: Sex value to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_sex("Male")
        (True, None)
        >>> validate_sex("Female")
        (True, None)
        >>> validate_sex("All")
        (True, None)
        >>> validate_sex("Other")
        (False, "Invalid sex value")
    """
    if not value:
        return False, "Sex parameter cannot be empty"

    if value not in VALID_SEX_VALUES:
        return (
            False,
            f"Invalid sex value. Must be one of: {', '.join(sorted(VALID_SEX_VALUES))}",
        )

    return True, None


def validate_age_group(age_group: str) -> Tuple[bool, Optional[str]]:
    """Validate age group parameter.

    Args:
        age_group: Age group string to validate (e.g., "0-9", "70-79")

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_age_group("0-9")
        (True, None)
        >>> validate_age_group("70-79")
        (True, None)
        >>> validate_age_group("invalid")
        (False, "Invalid age group format")
    """
    if not age_group:
        return False, "Age group cannot be empty"

    if not AGE_GROUP_PATTERN.match(age_group):
        return (
            False,
            "Invalid age group format (expected: 'start-end', e.g., '0-9', '70-79')",
        )

    # Validate range logic
    try:
        start, end = map(int, age_group.split("-"))
        if start >= end:
            return False, "Invalid age group: start must be less than end"
        if start < 0 or end > 120:
            return False, "Invalid age group: ages must be between 0 and 120"
    except ValueError:
        return False, "Invalid age group format"

    return True, None


def sanitize_error_message(message: str) -> str:
    """Sanitize error messages to prevent information leakage.

    Removes sensitive information like database details, file paths,
    and stack traces from error messages returned to clients.

    Args:
        message: Raw error message

    Returns:
        Sanitized error message safe for client exposure

    Examples:
        >>> sanitize_error_message("Database connection failed: postgres://user:pass@host/db")
        'Database connection failed'
        >>> sanitize_error_message("File not found: /home/user/.env")
        'File not found'
    """
    if not message:
        return "An error occurred"

    # List of patterns to remove
    patterns_to_remove = [
        r"postgres://[^\s]+",  # PostgreSQL URLs
        r"mysql://[^\s]+",  # MySQL URLs
        r"http://[^\s]+",  # HTTP URLs
        r"https://[^\s]+",  # HTTPS URLs
        r"/home/[^\s]+",  # Linux home paths
        r"/Users/[^\s]+",  # macOS home paths
        r"C:\\\\[^\s]+",  # Windows paths
        r"password[=:][^\s]+",  # Password assignments
        r"key[=:][^\s]+",  # Key assignments
        r"token[=:][^\s]+",  # Token assignments
    ]

    import re as regex

    sanitized = message
    for pattern in patterns_to_remove:
        sanitized = regex.sub(pattern, "[REDACTED]", sanitized)

    # Limit length
    if len(sanitized) > 500:
        sanitized = sanitized[:497] + "..."

    return sanitized


# Convenience functions for raising exceptions


def validate_or_raise(value, validator_func, *args, **kwargs):
    """Validate a value and raise ValueError if invalid.

    Args:
        value: Value to validate
        validator_func: Validation function to use
        *args: Additional positional arguments for validator
        **kwargs: Additional keyword arguments for validator

    Raises:
        ValueError: If validation fails

    Example:
        >>> validate_or_raise("E11", validate_icd_code)
        # Returns None if valid
        >>> validate_or_raise("invalid", validate_icd_code)
        ValueError: Invalid ICD-10 code format
    """
    is_valid, error = validator_func(value, *args, **kwargs)
    if not is_valid:
        raise ValueError(error)


if __name__ == "__main__":
    # Test validation functions
    import doctest

    doctest.testmod()

    print("Validation module tests passed!")
