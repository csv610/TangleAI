"""Tests for the disease_qa.py module."""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel

# Add tangle module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from disease_qa import (
    DiseaseResponse,
    ApiError,
    ask_disease_question,
    display_results,
    main
)
from config import ModelConfig, ModelInput


class TestDiseaseResponse:
    """Test the DiseaseResponse Pydantic model."""

    def test_disease_response_valid(self):
        """Test creating a valid DiseaseResponse."""
        response = DiseaseResponse(
            overview="Diabetes is a metabolic disorder",
            causes="High blood sugar levels",
            treatments="Insulin therapy",
            citations=["Source 1", "Source 2"]
        )
        assert response.overview == "Diabetes is a metabolic disorder"
        assert response.causes == "High blood sugar levels"
        assert response.treatments == "Insulin therapy"
        assert len(response.citations) == 2

    def test_disease_response_empty_citations(self):
        """Test DiseaseResponse with empty citations."""
        response = DiseaseResponse(
            overview="Overview",
            causes="Causes",
            treatments="Treatments"
        )
        assert response.citations == []

    def test_disease_response_missing_fields(self):
        """Test DiseaseResponse validation with missing required fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            DiseaseResponse(overview="Overview")


class TestApiError:
    """Test the ApiError exception."""

    def test_api_error_creation(self):
        """Test creating an ApiError."""
        error = ApiError("Test error message")
        assert str(error) == "Test error message"

    def test_api_error_is_exception(self):
        """Test that ApiError is an Exception."""
        error = ApiError("Test")
        assert isinstance(error, Exception)


class TestAskDiseaseQuestion:
    """Test the ask_disease_question function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()

    def test_ask_disease_question_success_json(self):
        """Test successful API response with JSON content."""
        response_data = {
            "overview": "Diabetes is a chronic disease",
            "causes": "Insulin resistance",
            "treatments": "Medication and diet",
            "citations": ["https://example.com/1"]
        }

        mock_response = MagicMock()
        mock_json = MagicMock()
        mock_json.model_dump.return_value = response_data
        mock_response.json = mock_json
        mock_response.text = None

        self.mock_client.generate_content.return_value = mock_response

        result = ask_disease_question("What is diabetes?", self.mock_client, "sonar-pro")

        assert result is not None
        assert result["overview"] == "Diabetes is a chronic disease"
        assert result["causes"] == "Insulin resistance"
        assert result["treatments"] == "Medication and diet"
        assert len(result["citations"]) == 1

    def test_ask_disease_question_no_json_response(self):
        """Test API response with no structured output."""
        mock_response = MagicMock()
        mock_response.json = None

        self.mock_client.generate_content.return_value = mock_response

        result = ask_disease_question("What is diabetes?", self.mock_client)

        assert result is None

    def test_ask_disease_question_api_error(self):
        """Test handling of API errors."""
        self.mock_client.generate_content.side_effect = Exception("API request failed")

        with pytest.raises(ApiError) as exc_info:
            ask_disease_question("What is diabetes?", self.mock_client)

        assert "Error querying Perplexity API" in str(exc_info.value)

    def test_ask_disease_question_model_parameter(self):
        """Test that model parameter is passed correctly."""
        mock_response = MagicMock()
        mock_json = MagicMock()
        mock_json.model_dump.return_value = {
            "overview": "Test",
            "causes": "Test",
            "treatments": "Test"
        }
        mock_response.json = mock_json
        mock_response.text = None

        self.mock_client.generate_content.return_value = mock_response

        ask_disease_question("What is diabetes?", self.mock_client, model="sonar")

        # Verify generate_content was called
        assert self.mock_client.generate_content.called

    def test_ask_disease_question_system_prompt(self):
        """Test that system prompt is set correctly."""
        mock_response = MagicMock()
        mock_json = MagicMock()
        mock_json.model_dump.return_value = {
            "overview": "Test",
            "causes": "Test",
            "treatments": "Test"
        }
        mock_response.json = mock_json
        mock_response.text = None

        self.mock_client.generate_content.return_value = mock_response

        ask_disease_question("What is diabetes?", self.mock_client)

        # Verify that generate_content was called with ModelInput
        call_args = self.mock_client.generate_content.call_args
        model_input = call_args[0][0]
        assert isinstance(model_input, ModelInput)
        assert "medical assistant" in model_input.system_prompt.lower()


class TestDisplayResults:
    """Test the display_results function."""

    def test_display_results_with_data(self, capsys):
        """Test displaying results with valid data."""
        data = {
            "overview": "Diabetes is a chronic disease",
            "causes": "Insulin resistance",
            "treatments": "Medication and diet",
            "citations": ["https://example.com/1", "https://example.com/2"]
        }

        display_results("What is diabetes?", data)

        captured = capsys.readouterr()
        assert "What is diabetes?" in captured.out
        assert "OVERVIEW" in captured.out
        assert "Diabetes is a chronic disease" in captured.out
        assert "CAUSES" in captured.out
        assert "Insulin resistance" in captured.out
        assert "TREATMENTS" in captured.out
        assert "Medication and diet" in captured.out
        assert "CITATIONS" in captured.out
        assert "https://example.com/1" in captured.out
        assert "https://example.com/2" in captured.out

    def test_display_results_empty_citations(self, capsys):
        """Test displaying results without citations."""
        data = {
            "overview": "Overview text",
            "causes": "Causes text",
            "treatments": "Treatments text",
            "citations": []
        }

        display_results("Test question", data)

        captured = capsys.readouterr()
        assert "CITATIONS: None provided" in captured.out

    def test_display_results_no_data(self, capsys):
        """Test displaying results with None data."""
        display_results("Test question", None)

        captured = capsys.readouterr()
        assert "No data received from API" in captured.out

    def test_display_results_missing_keys(self, capsys):
        """Test displaying results with missing keys."""
        data = {
            "overview": "Overview text"
        }

        display_results("Test question", data)

        captured = capsys.readouterr()
        assert "Overview text" in captured.out
        assert "N/A" in captured.out  # For missing keys

    def test_display_results_formatting(self, capsys):
        """Test that results are properly formatted."""
        data = {
            "overview": "Test overview",
            "causes": "Test causes",
            "treatments": "Test treatments",
            "citations": ["Citation 1"]
        }

        display_results("Question?", data)

        captured = capsys.readouterr()
        # Check for formatting elements
        assert "=" * 70 in captured.out
        assert "-" * 70 in captured.out
        assert "📋" in captured.out or "OVERVIEW" in captured.out
        assert "🔍" in captured.out or "CAUSES" in captured.out


class TestMain:
    """Test the main function."""

    @patch('disease_qa.PerplexityClient')
    @patch('disease_qa.ask_disease_question')
    @patch('disease_qa.display_results')
    def test_main_success(self, mock_display, mock_ask, mock_client_class, capsys):
        """Test main function with successful execution."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_result = {
            "overview": "Test",
            "causes": "Test",
            "treatments": "Test",
            "citations": []
        }
        mock_ask.return_value = mock_result

        with patch('sys.argv', ['disease_qa.py', 'What is diabetes?']):
            main()

        # Verify client was initialized
        mock_client_class.assert_called_once()

        # Verify ask_disease_question was called
        mock_ask.assert_called_once()
        call_args = mock_ask.call_args
        assert call_args[0][0] == "What is diabetes?"

        # Verify display_results was called
        mock_display.assert_called_once()

    @patch('disease_qa.PerplexityClient')
    @patch('disease_qa.ask_disease_question')
    def test_main_with_model_option(self, mock_ask, mock_client_class):
        """Test main function with custom model option."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_result = {
            "overview": "Test",
            "causes": "Test",
            "treatments": "Test",
            "citations": []
        }
        mock_ask.return_value = mock_result

        with patch('sys.argv', ['disease_qa.py', 'Test question', '-m', 'sonar-pro']):
            with patch('disease_qa.display_results'):
                main()

        # Verify model parameter was used
        call_args = mock_ask.call_args
        assert call_args[1]['model'] == 'sonar-pro'

    @patch('disease_qa.PerplexityClient')
    def test_main_api_error(self, mock_client_class, capsys):
        """Test main function with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with patch('disease_qa.ask_disease_question') as mock_ask:
            from disease_qa import ApiError
            mock_ask.side_effect = ApiError("API failed")

            with patch('sys.argv', ['disease_qa.py', 'Test question']):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "API Error" in captured.out

    @patch('disease_qa.PerplexityClient')
    @patch('disease_qa.ask_disease_question')
    def test_main_no_result(self, mock_ask, mock_client_class, capsys):
        """Test main function when API returns no result."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_ask.return_value = None

        with patch('sys.argv', ['disease_qa.py', 'Test question']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Failed to get a valid response" in captured.out

    @patch('disease_qa.PerplexityClient')
    def test_main_unexpected_error(self, mock_client_class, capsys):
        """Test main function with unexpected error."""
        mock_client_class.side_effect = Exception("Unexpected error")

        with patch('sys.argv', ['disease_qa.py', 'Test question']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out

    def test_main_keyboard_interrupt(self, capsys):
        """Test main function with keyboard interrupt."""
        with patch('disease_qa.PerplexityClient') as mock_client_class:
            mock_client_class.side_effect = KeyboardInterrupt()

            with patch('sys.argv', ['disease_qa.py', 'Test question']):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "cancelled by user" in captured.out or "Operation cancelled" in captured.out

    @patch('disease_qa.PerplexityClient')
    @patch('disease_qa.ask_disease_question')
    @patch('disease_qa.display_results')
    def test_main_help_option(self, mock_display, mock_ask, mock_client_class, capsys):
        """Test main function with --help option."""
        with patch('sys.argv', ['disease_qa.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # argparse exits with code 0 for help
            assert exc_info.value.code == 0


class TestIntegration:
    """Integration tests for disease_qa module."""

    @patch('disease_qa.PerplexityClient')
    def test_full_workflow(self, mock_client_class, capsys):
        """Test full workflow from question to displayed results."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response_data = {
            "overview": "Asthma is a respiratory condition",
            "causes": "Allergies, exercise, cold air",
            "treatments": "Inhalers, corticosteroids",
            "citations": ["https://medical.example.com"]
        }

        mock_response = MagicMock()
        mock_json = MagicMock()
        mock_json.model_dump.return_value = response_data
        mock_response.json = mock_json
        mock_response.text = None
        mock_client.generate_content.return_value = mock_response

        with patch('sys.argv', ['disease_qa.py', 'What causes asthma?']):
            main()

        captured = capsys.readouterr()
        assert "What causes asthma?" in captured.out
        assert "Asthma is a respiratory condition" in captured.out
        assert "Allergies, exercise, cold air" in captured.out
        assert "Inhalers, corticosteroids" in captured.out
        assert "https://medical.example.com" in captured.out
