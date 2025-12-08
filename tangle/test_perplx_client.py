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


class TestModelConfigParameters:
    """Test ModelConfig parameters and their effects on API calls."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                self.mock_perplexity_class = mock_perplexity
                self.mock_client_instance = MagicMock()
                mock_perplexity.return_value = self.mock_client_instance
                self.client = PerplexityClient()

    def test_model_parameter_sonar(self):
        """Test model parameter with sonar model."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(model="sonar")
        params = self.client._build_api_params(model_input, config)
        assert params["model"] == "sonar"

    def test_model_parameter_sonar_pro(self):
        """Test model parameter with sonar-pro model."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(model="sonar-pro")
        params = self.client._build_api_params(model_input, config)
        assert params["model"] == "sonar-pro"

    def test_max_tokens_various_values(self):
        """Test max_tokens parameter with various values."""
        model_input = ModelInput(user_prompt="Test")

        test_cases = [128, 512, 1024, 2048, 4096]
        for max_tokens in test_cases:
            config = ModelConfig(max_tokens=max_tokens)
            params = self.client._build_api_params(model_input, config)
            assert params["max_tokens"] == max_tokens

    def test_temperature_range(self):
        """Test temperature parameter across valid range [0.0, 2.0]."""
        model_input = ModelInput(user_prompt="Test")

        test_cases = [0.0, 0.1, 0.5, 0.7, 1.0, 1.5, 2.0]
        for temp in test_cases:
            config = ModelConfig(temperature=temp)
            params = self.client._build_api_params(model_input, config)
            assert params["temperature"] == temp

    def test_top_p_range(self):
        """Test top_p parameter across valid range [0.0, 1.0]."""
        model_input = ModelInput(user_prompt="Test")

        test_cases = [0.0, 0.1, 0.5, 0.9, 0.99, 1.0]
        for top_p in test_cases:
            config = ModelConfig(top_p=top_p)
            params = self.client._build_api_params(model_input, config)
            assert params["top_p"] == top_p

    def test_stream_parameter(self):
        """Test stream parameter (True/False)."""
        model_input = ModelInput(user_prompt="Test")

        config = ModelConfig(stream=True)
        params = self.client._build_api_params(model_input, config)
        assert params["stream"] is True

        config = ModelConfig(stream=False)
        params = self.client._build_api_params(model_input, config)
        assert params["stream"] is False

    def test_search_mode_web(self):
        """Test search_mode parameter with 'web' mode."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(search_mode="web")
        params = self.client._build_api_params(model_input, config)
        assert params["search_mode"] == "web"

    def test_search_mode_local(self):
        """Test search_mode parameter with 'local' mode."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(search_mode="local")
        params = self.client._build_api_params(model_input, config)
        assert params["search_mode"] == "local"

    def test_reasoning_effort_low(self):
        """Test reasoning_effort parameter with 'low' value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(reasoning_effort="low")
        params = self.client._build_api_params(model_input, config)
        assert params["reasoning_effort"] == "low"

    def test_reasoning_effort_medium(self):
        """Test reasoning_effort parameter with 'medium' value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(reasoning_effort="medium")
        params = self.client._build_api_params(model_input, config)
        assert params["reasoning_effort"] == "medium"

    def test_reasoning_effort_high(self):
        """Test reasoning_effort parameter with 'high' value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(reasoning_effort="high")
        params = self.client._build_api_params(model_input, config)
        assert params["reasoning_effort"] == "high"

    def test_return_images_true(self):
        """Test return_images parameter when True."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(return_images=True)
        params = self.client._build_api_params(model_input, config)
        assert params["return_images"] is True

    def test_return_images_false(self):
        """Test return_images parameter when False."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(return_images=False)
        params = self.client._build_api_params(model_input, config)
        # When False, it should not be included or explicitly set to False
        assert params.get("return_images", False) is False

    def test_return_related_questions_true(self):
        """Test return_related_questions parameter when True."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(return_related_questions=True)
        params = self.client._build_api_params(model_input, config)
        assert params["return_related_questions"] is True

    def test_return_related_questions_false(self):
        """Test return_related_questions parameter when False."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(return_related_questions=False)
        params = self.client._build_api_params(model_input, config)
        assert params.get("return_related_questions", False) is False

    def test_language_preference_english(self):
        """Test language_preference parameter with English."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(language_preference="en")
        params = self.client._build_api_params(model_input, config)
        assert params["search_language_filter"] == ["en"]

    def test_language_preference_spanish(self):
        """Test language_preference parameter with Spanish."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(language_preference="es")
        params = self.client._build_api_params(model_input, config)
        assert params["search_language_filter"] == ["es"]

    def test_language_preference_french(self):
        """Test language_preference parameter with French."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(language_preference="fr")
        params = self.client._build_api_params(model_input, config)
        assert params["search_language_filter"] == ["fr"]

    def test_top_k_zero(self):
        """Test top_k parameter with zero (disabled)."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(top_k=0)
        params = self.client._build_api_params(model_input, config)
        # When 0, should not be included
        assert "top_k" not in params or params.get("top_k") == 0

    def test_top_k_nonzero(self):
        """Test top_k parameter with non-zero value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(top_k=5)
        params = self.client._build_api_params(model_input, config)
        assert params["top_k"] == 5

    def test_presence_penalty_zero(self):
        """Test presence_penalty parameter with zero (disabled)."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(presence_penalty=0.0)
        params = self.client._build_api_params(model_input, config)
        # When 0.0, should not be included
        assert "presence_penalty" not in params or params.get("presence_penalty") == 0.0

    def test_presence_penalty_nonzero(self):
        """Test presence_penalty parameter with non-zero value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(presence_penalty=0.5)
        params = self.client._build_api_params(model_input, config)
        assert params["presence_penalty"] == 0.5

    def test_frequency_penalty_zero(self):
        """Test frequency_penalty parameter with zero (disabled)."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(frequency_penalty=0.0)
        params = self.client._build_api_params(model_input, config)
        # When 0.0, should not be included
        assert "frequency_penalty" not in params or params.get("frequency_penalty") == 0.0

    def test_frequency_penalty_nonzero(self):
        """Test frequency_penalty parameter with non-zero value."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(frequency_penalty=0.5)
        params = self.client._build_api_params(model_input, config)
        assert params["frequency_penalty"] == 0.5

    def test_disable_search_false(self):
        """Test disable_search parameter when False."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(disable_search=False)
        params = self.client._build_api_params(model_input, config)
        # Should not override search_mode when False
        assert params.get("search_mode") != "local"

    def test_disable_search_true(self):
        """Test disable_search parameter when True."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(disable_search=True)
        params = self.client._build_api_params(model_input, config)
        # Should set search_mode to "local"
        assert params["search_mode"] == "local"

    def test_all_parameters_combined(self):
        """Test all parameters set at once."""
        model_input = ModelInput(user_prompt="Test", system_prompt="You are helpful")
        config = ModelConfig(
            model="sonar-pro",
            max_tokens=2048,
            temperature=0.8,
            top_p=0.95,
            stream=True,
            search_mode="web",
            reasoning_effort="high",
            return_images=True,
            return_related_questions=True,
            language_preference="en",
            top_k=10,
            presence_penalty=0.1,
            frequency_penalty=0.2,
            disable_search=False
        )
        params = self.client._build_api_params(model_input, config)

        assert params["model"] == "sonar-pro"
        assert params["max_tokens"] == 2048
        assert params["temperature"] == 0.8
        assert params["top_p"] == 0.95
        assert params["stream"] is True
        assert params["search_mode"] == "web"
        assert params["reasoning_effort"] == "high"
        assert params["return_images"] is True
        assert params["return_related_questions"] is True
        assert params["search_language_filter"] == ["en"]
        assert params["top_k"] == 10
        assert params["presence_penalty"] == 0.1
        assert params["frequency_penalty"] == 0.2


class TestSearchFilterParameters:
    """Test SearchFilter parameters and their effects."""

    def test_allowed_domains_single(self):
        """Test allowed_domains with single domain."""
        from config import SearchFilter
        filter = SearchFilter(allowed_domains=["nasa.gov"])
        params = filter.to_model_config()
        assert params["search_domain_filter"] == ["nasa.gov"]

    def test_allowed_domains_multiple(self):
        """Test allowed_domains with multiple domains."""
        from config import SearchFilter
        filter = SearchFilter(allowed_domains=["nasa.gov", "wikipedia.org", "arxiv.org"])
        params = filter.to_model_config()
        assert params["search_domain_filter"] == ["nasa.gov", "wikipedia.org", "arxiv.org"]

    def test_allowed_domains_max_limit(self):
        """Test allowed_domains respects max limit of 20."""
        from config import SearchFilter
        domains = [f"domain{i}.com" for i in range(20)]
        filter = SearchFilter(allowed_domains=domains)
        params = filter.to_model_config()
        assert len(params["search_domain_filter"]) == 20

    def test_allowed_domains_exceeds_max(self):
        """Test allowed_domains raises error when exceeding max limit."""
        from config import SearchFilter
        domains = [f"domain{i}.com" for i in range(21)]
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(allowed_domains=domains)
        assert "Maximum 20 domains" in str(exc_info.value)

    def test_blocked_domains_single(self):
        """Test blocked_domains with single domain."""
        from config import SearchFilter
        filter = SearchFilter(blocked_domains=["reddit.com"])
        params = filter.to_model_config()
        assert params["search_domain_filter"] == ["-reddit.com"]

    def test_blocked_domains_multiple(self):
        """Test blocked_domains with multiple domains."""
        from config import SearchFilter
        filter = SearchFilter(blocked_domains=["reddit.com", "pinterest.com", "facebook.com"])
        params = filter.to_model_config()
        assert params["search_domain_filter"] == ["-reddit.com", "-pinterest.com", "-facebook.com"]

    def test_blocked_domains_minus_prefix(self):
        """Test blocked_domains automatically adds minus prefix."""
        from config import SearchFilter
        filter = SearchFilter(blocked_domains=["example.com"])
        params = filter.to_model_config()
        assert params["search_domain_filter"][0].startswith("-")

    def test_allowed_and_blocked_domains_conflict(self):
        """Test that using both allowed and blocked domains raises error."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(allowed_domains=["nasa.gov"], blocked_domains=["reddit.com"])
        assert "Cannot use both allowed_domains and blocked_domains" in str(exc_info.value)

    def test_recency_day(self):
        """Test recency filter with 'day'."""
        from config import SearchFilter
        filter = SearchFilter(recency="day")
        params = filter.to_model_config()
        assert params["search_recency_filter"] == "day"

    def test_recency_week(self):
        """Test recency filter with 'week'."""
        from config import SearchFilter
        filter = SearchFilter(recency="week")
        params = filter.to_model_config()
        assert params["search_recency_filter"] == "week"

    def test_recency_month(self):
        """Test recency filter with 'month'."""
        from config import SearchFilter
        filter = SearchFilter(recency="month")
        params = filter.to_model_config()
        assert params["search_recency_filter"] == "month"

    def test_recency_year(self):
        """Test recency filter with 'year'."""
        from config import SearchFilter
        filter = SearchFilter(recency="year")
        params = filter.to_model_config()
        assert params["search_recency_filter"] == "year"

    def test_recency_invalid_value(self):
        """Test recency filter with invalid value."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(recency="invalid")
        assert "recency must be one of" in str(exc_info.value)

    def test_published_after_date(self):
        """Test published_after date filter."""
        from config import SearchFilter
        filter = SearchFilter(published_after="3/1/2025")
        params = filter.to_model_config()
        assert params["search_after_date_filter"] == "3/1/2025"

    def test_published_before_date(self):
        """Test published_before date filter."""
        from config import SearchFilter
        filter = SearchFilter(published_before="12/31/2024")
        params = filter.to_model_config()
        assert params["search_before_date_filter"] == "12/31/2024"

    def test_updated_after_date(self):
        """Test updated_after date filter."""
        from config import SearchFilter
        filter = SearchFilter(updated_after="3/1/2025")
        params = filter.to_model_config()
        assert params["last_updated_after_filter"] == "3/1/2025"

    def test_updated_before_date(self):
        """Test updated_before date filter."""
        from config import SearchFilter
        filter = SearchFilter(updated_before="12/31/2024")
        params = filter.to_model_config()
        assert params["last_updated_before_filter"] == "12/31/2024"

    def test_recency_and_published_date_conflict(self):
        """Test that recency and published_after conflict raises error."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(recency="week", published_after="3/1/2025")
        assert "Cannot combine 'recency' with specific date filters" in str(exc_info.value)

    def test_recency_and_published_before_conflict(self):
        """Test that recency and published_before conflict raises error."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(recency="week", published_before="3/1/2025")
        assert "Cannot combine 'recency' with specific date filters" in str(exc_info.value)

    def test_recency_and_updated_after_conflict(self):
        """Test that recency and updated_after conflict raises error."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(recency="week", updated_after="3/1/2025")
        assert "Cannot combine 'recency' with specific date filters" in str(exc_info.value)

    def test_recency_and_updated_before_conflict(self):
        """Test that recency and updated_before conflict raises error."""
        from config import SearchFilter
        with pytest.raises(ValueError) as exc_info:
            SearchFilter(recency="week", updated_before="3/1/2025")
        assert "Cannot combine 'recency' with specific date filters" in str(exc_info.value)

    def test_search_filter_with_client(self):
        """Test SearchFilter integration with PerplexityClient."""
        from config import SearchFilter
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                client = PerplexityClient()

                model_input = ModelInput(user_prompt="Test")
                config = ModelConfig()
                filter = SearchFilter(allowed_domains=["nasa.gov"], recency="week")

                params = client._build_api_params(model_input, config, filter)

                assert params["search_domain_filter"] == ["nasa.gov"]
                assert params["search_recency_filter"] == "week"

    def test_search_filter_all_parameters(self):
        """Test SearchFilter with all parameters combined."""
        from config import SearchFilter
        filter = SearchFilter(
            allowed_domains=["nasa.gov", "arxiv.org"],
            recency="month"
        )
        params = filter.to_model_config()
        assert params["search_domain_filter"] == ["nasa.gov", "arxiv.org"]
        assert params["search_recency_filter"] == "month"


class TestModelInputParameters:
    """Test ModelInput parameters and their effects."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity"):
                self.client = PerplexityClient()

    def test_user_prompt_only(self):
        """Test ModelInput with only user_prompt."""
        model_input = ModelInput(user_prompt="Hello")
        assert model_input.user_prompt == "Hello"
        assert model_input.system_prompt is None
        assert model_input.image_path is None
        assert model_input.pdf_path is None
        assert model_input.response_model is None

    def test_system_prompt(self):
        """Test ModelInput with system_prompt."""
        model_input = ModelInput(
            user_prompt="Hello",
            system_prompt="You are helpful"
        )
        assert model_input.system_prompt == "You are helpful"

    def test_system_prompt_empty_normalized_to_none(self):
        """Test that empty system_prompt is normalized to None."""
        model_input = ModelInput(
            user_prompt="Hello",
            system_prompt=""
        )
        assert model_input.system_prompt is None

    def test_system_prompt_whitespace_normalized(self):
        """Test that whitespace-only system_prompt is normalized to None."""
        model_input = ModelInput(
            user_prompt="Hello",
            system_prompt="   "
        )
        assert model_input.system_prompt is None

    def test_user_prompt_empty_without_attachments_raises_error(self):
        """Test that empty user_prompt without image or PDF raises error."""
        with pytest.raises(ValueError) as exc_info:
            ModelInput(user_prompt="")
        assert "user_prompt cannot be empty" in str(exc_info.value)

    def test_user_prompt_whitespace_without_attachments_raises_error(self):
        """Test that whitespace-only user_prompt without image or PDF raises error."""
        with pytest.raises(ValueError) as exc_info:
            ModelInput(user_prompt="   ")
        assert "user_prompt cannot be empty" in str(exc_info.value)

    def test_user_prompt_empty_with_image_defaults(self):
        """Test that empty user_prompt with image gets default prompt."""
        model_input = ModelInput(
            user_prompt="",
            image_path="/path/to/image.png"
        )
        assert model_input.user_prompt == "Describe this image in detail"

    def test_user_prompt_empty_with_pdf_defaults(self):
        """Test that empty user_prompt with PDF gets default prompt."""
        model_input = ModelInput(
            user_prompt="",
            pdf_path="/path/to/file.pdf"
        )
        assert model_input.user_prompt == "Describe this image in detail"

    def test_response_model_valid(self):
        """Test ModelInput with valid Pydantic response_model."""
        model_input = ModelInput(
            user_prompt="Test",
            response_model=SampleModelResponse
        )
        assert model_input.response_model == SampleModelResponse

    def test_response_model_invalid_not_pydantic(self):
        """Test ModelInput with invalid non-Pydantic response_model."""
        class NotPydantic:
            pass

        with pytest.raises(ValueError) as exc_info:
            ModelInput(user_prompt="Test", response_model=NotPydantic)
        assert "response_model must be a Pydantic BaseModel class" in str(exc_info.value)

    def test_response_model_none(self):
        """Test ModelInput with response_model=None."""
        model_input = ModelInput(user_prompt="Test", response_model=None)
        assert model_input.response_model is None

    def test_image_path_provided(self):
        """Test ModelInput with image_path."""
        model_input = ModelInput(
            user_prompt="Analyze",
            image_path="/path/to/image.png"
        )
        assert model_input.image_path == "/path/to/image.png"

    def test_pdf_path_provided(self):
        """Test ModelInput with pdf_path."""
        model_input = ModelInput(
            user_prompt="Summarize",
            pdf_path="/path/to/file.pdf"
        )
        assert model_input.pdf_path == "/path/to/file.pdf"

    def test_image_and_pdf_combined(self):
        """Test ModelInput with both image and pdf."""
        model_input = ModelInput(
            user_prompt="Test",
            image_path="/path/to/image.png",
            pdf_path="/path/to/file.pdf"
        )
        assert model_input.image_path == "/path/to/image.png"
        assert model_input.pdf_path == "/path/to/file.pdf"

    def test_payload_messages_with_response_model(self):
        """Test that response_model affects payload construction."""
        model_input = ModelInput(
            user_prompt="Test",
            response_model=SampleModelResponse
        )
        config = ModelConfig()
        params = self.client._build_api_params(model_input, config)
        assert "response_format" in params
        assert params["response_format"]["type"] == "json_schema"


class TestParameterCombinations:
    """Test various parameter combinations to ensure parameters interact correctly."""

    def setup_method(self):
        """Set up test client before each test."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
            with patch("perplx_client.Perplexity") as mock_perplexity:
                self.mock_client_instance = MagicMock()
                mock_perplexity.return_value = self.mock_client_instance
                self.client = PerplexityClient()

    def test_high_temperature_with_streaming(self):
        """Test high temperature with streaming enabled."""
        model_input = ModelInput(user_prompt="Be creative")
        config = ModelConfig(temperature=1.5, stream=True)
        params = self.client._build_api_params(model_input, config)

        assert params["temperature"] == 1.5
        assert params["stream"] is True

    def test_low_temperature_with_reasoning(self):
        """Test low temperature with high reasoning effort."""
        model_input = ModelInput(user_prompt="Solve complex problem")
        config = ModelConfig(temperature=0.1, reasoning_effort="high")
        params = self.client._build_api_params(model_input, config)

        assert params["temperature"] == 0.1
        assert params["reasoning_effort"] == "high"

    def test_penalties_combined(self):
        """Test presence and frequency penalties together."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(presence_penalty=0.2, frequency_penalty=0.3)
        params = self.client._build_api_params(model_input, config)

        assert params["presence_penalty"] == 0.2
        assert params["frequency_penalty"] == 0.3

    def test_disable_search_overrides_search_mode(self):
        """Test that disable_search overrides explicit search_mode."""
        model_input = ModelInput(user_prompt="Test")
        config = ModelConfig(search_mode="web", disable_search=True)
        params = self.client._build_api_params(model_input, config)

        # disable_search=True should force search_mode to "local"
        assert params["search_mode"] == "local"

    def test_structured_output_with_all_features(self):
        """Test structured output combined with other parameters."""
        model_input = ModelInput(
            user_prompt="Extract data",
            response_model=SampleModelResponse
        )
        config = ModelConfig(
            temperature=0.5,
            stream=False,
            return_images=True,
            return_related_questions=True
        )
        params = self.client._build_api_params(model_input, config)

        assert "response_format" in params
        assert params["temperature"] == 0.5
        assert params["return_images"] is True
        assert params["return_related_questions"] is True

    def test_multiple_attachments_with_system_prompt(self):
        """Test multiple attachments with system and user prompts."""
        pdf_content = b"%PDF-1.4\nTest content"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_content)
            temp_pdf_path = f.name

        try:
            model_input = ModelInput(
                user_prompt="Analyze this PDF",
                system_prompt="Be thorough",
                pdf_path=temp_pdf_path
            )
            messages = self.client._payload_messages(model_input)

            assert len(messages) == 2  # system + user
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert len(messages[1]["content"]) == 2  # text + pdf
        finally:
            os.unlink(temp_pdf_path)

    def test_search_filter_with_all_config_params(self):
        """Test SearchFilter with all ModelConfig parameters."""
        from config import SearchFilter

        model_input = ModelInput(user_prompt="Research question")
        config = ModelConfig(
            model="sonar-pro",
            temperature=0.7,
            return_related_questions=True
        )
        search_filter = SearchFilter(
            allowed_domains=["arxiv.org", "scholar.google.com"],
            recency="month"
        )
        params = self.client._build_api_params(model_input, config, search_filter)

        assert params["model"] == "sonar-pro"
        assert params["temperature"] == 0.7
        assert params["return_related_questions"] is True
        assert params["search_domain_filter"] == ["arxiv.org", "scholar.google.com"]
        assert params["search_recency_filter"] == "month"


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
