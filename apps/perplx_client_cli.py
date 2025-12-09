"""
Perplexity AI CLI Tool
Query the Perplexity API with text and image inputs.
Supports text questions, image analysis, and multi-modal queries.
"""

import sys
import os
import argparse

# Add tangle directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tangle'))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput
from logging_utils import setup_logging

logger = setup_logging("perplx_client_cli.log")


class PerplexityCLI:
    """Command-line interface for Perplexity AI."""

    SUPPORTED_MODELS = ('sonar', 'sonar-pro', 'sonar-reasoning')

    def __init__(self):
        """Initialize the CLI tool."""
        self.client = None

    def query_text_only(self, query: str, config: ModelConfig) -> str:
        """
        Query Perplexity with text only.

        Args:
            query: Text query
            config: Model configuration

        Returns:
            Response text from the API
        """
        logger.info(f"Text query received: {query}")
        print(f"\n📝 Query: {query}\n")
        print("⏳ Processing text query...")

        model_input = ModelInput(
            user_prompt=query,
            system_prompt=None
        )

        logger.info("Sending text-only request to Perplexity API")
        response = self.client.generate_content(model_input, config)
        logger.info("Successfully received response from API")
        return response.text or ""

    def query_text_with_image(
        self,
        query: str,
        image_path: str,
        config: ModelConfig
    ) -> str:
        """
        Query Perplexity with text and image.

        Args:
            query: Text query about the image
            image_path: Path to the image file
            config: Model configuration

        Returns:
            Response text from the API
        """
        logger.info(f"Text+Image query received - Image: {image_path}, Query: {query}")
        print(f"\n🖼️  Image: {image_path}")
        print(f"📝 Query: {query}\n")
        print("⏳ Processing image and text query...")

        model_input = ModelInput(
            user_prompt=query,
            image_path=image_path,
            system_prompt=None
        )

        logger.info("Sending text+image request to Perplexity API")
        response = self.client.generate_content(model_input, config)
        logger.info("Successfully received response from API")
        return response.text or ""

    def query_image_only(self, image_path: str, config: ModelConfig) -> str:
        """
        Query Perplexity with image only (describe the image).

        Args:
            image_path: Path to the image file
            config: Model configuration

        Returns:
            Response text from the API
        """
        logger.info(f"Image-only query received: {image_path}")
        print(f"\n🖼️  Image: {image_path}")
        print("⏳ Analyzing image...\n")

        default_prompt = "Please describe this image in detail, including all relevant elements, text, objects, and any notable features."

        model_input = ModelInput(
            user_prompt=default_prompt,
            image_path=image_path,
            system_prompt=None
        )

        logger.info("Sending image-only request to Perplexity API")
        response = self.client.generate_content(model_input, config)
        logger.info("Successfully received response from API")
        return response.text or ""

    def format_response(self, response: str, save_file: str = None) -> None:
        """
        Format and display the response.

        Args:
            response: Response text from the API
            save_file: Optional file path to save the response
        """
        print("\n" + "=" * 80)
        print("RESPONSE")
        print("=" * 80)
        print(response)
        print("=" * 80 + "\n")

        if save_file:
            try:
                # If no directory specified, use outputs/responses/
                if not os.path.dirname(save_file):
                    output_dir = os.path.join(os.path.dirname(__file__), "outputs", "responses")
                    os.makedirs(output_dir, exist_ok=True)
                    save_file = os.path.join(output_dir, save_file)
                else:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(save_file), exist_ok=True)

                logger.info(f"Saving response to: {save_file}")
                with open(save_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                logger.info(f"Response successfully saved to: {save_file}")
                print(f"✓ Response saved to: {save_file}")
            except IOError as e:
                logger.error(f"Could not save response: {e}")
                print(f"⚠️  Could not save response: {e}")

    def run(self, args):
        """
        Main entry point for the CLI.

        Args:
            args: Parsed command-line arguments
        """
        try:
            # Initialize client
            logger.info("Initializing Perplexity client")
            self.client = PerplexityClient()

            # Build model configuration
            logger.info(f"Building model configuration - Model: {args.model}, Web search: {args.web_search}")
            config = ModelConfig(
                model=args.model,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                stream=False,
                search_mode="web" if args.web_search else "local",
                reasoning_effort=args.reasoning_effort,
                return_images=args.return_images,
                return_related_questions=args.return_related_questions,
                language_preference=args.language,
                disable_search=not args.web_search
            )

            # Determine query type and execute
            if args.image and args.query:
                # Text + Image query
                logger.info("Executing text+image query")
                response = self.query_text_with_image(
                    args.query,
                    args.image,
                    config
                )
            elif args.image:
                # Image only query
                logger.info("Executing image-only query")
                response = self.query_image_only(args.image, config)
            elif args.query:
                # Text only query
                logger.info("Executing text-only query")
                response = self.query_text_only(args.query, config)
            else:
                logger.error("No query or image provided")
                print("Error: Please provide either a query (-q) or an image (-i), or both")
                sys.exit(1)

            # Display and optionally save response
            self.format_response(response, args.output)
            logger.info("Query completed successfully")

        except FileNotFoundError as e:
            logger.error(f"File not found error: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            logger.error(f"Value error: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="perplx-cli",
        description="Query Perplexity AI with text and image inputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Text query
  python perplx_client_cli.py -q "What is machine learning?"

  # Image analysis
  python perplx_client_cli.py -i photo.jpg

  # Image with question
  python perplx_client_cli.py -i photo.jpg -q "What objects are in this image?"

  # Advanced text query with web search
  python perplx_client_cli.py -q "Latest AI developments 2025" --web-search

  # Save response to file
  python perplx_client_cli.py -q "Explain quantum computing" -o output.txt

  # Use different model with custom temperature
  python perplx_client_cli.py -q "Write a poem" -m sonar-pro -t 0.9
        """
    )

    # Core arguments
    parser.add_argument(
        '-q', '--query',
        type=str,
        help="Text query to send to Perplexity"
    )

    parser.add_argument(
        '-i', '--image',
        type=str,
        help="Path to image file (jpg, jpeg, png, gif, webp)"
    )

    # Model arguments
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='sonar',
        choices=PerplexityCLI.SUPPORTED_MODELS,
        help="Model to use (default: sonar)"
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=1024,
        help="Maximum tokens in response (default: 1024)"
    )

    # Generation parameters
    parser.add_argument(
        '-t', '--temperature',
        type=float,
        default=0.7,
        help="Temperature for response randomness (0.0-2.0, default: 0.7)"
    )

    parser.add_argument(
        '--top-p',
        type=float,
        default=0.9,
        help="Nucleus sampling parameter (default: 0.9)"
    )

    # Search options
    parser.add_argument(
        '--web-search',
        action='store_true',
        help="Enable web search (default: enabled)"
    )

    parser.add_argument(
        '--no-web-search',
        dest='web_search',
        action='store_false',
        help="Disable web search"
    )

    parser.set_defaults(web_search=True)

    # Advanced options
    parser.add_argument(
        '--reasoning-effort',
        type=str,
        default='medium',
        choices=['low', 'medium', 'high'],
        help="Reasoning effort level (default: medium)"
    )

    parser.add_argument(
        '--return-images',
        action='store_true',
        help="Request images in response (if available)"
    )

    parser.add_argument(
        '--faq',
        action='store_true',
        dest='return_related_questions',
        help="Request related questions in response"
    )

    parser.add_argument(
        '--language',
        type=str,
        default='en',
        help="Response language code (default: en)"
    )

    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="Save response to file"
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    cli = PerplexityCLI()
    cli.run(args)


if __name__ == "__main__":
    main()
