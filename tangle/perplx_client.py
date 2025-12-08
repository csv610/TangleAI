import os
import argparse
import base64
from pathlib import Path
from perplexity import Perplexity
from typing import Dict, Any, List, Optional
from config import ModelConfig, ModelInput, SearchFilter
from image_utils import ImageUtils


class PerplexityClient:
    """
    Client for interacting with the Perplexity API using the native SDK.

    This class wraps the Perplexity SDK to provide a clean interface for
    making chat completion requests with support for various model configurations.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize the Perplexity client.

        Args:
            config: Optional default ModelConfig for all requests. If not provided, uses sensible defaults.

        Raises:
            ValueError: If PERPLEXITY_API_KEY environment variable is not set.
        """
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable must be set")

        self.client = Perplexity(api_key=api_key)
        self.config = config

    def _encode_pdf(self, pdf_path: str) -> str:
        """Encode a PDF file into a base64 string.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Base64 encoded PDF string
        """
        with open(pdf_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    def _payload_messages(self, model_input: ModelInput) -> List[Dict[str, Any]]:
        """
        Build messages payload for the LLM from ModelInput.

        Args:
            model_input: ModelInput dataclass with user prompt and system prompt

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        messages = []
        if model_input.system_prompt:
            messages.append({"role": "system", "content": model_input.system_prompt})

        # Build user message content
        user_content = []
        user_content.append({"type": "text", "text": model_input.user_prompt})

        # Add image if provided
        if model_input.image_path:
            image_data_uri = ImageUtils.encode_to_base64(model_input.image_path)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_data_uri}
            })

        # Add PDF if provided
        if model_input.pdf_path:
            encoded_pdf = self._encode_pdf(model_input.pdf_path)
            user_content.append({
                "type": "file_url",
                "file_url": {"url": encoded_pdf}
            })

        messages.append({"role": "user", "content": user_content})
        return messages

    def _build_api_params(self, model_input: ModelInput, config: ModelConfig, search_filter: Optional[SearchFilter] = None) -> Dict[str, Any]:
        """
        Build API parameters from ModelInput and ModelConfig.

        Args:
            model_input: ModelInput dataclass with user prompt and input options
            config: ModelConfig dataclass with model parameters and hyperparameters
            search_filter: Optional SearchFilter for high-level search result filtering

        Returns:
            Dictionary of API parameters ready for the Perplexity API
        """
        # Build messages list from ModelInput
        messages = self._payload_messages(model_input)

        # Build base API call parameters
        api_params = {
            "model": config.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": config.stream,
        }

        # Add optional Perplexity-specific parameters if they have non-default values
        if config.search_mode:
            api_params["search_mode"] = config.search_mode
        if config.reasoning_effort:
            api_params["reasoning_effort"] = config.reasoning_effort
        if config.return_images:
            api_params["return_images"] = config.return_images
        if config.return_related_questions:
            api_params["return_related_questions"] = config.return_related_questions
        if config.language_preference:
            api_params["search_language_filter"] = [config.language_preference]
        if config.top_k:
            api_params["top_k"] = config.top_k
        if config.presence_penalty:
            api_params["presence_penalty"] = config.presence_penalty
        if config.frequency_penalty:
            api_params["frequency_penalty"] = config.frequency_penalty
        if config.disable_search:
            api_params["search_mode"] = "local" if config.disable_search else "web"

        # Add high-level search filters if provided
        if search_filter:
            search_filter_params = search_filter.to_model_config()
            api_params.update(search_filter_params)

        # Add structured output if response_model is provided
        if model_input.response_model is not None:
            api_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "schema": model_input.response_model.model_json_schema()
                }
            }

        return api_params

    def generate_content(self, model_input: ModelInput, config: Optional[ModelConfig] = None, search_filter: Optional[SearchFilter] = None) -> Dict[str, Any]:
        """
        Generate content using the Perplexity API.

        Args:
            model_input: ModelInput dataclass with user prompt and input options
            config: Optional ModelConfig dataclass with model parameters and hyperparameters.
                   If not provided, uses sensible defaults.
            search_filter: Optional SearchFilter for high-level search result filtering.
                          Provides an easy way to filter domains, dates, and recency.

        Returns:
            Complete API response object

        Example:
            >>> filter = SearchFilter(
            ...     allowed_domains=["nasa.gov", "wikipedia.org"],
            ...     recency="week"
            ... )
            >>> response = client.generate_content(model_input, search_filter=filter)
        """
        # Use provided config, fall back to constructor config, or create default one
        if config is None:
            config = self.config or ModelConfig()

        api_params = self._build_api_params(model_input, config, search_filter)
        response = self.client.chat.completions.create(**api_params)

        return response


def main():
    """Parse arguments and make API call."""
    parser = argparse.ArgumentParser(
        description="Query the Perplexity AI API with custom prompts"
    )
    parser.add_argument(
        "-q", "--user-prompt",
        required=True,
        help="The user's query or prompt"
    )
    parser.add_argument(
        "-s", "--system-prompt",
        default=None,
        help="Optional system prompt to set the assistant's behavior"
    )
    parser.add_argument(
        "-i", "--image",
        default=None,
        help="Path to an image file to include with the query (PNG, JPEG, GIF, WEBP)"
    )
    parser.add_argument(
        "-p", "--pdf",
        default=None,
        help="Path to a PDF file to include with the query"
    )
    parser.add_argument(
        "-m", "--model",
        default="sonar-pro",
        help="Model to use (default: sonar-pro)"
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.7,
        help="Temperature for response randomness (default: 0.7)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens in response (default: 1024)"
    )

    args = parser.parse_args()

    # Create config and input dataclasses
    config = ModelConfig(
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=0.9,
        stream=False,
        reasoning_effort="medium",
        top_k=0,
        presence_penalty=0.0,
        frequency_penalty=0.0,
        search_mode="web",
        return_images=False,
        return_related_questions=False,
        language_preference="en",
        disable_search=False
    )

    model_input = ModelInput(
        user_prompt=args.user_prompt,
        system_prompt=args.system_prompt,
        image_path=args.image,
        pdf_path=args.pdf
    )

    # Make the API call
    print("Calling Perplexity Chat Completions API...")
    client = PerplexityClient()
    response = client.generate_content(model_input, config)
    
    # Print complete response structure
    print("\n=== COMPLETE API RESPONSE ===")
    print(f"ID: {response.id}")
    print(f"Model: {response.model}")
    print(f"Object: {response.object}")
    print(f"Created: {response.created}")
    
    print("\nUsage:")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")
    if hasattr(response.usage, 'search_context_size'):
        print(f"  Search context size: {getattr(response.usage, 'search_context_size', 'N/A')}")
    if hasattr(response.usage, 'citation_tokens'):
        print(f"  Citation tokens: {getattr(response.usage, 'citation_tokens', 'N/A')}")
    if hasattr(response.usage, 'num_search_queries'):
        print(f"  Search queries: {getattr(response.usage, 'num_search_queries', 'N/A')}")
    
    print("\nChoices:")
    for i, choice in enumerate(response.choices):
        print(f"  Choice {i}:")
        print(f"    Finish reason: {choice.finish_reason}")
        print(f"    Content: {choice.message.content[:200]}...")
    
    if hasattr(response, 'search_results') and response.search_results:
        print("\nSearch Results:")
        for result in response.search_results[:3]:  # First 3
            print(f"  - {result.title}: {result.url}")
    
    print("\nFull assistant response:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
