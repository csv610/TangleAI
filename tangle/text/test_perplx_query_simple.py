"""
Unit tests for perplx_query.py

Tests CLI argument parsing, single queries, batch queries, and file I/O.
No pytest dependency - uses standard unittest.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import unittest
from io import StringIO


class TestQuerySingle(unittest.TestCase):
    """Tests for single query functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the PerplexityTextClient
        self.mock_client = Mock()
        self.mock_client.query = Mock(return_value="Test response from Perplexity")

    def test_query_single_basic(self):
        """Test basic single query execution."""
        from perplx_query import _query_single

        query = "What is Python?"

        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output

        _query_single(self.mock_client, query)

        sys.stdout = sys.__stdout__

        # Verify client was called
        self.mock_client.query.assert_called_with(query)

        # Verify output contains the query
        output = captured_output.getvalue()
        self.assertIn("What is Python?", output)

    def test_query_single_with_special_chars(self):
        """Test query with special characters."""
        from perplx_query import _query_single

        query = "What are 'quotes' and \"double quotes\"?"
        self.mock_client.query.reset_mock()

        captured_output = StringIO()
        sys.stdout = captured_output

        _query_single(self.mock_client, query)

        sys.stdout = sys.__stdout__

        self.mock_client.query.assert_called_with(query)

    def test_query_single_long_query(self):
        """Test with long query."""
        from perplx_query import _query_single

        query = "This is a very long query " * 10
        self.mock_client.query.reset_mock()

        captured_output = StringIO()
        sys.stdout = captured_output

        _query_single(self.mock_client, query)

        sys.stdout = sys.__stdout__

        self.mock_client.query.assert_called_once()


class TestQueryFile(unittest.TestCase):
    """Tests for file-based query functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.query = Mock(return_value="Test response")

    def test_query_file_basic(self):
        """Test loading and querying from file."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with queries
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["What is AI?", "What is ML?", "What is DL?"]
            query_file.write_text("\n".join(queries))

            self.mock_client.query.reset_mock()

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            # Verify all queries were executed
            self.assertEqual(self.mock_client.query.call_count, 3)

            # Verify output file was created
            output_file = Path(tmpdir) / "queries_responses.txt"
            self.assertTrue(output_file.exists())

            # Verify output contains all queries
            output_text = output_file.read_text()
            for query in queries:
                self.assertIn(query, output_text)

    def test_query_file_with_empty_lines(self):
        """Test file with empty lines - should skip them."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            content = """What is AI?

What is ML?

What is DL?
"""
            query_file.write_text(content)

            self.mock_client.query.reset_mock()

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            # Should only process 3 queries (empty lines skipped)
            self.assertEqual(self.mock_client.query.call_count, 3)

    def test_query_file_custom_output(self):
        """Test specifying custom output file."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["Query 1", "Query 2"]
            query_file.write_text("\n".join(queries))

            output_path = Path(tmpdir) / "custom_output.txt"

            self.mock_client.query.reset_mock()

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file), str(output_path))

            sys.stdout = sys.__stdout__

            # Verify custom output file was created
            self.assertTrue(output_path.exists())

            # Verify content is in custom file
            output_text = output_path.read_text()
            self.assertIn("Query 1", output_text)
            self.assertIn("Query 2", output_text)

    def test_query_file_not_found(self):
        """Test error when file not found."""
        from perplx_query import _query_file

        with self.assertRaises(FileNotFoundError):
            _query_file(self.mock_client, "/nonexistent/file.txt")

    def test_query_file_empty(self):
        """Test error when file has no queries."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "empty.txt"
            query_file.write_text("")  # Empty file

            with self.assertRaises(ValueError) as context:
                captured_output = StringIO()
                sys.stdout = captured_output
                _query_file(self.mock_client, str(query_file))
                sys.stdout = sys.__stdout__

            self.assertIn("No queries found", str(context.exception))

    def test_query_file_only_whitespace(self):
        """Test file with only whitespace lines."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "whitespace.txt"
            query_file.write_text("\n   \n\t\n")  # Only whitespace

            with self.assertRaises(ValueError) as context:
                captured_output = StringIO()
                sys.stdout = captured_output
                _query_file(self.mock_client, str(query_file))
                sys.stdout = sys.__stdout__

            self.assertIn("No queries found", str(context.exception))


class TestOutputFile(unittest.TestCase):
    """Tests for output file generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()

    def test_output_file_format(self):
        """Test that output file has correct format."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            query_file.write_text("Test query 1\nTest query 2")

            self.mock_client.query.reset_mock()
            self.mock_client.query.side_effect = ["Response 1", "Response 2"]

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # Check format
            self.assertIn("[Question 1]", output_text)
            self.assertIn("Test query 1", output_text)
            self.assertIn("[Response]", output_text)
            self.assertIn("Response 1", output_text)
            self.assertIn("[Question 2]", output_text)
            self.assertIn("Test query 2", output_text)
            self.assertIn("Response 2", output_text)

    def test_output_file_separator(self):
        """Test that output file includes separators."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            query_file.write_text("Query 1\nQuery 2")

            self.mock_client.query.reset_mock()
            self.mock_client.query.side_effect = ["Resp 1", "Resp 2"]

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # Check that separator exists (60 equals signs)
            self.assertIn("=" * 60, output_text)

    def test_default_output_location(self):
        """Test default output file is in same directory as input."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            query_file = subdir / "my_queries.txt"
            query_file.write_text("Query 1")

            self.mock_client.query.reset_mock()
            self.mock_client.query.return_value = "Response"

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            # Output should be in same directory with _responses suffix
            output_file = subdir / "my_queries_responses.txt"
            self.assertTrue(output_file.exists())

    def test_output_preserves_query_stem(self):
        """Test output filename is based on input filename."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "medical_questions.txt"
            query_file.write_text("Question 1")

            self.mock_client.query.reset_mock()
            self.mock_client.query.return_value = "Answer"

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            output_file = Path(tmpdir) / "medical_questions_responses.txt"
            self.assertTrue(output_file.exists())


class TestQueryExecution(unittest.TestCase):
    """Tests for query execution behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()

    def test_query_execution_order(self):
        """Test that queries are executed in order."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["First", "Second", "Third"]
            query_file.write_text("\n".join(queries))

            self.mock_client.query.reset_mock()
            call_order = []

            def track_calls(q):
                call_order.append(q)
                return f"Response to {q}"

            self.mock_client.query.side_effect = track_calls

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            # Verify execution order
            self.assertEqual(call_order, queries)

    def test_all_responses_saved(self):
        """Test that all responses are saved to output file."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["Q1", "Q2", "Q3"]
            query_file.write_text("\n".join(queries))

            self.mock_client.query.reset_mock()
            responses = ["Response 1", "Response 2", "Response 3"]
            self.mock_client.query.side_effect = responses

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # All responses should be in output
            for response in responses:
                self.assertIn(response, output_text)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and corner scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.query = Mock(return_value="Response")

    def test_query_with_newlines(self):
        """Test query containing newline characters."""
        from perplx_query import _query_single

        query = "What is\nmultiline\nquery?"

        captured_output = StringIO()
        sys.stdout = captured_output

        _query_single(self.mock_client, query)

        sys.stdout = sys.__stdout__

        self.mock_client.query.assert_called_with(query)

    def test_unicode_in_query(self):
        """Test query with unicode characters."""
        from perplx_query import _query_single

        query = "What is 你好世界 and مرحبا العالم?"
        self.mock_client.query.reset_mock()

        captured_output = StringIO()
        sys.stdout = captured_output

        _query_single(self.mock_client, query)

        sys.stdout = sys.__stdout__

        self.mock_client.query.assert_called_with(query)

    def test_file_with_unicode(self):
        """Test file containing unicode characters."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "unicode.txt"
            queries = ["¿Cómo está?", "你好吗?", "كيف حالك؟"]
            query_file.write_text("\n".join(queries), encoding='utf-8')

            self.mock_client.query.reset_mock()
            self.mock_client.query.side_effect = ["R1", "R2", "R3"]

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            self.assertEqual(self.mock_client.query.call_count, 3)

    def test_very_long_file(self):
        """Test file with many queries."""
        from perplx_query import _query_file

        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "large.txt"
            # Create 100 queries
            queries = [f"Query {i}" for i in range(100)]
            query_file.write_text("\n".join(queries))

            self.mock_client.query.reset_mock()
            self.mock_client.query.side_effect = [f"Response {i}" for i in range(100)]

            captured_output = StringIO()
            sys.stdout = captured_output

            _query_file(self.mock_client, str(query_file))

            sys.stdout = sys.__stdout__

            self.assertEqual(self.mock_client.query.call_count, 100)


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PERPLX_QUERY TESTS")
    print("=" * 70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestQuerySingle))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryFile))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputFile))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryExecution))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return len(result.failures) + len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
