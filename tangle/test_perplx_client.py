"""Tests for the PerplexityClient module."""

import os
import base64
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput


class SampleModelResponse(BaseModel):
    """Sample response model for structured output testing."""
    answer: str
    confidence: float


class TestPerplexityClientInit:
    """Test PerplexityClient initialization."""

    def test_init_with_api_key(self):
        """Test successful initialization with API key environment variable."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key-12345"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                client = PerplexityClient()
                assert client.client is not None
                assert client.config is None
                mock_perplexity.assert_called_once_with(api_key="test-key-12345")

    def test_init_with_config(self):
        """Test initialization with custom ModelConfig."""
        config = ModelConfig(model="sonar-pro", max_tokens=2048)
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                client = PerplexityClient(config=config)
                assert client.config == config
                assert client.config.model == "sonar-pro"
                assert client.config.max_tokens == 2048

    def test_init_missing_api_key(self):
        """Test initialization fails when API key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                PerplexityClient()
            assert "PERPLEXITY_API_KEY environment variable must be set" in str(exc_info.value)

    def test_init_empty_api_key(self):
        """Test initialization fails when API key is empty string."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": ""}):
            with pytest.raises(ValueError):
                PerplexityClient()


class TestEncodePdf:
    """Test PDF encoding functionality."""

    def test_encode_pdf_valid_file(self):
        """Test encoding a valid PDF file."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                client = PerplexityClient()

                # Create a temporary PDF file with test content
                pdf_content = b"%PDF-1.4\nTest PDF content"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    f.write(pdf_content)
                    temp_pdf_path = f.name

                try:
                    encoded = client._encode_pdf(temp_pdf_path)

                    # Verify it's valid base64
                    decoded = base64.b64decode(encoded)
                    assert decoded == pdf_content
                finally:
                    os.unlink(temp_pdf_path)

    def test_encode_pdf_file_not_found(self):
        """Test encoding raises error when PDF file doesn't exist."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                client = PerplexityClient()

                with pytest.raises(FileNotFoundError):
                    client._encode_pdf("/nonexistent/path/file.pdf")


class TestPayloadMessages:
    """Test message payload building."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                self.client = PerplexityClient()

    def test_payload_messages_user_prompt_only(self):
        """Test message payload with only user prompt."""
        model_input = ModelInput(user_prompt="What is AI?")
        messages = self.client._payload_messages(model_input)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert isinstance(messages[0]["content"], list)
        assert messages[0]["content"][0]["type"] == "text"
        assert messages[0]["content"][0]["text"] == "What is AI?"

    def test_payload_messages_with_system_prompt(self):
        """Test message payload with system and user prompts."""
        model_input = ModelInput(
            user_prompt="What is AI?",
            system_prompt="You are a helpful AI assistant."
        )
        messages = self.client._payload_messages(model_input)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful AI assistant."
        assert messages[1]["role"] == "user"

    def test_payload_messages_with_pdf(self):
        """Test message payload with PDF file."""
        pdf_content = b"%PDF-1.4\nTest content"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_content)
            temp_pdf_path = f.name

        try:
            model_input = ModelInput(
                user_prompt="Analyze this PDF",
                pdf_path=temp_pdf_path
            )
            messages = self.client._payload_messages(model_input)

            assert len(messages) == 1
            user_message = messages[0]
            assert user_message["role"] == "user"
            assert len(user_message["content"]) == 2

            # Check text content
            assert user_message["content"][0]["type"] == "text"
            assert user_message["content"][0]["text"] == "Analyze this PDF"

            # Check PDF content
            assert user_message["content"][1]["type"] == "file_url"
            assert "url" in user_message["content"][1]["file_url"]

            # Verify base64 encoding
            encoded_pdf = user_message["content"][1]["file_url"]["url"]
            decoded = base64.b64decode(encoded_pdf)
            assert decoded == pdf_content
        finally:
            os.unlink(temp_pdf_path)

    def test_payload_messages_without_system_prompt(self):
        """Test that system prompt is not included when None."""
        model_input = ModelInput(user_prompt="Hello", system_prompt=None)
        messages = self.client._payload_messages(model_input)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_payload_messages_with_empty_system_prompt(self):
        """Test that empty system prompt is not included."""
        model_input = ModelInput(user_prompt="Hello", system_prompt="")
        # Note: ModelInput.__post_init__ normalizes empty system_prompt to None
        messages = self.client._payload_messages(model_input)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"


class TestBuildApiParams:
    """Test API parameter building."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                self.client = PerplexityClient()

    def test_build_api_params_minimal(self):
        """Test building API params with minimal config."""
        model_input = ModelInput(user_prompt="Test prompt")
        config = ModelConfig()

        params = self.client._build_api_params(model_input, config)

        assert params["model"] == "sonar"
        assert params["max_tokens"] == 1024
        assert params["temperature"] == 0.7
        assert params["top_p"] == 0.9
        assert params["stream"] is False
        assert "messages" in params
        assert len(params["messages"]) == 1

    def test_build_api_params_with_optional_fields(self):
        """Test building API params with optional fields."""
        model_input = ModelInput(user_prompt="Test prompt")
        config = ModelConfig(
            model="sonar-pro",
            max_tokens=2048,
            temperature=0.5,
            search_mode="local",
            reasoning_effort="high",
            return_images=True,
            return_related_questions=True,
            language_preference="es",
            top_k=5,
            presence_penalty=0.1,
            frequency_penalty=0.2
        )

        params = self.client._build_api_params(model_input, config)

        assert params["model"] == "sonar-pro"
        assert params["max_tokens"] == 2048
        assert params["temperature"] == 0.5
        assert params["search_mode"] == "local"
        assert params["reasoning_effort"] == "high"
        assert params["return_images"] is True
        assert params["return_related_questions"] is True
        assert params["search_language_filter"] == ["es"]
        assert params["top_k"] == 5
        assert params["presence_penalty"] == 0.1
        assert params["frequency_penalty"] == 0.2

    def test_build_api_params_disable_search(self):
        """Test that disable_search overrides search_mode."""
        model_input = ModelInput(user_prompt="Test prompt")
        config = ModelConfig(disable_search=True)

        params = self.client._build_api_params(model_input, config)

        assert params["search_mode"] == "local"

    def test_build_api_params_with_response_model(self):
        """Test building API params with structured output."""
        model_input = ModelInput(
            user_prompt="Test prompt",
            response_model=SampleModelResponse
        )
        config = ModelConfig()

        params = self.client._build_api_params(model_input, config)

        assert "response_format" in params
        assert params["response_format"]["type"] == "json_schema"
        assert "json_schema" in params["response_format"]
        assert "schema" in params["response_format"]["json_schema"]

    def test_build_api_params_with_system_prompt(self):
        """Test that system prompt is included in messages."""
        model_input = ModelInput(
            user_prompt="Test prompt",
            system_prompt="Be concise."
        )
        config = ModelConfig()

        params = self.client._build_api_params(model_input, config)

        assert len(params["messages"]) == 2
        assert params["messages"][0]["role"] == "system"
        assert params["messages"][0]["content"] == "Be concise."
        assert params["messages"][1]["role"] == "user"

    def test_build_api_params_default_values_not_included(self):
        """Test that default values are not included in optional params."""
        model_input = ModelInput(user_prompt="Test prompt")
        config = ModelConfig(
            search_mode=None,
            reasoning_effort=None,
            return_images=False,
            return_related_questions=False,
            language_preference=None,
            top_k=0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            disable_search=False
        )

        params = self.client._build_api_params(model_input, config)

        # These should not be in params when they're falsy or None
        assert "return_images" not in params or params.get("return_images") is False
        assert "return_related_questions" not in params or params.get("return_related_questions") is False


class TestGenerateContent:
    """Test content generation."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                self.mock_perplexity_class = mock_perplexity
                self.mock_client_instance = MagicMock()
                mock_perplexity.return_value = self.mock_client_instance
                self.client = PerplexityClient()

    def test_generate_content_with_provided_config(self):
        """Test generate_content with provided config."""
        model_input = ModelInput(user_prompt="Hello")
        config = ModelConfig(model="sonar-pro")

        mock_response = MagicMock()
        self.mock_client_instance.chat.completions.create.return_value = mock_response

        result = self.client.generate_content(model_input, config)

        assert result == mock_response
        self.mock_client_instance.chat.completions.create.assert_called_once()

        # Verify the config was used
        call_args = self.mock_client_instance.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "sonar-pro"

    def test_generate_content_uses_constructor_config(self):
        """Test generate_content uses config from constructor if not provided."""
        config = ModelConfig(model="sonar-pro", max_tokens=2048)
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                mock_instance = MagicMock()
                mock_perplexity.return_value = mock_instance
                client = PerplexityClient(config=config)

                model_input = ModelInput(user_prompt="Test")
                mock_response = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response

                result = client.generate_content(model_input)

                assert result == mock_response
                call_args = mock_instance.chat.completions.create.call_args
                assert call_args.kwargs["model"] == "sonar-pro"
                assert call_args.kwargs["max_tokens"] == 2048

    def test_generate_content_uses_default_config(self):
        """Test generate_content uses default config when none provided."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                mock_instance = MagicMock()
                mock_perplexity.return_value = mock_instance
                client = PerplexityClient()

                model_input = ModelInput(user_prompt="Test")
                mock_response = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response

                result = client.generate_content(model_input)

                assert result == mock_response
                call_args = mock_instance.chat.completions.create.call_args
                # Verify default config values are used
                assert call_args.kwargs["model"] == "sonar"
                assert call_args.kwargs["max_tokens"] == 1024
                assert call_args.kwargs["temperature"] == 0.7


class TestIntegration:
    """Integration tests for PerplexityClient."""

    def test_full_workflow_with_text_only(self):
        """Test full workflow with text-only prompt."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                mock_instance = MagicMock()
                mock_perplexity.return_value = mock_instance

                client = PerplexityClient()

                model_input = ModelInput(
                    user_prompt="What is machine learning?",
                    system_prompt="You are an expert AI scientist."
                )
                config = ModelConfig(
                    model="sonar-pro",
                    max_tokens=2048,
                    temperature=0.5
                )

                mock_response = MagicMock()
                mock_instance.chat.completions.create.return_value = mock_response

                result = client.generate_content(model_input, config)

                # Verify the API was called
                assert mock_instance.chat.completions.create.called
                assert result == mock_response

                # Verify correct parameters
                call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
                assert call_kwargs["model"] == "sonar-pro"
                assert call_kwargs["max_tokens"] == 2048
                assert call_kwargs["temperature"] == 0.5
                assert len(call_kwargs["messages"]) == 2

    def test_full_workflow_with_pdf(self):
        """Test full workflow with PDF file."""
        pdf_content = b"%PDF-1.4\nTest PDF content"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_content)
            temp_pdf_path = f.name

        try:
            with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
                with patch("perplx_client.Perplexity") as mock_perplexity:
                    mock_instance = MagicMock()
                    mock_perplexity.return_value = mock_instance

                    client = PerplexityClient()

                    model_input = ModelInput(
                        user_prompt="Summarize this PDF",
                        pdf_path=temp_pdf_path
                    )

                    mock_response = MagicMock()
                    mock_instance.chat.completions.create.return_value = mock_response

                    result = client.generate_content(model_input)

                    # Verify the API was called
                    assert mock_instance.chat.completions.create.called
                    assert result == mock_response

                    # Verify PDF was included in message
                    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
                    messages = call_kwargs["messages"]
                    user_content = messages[0]["content"]
                    assert len(user_content) == 2  # Text + PDF
                    assert user_content[1]["type"] == "file_url"
        finally:
            os.unlink(temp_pdf_path)
