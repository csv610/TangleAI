"""
Domain Search Module - Get top 20 domain names for a given query using LLM.

This module uses Perplexity LLM to intelligently suggest the top 20 domain names
relevant to a given search query or subject area. Includes quality filtering and
domain scoring for better results.
"""

import os
import json
import argparse
import logging
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

from perplexity import Perplexity
from shared_utils import error, search

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)



# Domains to exclude (low academic value)
EXCLUDED_DOMAINS = {
    "quora.com",
    "reddit.com",
    "pinterest.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "linkedin.com",
    "wordpress.com",
    "blogspot.com",
    "medium.com",  # Can be included but lower priority
    "dev.to",
    "substack.com",
}

# High-quality domain indicators (boosted priority)
# Use full domain names or TLDs with dots to avoid substring matching false positives
AUTHORITATIVE_INDICATORS = {
    "arxiv.org": 0.95,
    "nature.com": 0.95,
    "science.org": 0.95,
    "sciencemag.org": 0.95,
    "jstor.org": 0.95,
    "springer.com": 0.90,
    "sciencedirect.com": 0.90,
    "ieee.org": 0.90,
    "acm.org": 0.90,
    "cambridge.org": 0.90,
    "oup.com": 0.90,
    "wiley.com": 0.90,
    "ncbi.nlm.nih.gov": 0.95,
    "nih.gov": 0.90,
    "nasa.gov": 0.90,
    ".edu": 0.85,
    ".ac.": 0.85,
    ".gov": 0.85,  # Changed from "gov" to ".gov" to require TLD boundary
    ".org": 0.75,
}


@dataclass
class DomainResult:
    """Domain search result."""
    query: str
    domains: List[str]
    reasoning: str
    quality_scores: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "domains": self.domains,
            "reasoning": self.reasoning,
            "quality_scores": self.quality_scores,
        }

    def __str__(self) -> str:
        """Pretty print the result."""
        lines = [
            f"Query: {self.query}",
            f"Count: {len(self.domains)} domains",
            f"Reasoning: {self.reasoning}",
            "Domains:"
        ]
        lines.extend(f"  {i}. {domain}" for i, domain in enumerate(self.domains, 1))
        return "\n".join(lines)


class DomainSearcher:
    """Search for relevant domains using Perplexity LLM."""

    # Valid Perplexity models
    VALID_MODELS = {"sonar-pro", "sonar", "sonar-deep-research"}

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the DomainSearcher.

        Args:
            api_key: Perplexity API key. If not provided, uses PERPLEXITY_API_KEY env var.

        Raises:
            EnvironmentError: If API key is not found.
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "❌ PERPLEXITY_API_KEY environment variable not set."
            )

        self.client = Perplexity(api_key=self.api_key)

    def _search_domains(self, query: str, count: int, model: str, filter_quality: bool) -> DomainResult:
        """Internal method to search for domains using LLM.

        Args:
            query: The search query
            count: Number of domains to return
            model: Perplexity model to use (sonar-pro, sonar, sonar-deep-research)
            filter_quality: Filter and score domains by quality

        Returns:
            DomainResult: Object containing the top domains and reasoning

        Raises:
            ValueError: If count is invalid or query is empty
            Exception: If API call fails
        """
        if not 1 <= count <= 20:
            raise ValueError(f"Count must be between 1 and 20, got {count}")

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Validate model name
        if model not in self.VALID_MODELS:
            raise ValueError(
                f"Invalid model '{model}'. Must be one of: {', '.join(sorted(self.VALID_MODELS))}"
            )

        prompt = self._build_prompt(query, count)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            result_text = response.choices[0].message.content
            domains, reasoning = self._parse_response(result_text)
            initial_count = len(domains)

            # Filter and score domains
            if filter_quality:
                domains, scores = self._filter_and_score_domains(domains)
                # Log if domains were removed by filtering
                if len(domains) < initial_count:
                    logger.warning(
                        f"Filtered {initial_count - len(domains)}/{initial_count} domains "
                        f"({((initial_count-len(domains))/initial_count*100):.1f}% removed)"
                    )
            else:
                scores = [0.5] * len(domains)

            # Limit to requested count
            domains = domains[:count]
            scores = scores[:count]

            # Log if final count is less than requested
            if len(domains) < count:
                logger.warning(
                    f"Returning {len(domains)} domains instead of requested {count}"
                )

            return DomainResult(
                query=query,
                domains=domains,
                reasoning=reasoning,
                quality_scores=scores,
            )

        except Exception as e:
            raise Exception(
                f"Failed to search domains for '{query}': {str(e)}"
            ) from e

    def get_domains_by_query(self, query: str, count: int = 20, model: str = "sonar-pro",
                             filter_quality: bool = True) -> DomainResult:
        """Get top domain names relevant to the given query using LLM.

        Args:
            query: The search query (e.g., "quantum computing breakthroughs", "ancient history")
            count: Number of domains to return (default: 20, max: 20)
            model: Perplexity model to use (default: sonar-pro)
            filter_quality: Filter and score domains by quality (default: True)

        Returns:
            DomainResult: Object containing the top domains and reasoning

        Raises:
            ValueError: If count is invalid or query is empty
            Exception: If API call fails

        Examples:
            >>> searcher = DomainSearcher()
            >>> result = searcher.get_domains_by_query("quantum computing", count=15)
            >>> print(result)
        """
        return self._search_domains(query, count, model, filter_quality)

    def get_domains_by_topic(self, topic: str, count: int = 20, model: str = "sonar-pro",
                             filter_quality: bool = True) -> DomainResult:
        """Get top domain names for a specific topic using LLM.

        This method is optimized for structured topic-based queries where the
        LLM focuses on finding authoritative domains for well-defined subjects.

        Args:
            topic: The topic/subject name (e.g., "physics", "machine learning", "medieval history")
            count: Number of domains to return (default: 20, max: 20)
            model: Perplexity model to use (default: sonar-pro)
            filter_quality: Filter and score domains by quality (default: True)

        Returns:
            DomainResult: Object containing the top domains and reasoning

        Raises:
            ValueError: If count is invalid or topic is empty
            Exception: If API call fails

        Examples:
            >>> searcher = DomainSearcher()
            >>> result = searcher.get_domains_by_topic("artificial intelligence")
            >>> print(result)
        """
        return self.get_domains_by_query(topic, count, model, filter_quality)

    def save_results(self, results: List[DomainResult], output_path: str):
        """Save search results to a JSON file.

        Args:
            results: List of DomainResult objects
            output_path: Path to save the JSON file
        """
        data = [result.to_dict() for result in results]

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Results saved to {output_path}")

    @staticmethod
    def _filter_and_score_domains(domains: List[str]) -> Tuple[List[str], List[float]]:
        """Filter and score domains by authority level.

        Args:
            domains: List of domain names

        Returns:
            Tuple of (filtered_domains, quality_scores)
        """
        scored_domains = []

        for domain in domains:
            domain_lower = domain.lower()

            # Skip excluded domains
            if domain_lower in EXCLUDED_DOMAINS:
                continue

            # Calculate quality score based on authoritative indicators
            score = 0.5  # Base score
            for indicator, base_score in AUTHORITATIVE_INDICATORS.items():
                if indicator in domain_lower:
                    score = max(score, base_score)

            scored_domains.append((domain, score))

        # Sort by score (descending)
        scored_domains.sort(key=lambda x: -x[1])

        domains = [d[0] for d in scored_domains]
        scores = [d[1] for d in scored_domains]

        return domains, scores

    @staticmethod
    def _build_prompt(query: str, count: int) -> str:
        """Build the prompt for Claude LLM.

        Args:
            query: The search query
            count: Number of domains to return

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert in academic research and content discovery.

Given the search query or subject: "{query}"

Please identify the top {count} most relevant and authoritative domain names/websites for this topic.

Focus on:
1. Academic and research websites (universities, journals, repositories)
2. Specialized databases and resources for the subject
3. Official organizational websites
4. Leading publications and news sources in the field
5. Educational platforms and archives

Return the response in this exact format:
DOMAINS:
1. domain1.com
2. domain2.com
3. domain3.com
... and so on

REASONING:
Brief explanation of why these domains are relevant to the query.

Important:
- Only return domain names (no http://, www., or paths)
- One domain per line
- Include only the most authoritative and relevant domains
- Domains should be diverse in type (academic, news, reference, tools, etc.)
- Do not number the list differently or add extra formatting"""

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        """Validate domain format.

        Args:
            domain: Domain name to validate

        Returns:
            bool: True if domain is valid, False otherwise
        """
        if not domain or len(domain) < 5:  # Minimum: a.com
            return False

        # Check for invalid patterns
        if domain in {".", ""} or domain.count(".") < 1:
            return False

        # Split by dot
        parts = domain.split(".")
        if len(parts) < 2:
            return False

        # Check each part
        for part in parts:
            if not part:  # Empty part (e.g., "example..com")
                return False
            if not re.match(r'^[a-z0-9-]+$', part.lower()):  # Invalid characters
                return False
            if part.startswith("-") or part.endswith("-"):  # Hyphens at edges
                return False

        # Check TLD (last part) - must be at least 2 letters
        tld = parts[-1]
        if not re.match(r'^[a-z]{2,}$', tld.lower()):
            return False

        return True

    @staticmethod
    def _parse_response(response_text: str) -> Tuple[List[str], str]:
        """Parse the LLM response to extract domains and reasoning.

        Args:
            response_text: Raw response from Perplexity

        Returns:
            Tuple of (domains_list, reasoning_text)

        Raises:
            ValueError: If response format is invalid
        """
        lines = response_text.strip().split("\n")

        domains = []
        reasoning = ""
        in_domains_section = False
        in_reasoning_section = False

        for line in lines:
            line_stripped = line.strip()

            # Check for section markers
            if line_stripped.upper().startswith("DOMAINS"):
                in_domains_section = True
                in_reasoning_section = False
                continue

            if line_stripped.upper().startswith("REASONING"):
                in_domains_section = False
                in_reasoning_section = True
                continue

            if in_domains_section and line_stripped:
                # Remove leading numbers "1.", "2.", etc.
                domain = line_stripped
                if domain and domain[0].isdigit():
                    dot_pos = domain.find(".")
                    if dot_pos != -1:
                        domain = domain[dot_pos + 1:].strip()

                # Remove bullet points
                domain = domain.lstrip("- * •").strip()

                # Remove paths (keep only domain part)
                if "/" in domain:
                    domain = domain.split("/")[0]

                # Validate domain with strict validation
                if DomainSearcher._is_valid_domain(domain):
                    domains.append(domain)

            if in_reasoning_section and line_stripped:
                reasoning += line_stripped + " "

        if not domains:
            raise ValueError("No domains found in LLM response.")

        return domains, reasoning.strip()




def main():
    """CLI for domain search."""
    parser = argparse.ArgumentParser(
        description="Domain Search - Discover authoritative domains using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python domain_search.py "quantum computing"
    Find domains for a custom query
  python domain_search.py "AI" --count 10
    Get top 10 domains
  python domain_search.py "climate science" --output results.json
    Save to custom file
        """
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of domains to return (1-20, default: 20)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: domain_search_results.json)"
    )
    parser.add_argument(
        "--model",
        default="sonar-pro",
        help="Perplexity model to use (default: sonar-pro)"
    )

    args = parser.parse_args()

    # Require query
    if not args.query:
        parser.print_help()
        return

    try:
        searcher = DomainSearcher()
        search("Searching for domains...")
        result = searcher.get_domains_by_query(args.query, count=args.count, model=args.model)
        print(f"Discovered {len(result.domains)} domains for query: {args.query}\n")
        print(result)

        # Save results
        output_file = args.output or "domain_search_results.json"
        searcher.save_results([result], output_file)

    except ValueError as e:
        error(f"Error: {e}", exit_code=1)
    except Exception as e:
        error(f"Unexpected error: {e}", exit_code=1)

if __name__ == "__main__":
    main()
