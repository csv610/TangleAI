"""
Unit tests for shared_utils.py

Tests printing functions, validation, and formatting utilities.
"""

import sys
import unittest
from io import StringIO
from shared_utils import (
    success, error, info, search, summary, section,
    not_empty, in_range, format_list, format_dict,
    SEPARATOR, INDENT
)


class TestPrintingFunctions(unittest.TestCase):
    """Tests for printing utility functions."""

    def setUp(self):
        """Capture stdout."""
        self.held_output = StringIO()

    def tearDown(self):
        """Restore stdout."""
        sys.stdout = sys.__stdout__

    def test_success_message(self):
        """Test success message printing."""
        sys.stdout = self.held_output
        success("Test message")
        output = self.held_output.getvalue()

        self.assertIn("✓", output)
        self.assertIn("Test message", output)

    def test_error_message_no_exit(self):
        """Test error message without exit."""
        sys.stdout = self.held_output
        error("Error message", exit_code=0)
        output = self.held_output.getvalue()

        self.assertIn("❌", output)
        self.assertIn("Error message", output)

    def test_error_message_with_exit(self):
        """Test error message with exit code."""
        sys.stdout = self.held_output

        with self.assertRaises(SystemExit) as context:
            error("Critical error", exit_code=1)

        self.assertEqual(context.exception.code, 1)

    def test_info_message(self):
        """Test info message printing."""
        sys.stdout = self.held_output
        info("Info message")
        output = self.held_output.getvalue()

        self.assertIn("ℹ", output)
        self.assertIn("Info message", output)

    def test_search_message(self):
        """Test search message printing."""
        sys.stdout = self.held_output
        search("Searching...")
        output = self.held_output.getvalue()

        self.assertIn("🔍", output)
        self.assertIn("Searching...", output)

    def test_summary_message(self):
        """Test summary message printing."""
        sys.stdout = self.held_output
        summary("Summary text")
        output = self.held_output.getvalue()

        self.assertIn("📊", output)
        self.assertIn("Summary text", output)

    def test_section_formatting(self):
        """Test section header formatting."""
        sys.stdout = self.held_output
        section("TEST TITLE", "Test content here")
        output = self.held_output.getvalue()

        self.assertIn("TEST TITLE", output)
        self.assertIn("Test content here", output)
        self.assertIn("=", output)  # Separator


class TestValidationFunctions(unittest.TestCase):
    """Tests for validation utility functions."""

    def test_not_empty_valid(self):
        """Test not_empty with valid input."""
        result = not_empty("hello", "name")
        self.assertEqual(result, "hello")

    def test_not_empty_with_whitespace(self):
        """Test not_empty strips whitespace."""
        result = not_empty("  hello  ", "name")
        self.assertEqual(result, "hello")

    def test_not_empty_empty_string(self):
        """Test not_empty with empty string."""
        with self.assertRaises(ValueError) as context:
            not_empty("", "name")
        self.assertIn("name cannot be empty", str(context.exception))

    def test_not_empty_whitespace_only(self):
        """Test not_empty with whitespace only."""
        with self.assertRaises(ValueError) as context:
            not_empty("   ", "name")
        self.assertIn("name cannot be empty", str(context.exception))

    def test_in_range_valid(self):
        """Test in_range with valid input."""
        result = in_range(5, 1, 10, "value")
        self.assertEqual(result, 5)

    def test_in_range_boundary_min(self):
        """Test in_range at minimum boundary."""
        result = in_range(1, 1, 10, "value")
        self.assertEqual(result, 1)

    def test_in_range_boundary_max(self):
        """Test in_range at maximum boundary."""
        result = in_range(10, 1, 10, "value")
        self.assertEqual(result, 10)

    def test_in_range_below_min(self):
        """Test in_range below minimum."""
        with self.assertRaises(ValueError) as context:
            in_range(0, 1, 10, "value")
        self.assertIn("between 1 and 10", str(context.exception))

    def test_in_range_above_max(self):
        """Test in_range above maximum."""
        with self.assertRaises(ValueError) as context:
            in_range(11, 1, 10, "value")
        self.assertIn("between 1 and 10", str(context.exception))

    def test_in_range_negative(self):
        """Test in_range with negative values."""
        result = in_range(-5, -10, 0, "value")
        self.assertEqual(result, -5)


class TestFormattingFunctions(unittest.TestCase):
    """Tests for formatting utility functions."""

    def test_format_list_empty(self):
        """Test format_list with empty list."""
        result = format_list([])
        self.assertEqual(result, "(empty)")

    def test_format_list_single_item(self):
        """Test format_list with single item."""
        result = format_list(["item1"])
        self.assertIn("1. item1", result)

    def test_format_list_multiple_items(self):
        """Test format_list with multiple items."""
        result = format_list(["item1", "item2", "item3"])
        self.assertIn("1. item1", result)
        self.assertIn("2. item2", result)
        self.assertIn("3. item3", result)

    def test_format_list_with_indent(self):
        """Test format_list with indentation."""
        result = format_list(["item1"], indent=True)
        self.assertIn(INDENT, result)

    def test_format_list_without_indent(self):
        """Test format_list without indentation."""
        result = format_list(["item1"], indent=False)
        self.assertEqual(result.startswith(INDENT), False)

    def test_format_dict_empty(self):
        """Test format_dict with empty dictionary."""
        result = format_dict({})
        self.assertEqual(result, "(empty)")

    def test_format_dict_single_item(self):
        """Test format_dict with single item."""
        result = format_dict({"key": "value"})
        self.assertIn("key: value", result)

    def test_format_dict_multiple_items(self):
        """Test format_dict with multiple items."""
        result = format_dict({"a": "1", "b": "2", "c": "3"})
        self.assertIn("a: 1", result)
        self.assertIn("b: 2", result)
        self.assertIn("c: 3", result)

    def test_format_dict_with_indent(self):
        """Test format_dict with indentation."""
        result = format_dict({"key": "value"}, indent=True)
        self.assertIn(INDENT, result)

    def test_format_dict_without_indent(self):
        """Test format_dict without indentation."""
        result = format_dict({"key": "value"}, indent=False)
        self.assertFalse(result.startswith(INDENT))


class TestConstants(unittest.TestCase):
    """Tests for constant values."""

    def test_separator_length(self):
        """Test SEPARATOR is 60 characters."""
        self.assertEqual(len(SEPARATOR), 60)
        self.assertTrue(all(c == "=" for c in SEPARATOR))

    def test_indent_value(self):
        """Test INDENT is 2 spaces."""
        self.assertEqual(INDENT, "  ")


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases."""

    def test_format_list_with_special_characters(self):
        """Test format_list with special characters."""
        items = ["item with spaces", "item\nwith\nnewlines", "item🎉with🎉emojis"]
        result = format_list(items)
        for item in items:
            self.assertIn(item, result)

    def test_format_dict_with_special_values(self):
        """Test format_dict with special values."""
        data = {
            "normal": "value",
            "spaces": "value with spaces",
            "newline": "value\nwith\nnewline",
            "special": "値"
        }
        result = format_dict(data)
        for k, v in data.items():
            self.assertIn(f"{k}: {v}", result)

    def test_in_range_with_negative_range(self):
        """Test in_range with negative numbers."""
        result = in_range(-50, -100, -10, "negative value")
        self.assertEqual(result, -50)

    def test_not_empty_with_numbers(self):
        """Test not_empty converts to string."""
        # String numbers should work
        result = not_empty("123", "number")
        self.assertEqual(result, "123")


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestPrintingFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestFormattingFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
