#!/usr/bin/env python3
"""
Research Finder Command-Line Application using Perplexity API
Researches topics and displays results in the terminal
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Add tangle module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("research_finder.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("research_finder")


class ResearchResponse(BaseModel):
    """Structured response for research findings."""
    summary: str
    sources: list[str] = []


class ApiError(Exception):
    """Custom exception for API-related errors."""
    pass


def research_topic(query: str, client: PerplexityClient, model: str = "sonar-pro") -> Optional[Dict[str, Any]]:
    """
    Research a given topic or question using the Perplexity API.

    Args:
        query: The research question or topic.
        client: The PerplexityClient instance
        model: The model to use for the query (defaults to sonar-pro)

    Returns:
        Dictionary with summary and sources or None if an error occurs

    Raises:
        ApiError: If there's an issue with the API request
    """
    if not query or not query.strip():
        raise ApiError("Input query is empty. Cannot perform research.")

    system_prompt = "You are an AI research assistant. Your task is to research the user's query, provide a concise summary, and list the sources used."

    try:
        logger.info(f"Sending request to Perplexity API for query: '{query}'")

        model_input = ModelInput(
            user_prompt=query,
            system_prompt=system_prompt,
            response_model=ResearchResponse
        )

        config = ModelConfig(
            model=model,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            stream=False,
            search_mode="web"
        )

        response = client.generate_content(model_input, config)

        # Extract the response content
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            logger.info("Successfully received response from API")

            # Try to parse as JSON if structured output is returned
            try:
                parsed_data = json.loads(content) if isinstance(content, str) else content
                logger.info("Successfully parsed response")
                return parsed_data
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return the raw content
                logger.warning("Response is not structured JSON, returning as text")
                return {
                    "summary": content,
                    "sources": []
                }
        else:
            logger.error("No answer provided in the response.")
            return None

    except Exception as e:
        logger.error(f"Error querying API: {str(e)}")
        raise ApiError(f"Error querying Perplexity API: {str(e)}")


def display_results(query: str, data: Optional[Dict[str, Any]]) -> None:
    """
    Display the research results in a formatted terminal output.

    Args:
        query: The original query
        data: The parsed response data from the API
    """
    if not data:
        print("\n❌ No data received from API")
        return

    print("\n" + "=" * 70)
    print(f"Query: {query}")
    print("=" * 70)

    # Display Summary
    print("\n📝 SUMMARY:")
    print("-" * 70)
    print(data.get("summary", "N/A"))

    # Display Sources
    sources = data.get("sources", [])
    if sources:
        print("\n🔗 SOURCES:")
        print("-" * 70)
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")
    else:
        print("\n🔗 SOURCES: No sources were explicitly listed or extracted.")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for the command-line application."""
    parser = argparse.ArgumentParser(
        description="Research Finder Application - Research topics using Perplexity API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research_finder.py "What is machine learning?"
  python research_finder.py -m sonar "Latest developments in AI"
  python research_finder.py --model sonar-pro "How do solar panels work?"
        """
    )

    parser.add_argument(
        "query",
        help="The research question or topic to investigate"
    )

    parser.add_argument(
        "-m", "--model",
        default="sonar-pro",
        help="Model to use for the query (default: sonar-pro)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    try:
        # Initialize the Perplexity client
        client = PerplexityClient()
        logger.info("Perplexity client initialized successfully")

        # Query the API
        print(f"\n🔄 Researching: '{args.query}'")
        print("Please wait...\n")

        result = research_topic(args.query, client, model=args.model)

        # Display results
        if result:
            display_results(args.query, result)
        else:
            print("\n❌ Failed to get a valid response from the API")
            sys.exit(1)

    except ApiError as e:
        logger.error(f"API Error: {str(e)}")
        print(f"\n❌ API Error: {str(e)}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
