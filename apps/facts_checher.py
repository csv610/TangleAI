#!/usr/bin/env python3
"""
Fact Checker Application using Perplexity API
Checks claims and articles for factual accuracy with structured output
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field
from newspaper import Article, ArticleException

# Add tangle module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("facts_checker.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("facts_checker")


class Claim(BaseModel):
    """Model for representing a single claim and its fact check."""
    claim: str = Field(description="The specific claim extracted from the text")
    rating: str = Field(description="Rating of the claim: TRUE, FALSE, MISLEADING, or UNVERIFIABLE")
    explanation: str = Field(description="Detailed explanation with supporting evidence")
    sources: List[str] = Field(description="List of sources used to verify the claim")


class FactCheckResult(BaseModel):
    """Model for the complete fact check result."""
    overall_rating: str = Field(description="Overall rating: MOSTLY_TRUE, MIXED, or MOSTLY_FALSE")
    summary: str = Field(description="Brief summary of the overall findings")
    claims: List[Claim] = Field(description="List of specific claims and their fact checks")
    citations: List[str] = Field(default=[], description="List of sources and citations")


class ApiError(Exception):
    """Custom exception for API-related errors."""
    pass


def check_claim(text: str, client: PerplexityClient, model: str = "sonar-pro") -> Optional[Dict[str, Any]]:
    """
    Check the factual accuracy of a claim or article using Perplexity API.

    Args:
        text: The claim or article text to fact check
        client: The PerplexityClient instance
        model: The model to use for the query (defaults to sonar-pro)

    Returns:
        Dictionary with fact check results or None if an error occurs

    Raises:
        ApiError: If there's an issue with the API request
    """
    if not text or not text.strip():
        raise ApiError("Input text is empty. Cannot perform fact check.")

    system_prompt = """You are a professional fact-checker with extensive research capabilities. Your task is to evaluate claims or articles for factual accuracy. Analyze the text thoroughly and provide structured fact-check results with overall rating, summary, and detailed analysis of each claim. Focus on identifying false, misleading, or unsubstantiated claims. Provide citations for your findings."""

    try:
        logger.info("Preparing fact check request")

        model_input = ModelInput(
            user_prompt=f"Fact check the following text and identify any false or misleading claims:\n\n{text}",
            system_prompt=system_prompt,
            response_model=FactCheckResult
        )

        config = ModelConfig(
            model=model,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            stream=False,
            search_mode="web",
            reasoning_effort="medium"
        )

        logger.info(f"Sending request to Perplexity API for fact checking")
        response = client.generate_content(model_input, config)

        # Extract the response content
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            logger.info("Successfully received response from API")

            # Try to parse as JSON if structured output is returned
            try:
                parsed_data = json.loads(content) if isinstance(content, str) else content
                logger.info("Successfully parsed response as structured JSON")
                return parsed_data
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return the raw content
                logger.warning("Response is not structured JSON, returning as text")
                return {
                    "overall_rating": "MIXED",
                    "summary": content,
                    "claims": [],
                    "citations": []
                }
        else:
            logger.error("No answer provided in the response.")
            return None

    except Exception as e:
        logger.error(f"Error querying API: {str(e)}")
        raise ApiError(f"Error querying Perplexity API: {str(e)}")


def display_results(text: str, data: Optional[Dict[str, Any]], format_json: bool = False) -> None:
    """
    Display the fact checking results in a formatted terminal output.

    Args:
        text: The original text that was fact-checked
        data: The parsed response data from the API
        format_json: Whether to display results as JSON
    """
    if not data:
        print("\n❌ No data received from API")
        return

    if format_json:
        print(json.dumps(data, indent=2))
        return

    print("\n" + "=" * 70)
    print("FACT CHECK RESULTS")
    print("=" * 70)

    # Display Overall Rating
    overall_rating = data.get("overall_rating", "UNKNOWN")
    rating_emoji = "🟢" if overall_rating == "MOSTLY_TRUE" else "🟠" if overall_rating == "MIXED" else "🔴"
    print(f"\n{rating_emoji} OVERALL RATING: {overall_rating}")

    # Display Summary
    summary = data.get("summary", "N/A")
    if summary:
        print("\n📝 SUMMARY:")
        print("-" * 70)
        print(summary)

    # Display Claims Analysis
    claims = data.get("claims", [])
    if claims:
        print("\n🔍 CLAIMS ANALYSIS:")
        print("-" * 70)
        for i, claim in enumerate(claims, 1):
            rating = claim.get("rating", "UNKNOWN")
            if rating == "TRUE":
                rating_emoji = "✅"
            elif rating == "FALSE":
                rating_emoji = "❌"
            elif rating == "MISLEADING":
                rating_emoji = "⚠️"
            elif rating == "UNVERIFIABLE":
                rating_emoji = "❓"
            else:
                rating_emoji = "🔄"

            print(f"\nClaim {i}: {rating_emoji} {rating}")
            print(f"  Statement: \"{claim.get('claim', 'N/A')}\"")
            print(f"  Explanation: {claim.get('explanation', 'N/A')}")

            sources = claim.get("sources", [])
            if sources:
                print(f"  Sources:")
                for source in sources:
                    print(f"    - {source}")

    # Display Citations
    citations = data.get("citations", [])
    if citations:
        print("\n📚 CITATIONS:")
        print("-" * 70)
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {citation}")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for the fact checker CLI."""
    parser = argparse.ArgumentParser(
        description="Fact Checker Application - Identify false or misleading claims using Perplexity API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python facts_checher.py "The Earth is flat"
  python facts_checher.py -f article.txt
  python facts_checher.py -u https://example.com/article
  python facts_checher.py -m sonar-pro "Climate change is not real"
        """
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "text",
        nargs="?",
        help="Text to fact check"
    )
    input_group.add_argument(
        "-f", "--file",
        type=str,
        help="Path to file containing text to fact check"
    )
    input_group.add_argument(
        "-u", "--url",
        type=str,
        help="URL of the article to fact check"
    )

    parser.add_argument(
        "-m", "--model",
        default="sonar-pro",
        help="Model to use for the query (default: sonar-pro)"
    )

    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output results as JSON"
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

        # Get text from appropriate source
        text = None
        if args.file:
            try:
                logger.info(f"Reading text from file: {args.file}")
                with open(args.file, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                print(f"\n❌ Error reading file: {e}")
                sys.exit(1)
        elif args.url:
            try:
                logger.info(f"Fetching content from URL: {args.url}")
                print(f"\n🔄 Fetching content from URL: {args.url}")

                import requests
                response = requests.get(args.url, timeout=15)
                response.raise_for_status()

                article = Article(url=args.url)
                article.download(input_html=response.text)
                article.parse()
                text = article.text

                if not text:
                    logger.error(f"Could not extract text from URL: {args.url}")
                    print(f"\n❌ Error: Could not extract text from URL: {args.url}")
                    sys.exit(1)
                logger.info("Successfully extracted article text")
            except Exception as e:
                logger.error(f"Error processing URL: {e}")
                print(f"\n❌ Error processing URL: {e}")
                sys.exit(1)
        else:
            text = args.text

        if not text or not text.strip():
            logger.error("No text to fact check")
            print("\n❌ Error: No text found to fact check.")
            sys.exit(1)

        # Perform fact checking
        print(f"\n🔄 Fact checking in progress...")
        print("Please wait...\n")

        result = check_claim(text, client, model=args.model)

        # Display results
        if result:
            display_results(text, result, format_json=args.json)
        else:
            logger.error("Failed to get a valid response from the API")
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
