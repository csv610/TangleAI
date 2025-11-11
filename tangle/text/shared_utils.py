"""
Shared utilities and constants for Perplexity CLI tools.

Provides standardized formatting, error handling, and validation functions.
"""

import sys
from typing import Optional

# ============================================================================
# CONSTANTS
# ============================================================================

# Standard output formatting
SEPARATOR = "=" * 60
INDENT = "  "

# Status indicators
SUCCESS = "✓"
ERROR = "❌"
SEARCH = "🔍"
INFO = "ℹ"
SUMMARY = "📊"


# ============================================================================
# PRINTING FUNCTIONS
# ============================================================================

def success(message: str) -> None:
    """Print a success message."""
    print(f"{SUCCESS} {message}")


def error(message: str, exit_code: int = 1) -> None:
    """Print an error message and optionally exit."""
    print(f"{ERROR} {message}")
    if exit_code:
        sys.exit(exit_code)


def info(message: str) -> None:
    """Print an info message."""
    print(f"{INFO} {message}")


def search(message: str) -> None:
    """Print a search message."""
    print(f"{SEARCH} {message}")


def summary(message: str) -> None:
    """Print a summary message."""
    print(f"{SUMMARY} {message}")


def section(title: str, content: str) -> None:
    """
    Print a formatted section with title and content.

    Args:
        title: Section title
        content: Section content
    """
    # Calculate padding for centered title
    padding = (SEPARATOR.__len__() - len(title) - 2) // 2
    left = "=" * max(0, padding)
    right = "=" * max(0, len(SEPARATOR) - len(title) - 2 - padding)

    print(f"\n{left} {title} {right}")
    print(content)
    print(SEPARATOR)


# ============================================================================
# ERROR HANDLING
# ============================================================================

def api_error(error_msg: str, context: str = "") -> None:
    """
    Handle API errors consistently.

    Args:
        error_msg: The error message
        context: Optional context about what was being done
    """
    prefix = f"({context})" if context else ""
    error(f"API Error {prefix}: {error_msg}", exit_code=1)


def file_error(error_msg: str, filename: str = "") -> None:
    """
    Handle file errors consistently.

    Args:
        error_msg: The error message
        filename: Optional filename that caused the error
    """
    context = f"with {filename}" if filename else ""
    error(f"File Error {context}: {error_msg}", exit_code=1)


# ============================================================================
# VALIDATION
# ============================================================================

def not_empty(value: str, field_name: str) -> str:
    """
    Validate that a string is not empty.

    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated, stripped value

    Raises:
        ValueError: If value is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return value.strip()


def in_range(value: int, min_val: int, max_val: int, field_name: str) -> int:
    """
    Validate that an integer is within a range.

    Args:
        value: The value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field_name: Name of the field (for error messages)

    Returns:
        The validated value

    Raises:
        ValueError: If value is outside the range
    """
    if not min_val <= value <= max_val:
        raise ValueError(
            f"{field_name} must be between {min_val} and {max_val}, got {value}"
        )
    return value


# ============================================================================
# FORMATTING
# ============================================================================

def format_list(items: list, indent: bool = True) -> str:
    """
    Format a list of items for display.

    Args:
        items: List of items to format
        indent: Whether to indent items (default: True)

    Returns:
        Formatted string
    """
    if not items:
        return "(empty)"

    prefix = INDENT if indent else ""
    formatted_items = [f"{prefix}{i + 1}. {item}" for i, item in enumerate(items)]
    return "\n".join(formatted_items)


def format_dict(data: dict, indent: bool = True) -> str:
    """
    Format a dictionary for display.

    Args:
        data: Dictionary to format
        indent: Whether to indent items (default: True)

    Returns:
        Formatted string
    """
    if not data:
        return "(empty)"

    prefix = INDENT if indent else ""
    lines = [f"{prefix}{k}: {v}" for k, v in data.items()]
    return "\n".join(lines)
