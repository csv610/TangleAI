"""
Unit tests for perplx_query.py

Tests CLI argument parsing, single queries, batch queries, and file I/O.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Mock the PerplexityTextClient to avoid API calls
mock_client = Mock()
mock_client.query = Mock(return_value="Test response from Perplexity")

sys.modules['text_client'] = Mock(PerplexityTextClient=Mock(return_value=mock_client))

from perplx_query import _query_single, _query_file


class TestQuerySingle:
    """Tests for single query functionality."""

    def test_query_single_basic(self, capsys):
        """Test basic single query execution."""
        query = "What is Python?"
        _query_single(mock_client, query)

        # Verify client was called
        mock_client.query.assert_called_with(query)

        # Verify output contains the query
        captured = capsys.readouterr()
        assert "What is Python?" in captured.out

    def test_query_single_with_special_chars(self, capsys):
        """Test query with special characters."""
        query = "What are 'quotes' and \"double quotes\"?"
        mock_client.query.reset_mock()
        _query_single(mock_client, query)

        mock_client.query.assert_called_with(query)
        captured = capsys.readouterr()
        assert query in captured.out

    def test_query_single_long_query(self, capsys):
        """Test with long query."""
        query = "This is a very long query " * 10
        mock_client.query.reset_mock()
        _query_single(mock_client, query)

        mock_client.query.assert_called_once()
        captured = capsys.readouterr()
        assert "very long query" in captured.out


class TestQueryFile:
    """Tests for file-based query functionality."""

    def test_query_file_basic(self, capsys):
        """Test loading and querying from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with queries
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["What is AI?", "What is ML?", "What is DL?"]
            query_file.write_text("\n".join(queries))

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            # Verify all queries were executed
            assert mock_client.query.call_count == 3

            # Verify output file was created
            output_file = Path(tmpdir) / "queries_responses.txt"
            assert output_file.exists()

            # Verify output contains all queries
            output_text = output_file.read_text()
            for query in queries:
                assert query in output_text

    def test_query_file_with_empty_lines(self, capsys):
        """Test file with empty lines - should skip them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            content = """What is AI?

What is ML?

What is DL?
"""
            query_file.write_text(content)

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            # Should only process 3 queries (empty lines skipped)
            assert mock_client.query.call_count == 3

    def test_query_file_custom_output(self):
        """Test specifying custom output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["Query 1", "Query 2"]
            query_file.write_text("\n".join(queries))

            output_path = Path(tmpdir) / "custom_output.txt"

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file), str(output_path))

            # Verify custom output file was created
            assert output_path.exists()

            # Verify content is in custom file
            output_text = output_path.read_text()
            assert "Query 1" in output_text
            assert "Query 2" in output_text

    def test_query_file_not_found(self):
        """Test error when file not found."""
        with pytest.raises(FileNotFoundError):
            _query_file(mock_client, "/nonexistent/file.txt")

    def test_query_file_empty(self):
        """Test error when file has no queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "empty.txt"
            query_file.write_text("")  # Empty file

            with pytest.raises(ValueError, match="No queries found"):
                _query_file(mock_client, str(query_file))

    def test_query_file_only_whitespace(self):
        """Test file with only whitespace lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "whitespace.txt"
            query_file.write_text("\n   \n\t\n")  # Only whitespace

            with pytest.raises(ValueError, match="No queries found"):
                _query_file(mock_client, str(query_file))

    def test_query_file_multiple_spaces_between_queries(self, capsys):
        """Test file with multiple empty lines between queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            content = """Query 1


Query 2


Query 3"""
            query_file.write_text(content)

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            # Should process 3 queries
            assert mock_client.query.call_count == 3


class TestOutputFile:
    """Tests for output file generation."""

    def test_output_file_format(self):
        """Test that output file has correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            query_file.write_text("Test query 1\nTest query 2")

            mock_client.query.reset_mock()
            mock_client.query.side_effect = ["Response 1", "Response 2"]

            _query_file(mock_client, str(query_file))

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # Check format
            assert "[Question 1]" in output_text
            assert "Test query 1" in output_text
            assert "[Response]" in output_text
            assert "Response 1" in output_text
            assert "[Question 2]" in output_text
            assert "Test query 2" in output_text
            assert "Response 2" in output_text

    def test_output_file_separator(self):
        """Test that output file includes separators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            query_file.write_text("Query 1\nQuery 2")

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # Check that separator exists (60 equals signs)
            assert "=" * 60 in output_text

    def test_default_output_location(self):
        """Test default output file is in same directory as input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            query_file = subdir / "my_queries.txt"
            query_file.write_text("Query 1")

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            # Output should be in same directory with _responses suffix
            output_file = subdir / "my_queries_responses.txt"
            assert output_file.exists()

    def test_output_preserves_query_stem(self):
        """Test output filename is based on input filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "medical_questions.txt"
            query_file.write_text("Question 1")

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            output_file = Path(tmpdir) / "medical_questions_responses.txt"
            assert output_file.exists()


class TestQueryExecution:
    """Tests for query execution behavior."""

    def test_query_execution_order(self):
        """Test that queries are executed in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["First", "Second", "Third"]
            query_file.write_text("\n".join(queries))

            mock_client.query.reset_mock()
            call_order = []

            def track_calls(q):
                call_order.append(q)
                return f"Response to {q}"

            mock_client.query.side_effect = track_calls

            _query_file(mock_client, str(query_file))

            # Verify execution order
            assert call_order == queries

    def test_all_responses_saved(self):
        """Test that all responses are saved to output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "queries.txt"
            queries = ["Q1", "Q2", "Q3"]
            query_file.write_text("\n".join(queries))

            mock_client.query.reset_mock()
            responses = ["Response 1", "Response 2", "Response 3"]
            mock_client.query.side_effect = responses

            _query_file(mock_client, str(query_file))

            output_file = Path(tmpdir) / "queries_responses.txt"
            output_text = output_file.read_text()

            # All responses should be in output
            for response in responses:
                assert response in output_text


class TestCLIIntegration:
    """Tests for CLI integration."""

    def test_help_message(self):
        """Test that help message is available."""
        with patch('sys.argv', ['perplx_query.py', '-h']):
            from perplx_query import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            # -h should exit with code 0
            assert exc_info.value.code == 0

    def test_mutually_exclusive_args(self):
        """Test that -q and -f are mutually exclusive."""
        with patch('sys.argv', ['perplx_query.py', '-q', 'test', '-f', 'file.txt']):
            from perplx_query import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with error code
            assert exc_info.value.code != 0

    def test_missing_required_arg(self):
        """Test error when neither -q nor -f provided."""
        with patch('sys.argv', ['perplx_query.py']):
            from perplx_query import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with error code
            assert exc_info.value.code != 0


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_query_with_newlines(self, capsys):
        """Test query containing newline characters."""
        query = "What is\nmultiline\nquery?"
        _query_single(mock_client, query)

        mock_client.query.assert_called_with(query)

    def test_unicode_in_query(self, capsys):
        """Test query with unicode characters."""
        query = "What is 你好世界 and مرحبا العالم?"
        mock_client.query.reset_mock()
        _query_single(mock_client, query)

        mock_client.query.assert_called_with(query)

    def test_file_with_unicode(self):
        """Test file containing unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "unicode.txt"
            queries = ["¿Cómo está?", "你好吗?", "كيف حالك؟"]
            query_file.write_text("\n".join(queries), encoding='utf-8')

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            assert mock_client.query.call_count == 3

    def test_very_long_file(self):
        """Test file with many queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            query_file = Path(tmpdir) / "large.txt"
            # Create 100 queries
            queries = [f"Query {i}" for i in range(100)]
            query_file.write_text("\n".join(queries))

            mock_client.query.reset_mock()
            _query_file(mock_client, str(query_file))

            assert mock_client.query.call_count == 100


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PERPLX_QUERY TESTS")
    print("=" * 70)

    # Run pytest
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_tests()
