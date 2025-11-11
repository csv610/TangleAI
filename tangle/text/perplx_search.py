import os
import json
import time
import httpx
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from perplexity import Perplexity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from country_code import country_name_to_iso_code
from domain_search import DomainSearcher, DomainResult


@dataclass
class Config:
    """Configuration for Perplexity search client.

    Complete list of 30 parameters organized by category:

    ## 1. Search Result Control (2 params)
    - max_results: int = 10 | Maximum search results (1-20)
    - search_domain_filter: List[str] | None = None | Domain filtering (max 20 domains)

    ## 2. Image Processing (1 param)
    - max_token_per_image: int = 1024 | Maximum tokens per image

    ## 3. Geographic & Language (6 params)
    - iso_country_code: str = "US" | ISO 3166-1 alpha-2 country code
    - language_preference: str = "en" | Response language (en, es, fr, de, ja, ko)
    - user_location_latitude: float | None = None | User latitude for geographic refinement
    - user_location_longitude: float | None = None | User longitude for geographic refinement
    - user_location_region: str | None = None | User region/state for refinement
    - user_location_city: str | None = None | User city for refinement

    ## 4. Search Mode & Effort (2 params)
    - search_mode: str = "web" | web | academic | sec
    - reasoning_effort: str = "medium" | low | medium | high (sonar-deep-research only)

    ## 5. Result Options (3 params)
    - return_images: bool = False | Include images in results
    - return_videos: bool = False | Include videos in results
    - return_related_questions: bool = False | Include follow-up questions

    ## 6. Date Filtering (5 params)
    - search_recency_filter: str | None = None | day | week | month | year
    - search_after_date: str | None = None | MM/DD/YYYY format (publication date)
    - search_before_date: str | None = None | MM/DD/YYYY format (publication date)
    - last_updated_after: str | None = None | MM/DD/YYYY format (update date)
    - last_updated_before: str | None = None | MM/DD/YYYY format (update date)

    ## 7. Advanced Search Options (4 params)
    - search_context_size: str = "medium" | low | medium | high (retrieval scope)
    - image_search_relevance_enhanced: bool = False | Improve image result relevance
    - disable_search: bool = False | Disable web search (LLM-only)
    - enable_search_classifier: bool = False | Auto-detect if search is needed

    ## 8. LLM Response Control (7 params)
    - max_tokens: int | None = None | Maximum completion tokens
    - temperature: float = 0.2 | Randomness (0-2, lower = focused)
    - top_p: float = 0.9 | Nucleus sampling (0-1)
    - top_k: int = 0 | Top-k filtering (0 = disabled)
    - presence_penalty: float = 0.0 | Topic repetition penalty (0-2)
    - frequency_penalty: float = 0.0 | Word repetition penalty (0-2)
    - stream: bool = False | Enable streaming responses
    - response_format: str | None = None | JSON output formatting

    Note: The user_location_* parameters and search_context_size together form the
          web_search_options object in API requests. Use get_web_search_options()
          method to build the complete web_search_options object.
    """
    # Search Result Control
    max_results: int = 10
    search_domain_filter: Optional[List[str]] = None

    # Image Processing
    max_token_per_image: int = 1024

    # Geographic & Language
    iso_country_code: str = "US"
    language_preference: str = "en"
    user_location_latitude: Optional[float] = None
    user_location_longitude: Optional[float] = None
    user_location_region: Optional[str] = None
    user_location_city: Optional[str] = None

    # Search Mode & Effort
    search_mode: str = "web"
    reasoning_effort: str = "medium"

    # Result Options
    return_images: bool = False
    return_videos: bool = False
    return_related_questions: bool = False

    # Date Filtering
    search_recency_filter: Optional[str] = None
    search_after_date: Optional[str] = None
    search_before_date: Optional[str] = None
    last_updated_after: Optional[str] = None
    last_updated_before: Optional[str] = None

    # Advanced Search Options
    search_context_size: str = "medium"
    image_search_relevance_enhanced: bool = False
    disable_search: bool = False
    enable_search_classifier: bool = False

    # LLM Response Control
    max_tokens: Optional[int] = None
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stream: bool = False
    response_format: Optional[str] = None


    def set_search_params(self, max_results: int = None, domain_filter: List[str] = None,
                          search_mode: str = None, recency_filter: str = None) -> "Config":
        """Set common search parameters with a high-level method.

        Args:
            max_results: Maximum number of search results (1-20)
            domain_filter: List of domains to filter results (max 20)
            search_mode: Search mode: "web", "academic", or "sec"
            recency_filter: Recency filter: "day", "week", "month", "year"

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_search_params(
            ...     max_results=5,
            ...     search_mode="academic",
            ...     recency_filter="week"
            ... )
        """
        if max_results is not None:
            self.max_results = max_results
        if domain_filter is not None:
            self.search_domain_filter = domain_filter
        if search_mode is not None:
            self.search_mode = search_mode
        if recency_filter is not None:
            self.search_recency_filter = recency_filter
        return self

    def set_location_params(self, country: str = None, region: str = None,
                           city: str = None, latitude: float = None,
                           longitude: float = None) -> "Config":
        """Set geographic location parameters.

        Args:
            country: ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "DE")
            region: State/province/region name
            city: City name
            latitude: User latitude
            longitude: User longitude

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_location_params(
            ...     country="GB",
            ...     city="London",
            ...     region="England"
            ... )
        """
        if country is not None:
            self.iso_country_code = country
        if region is not None:
            self.user_location_region = region
        if city is not None:
            self.user_location_city = city
        if latitude is not None:
            self.user_location_latitude = latitude
        if longitude is not None:
            self.user_location_longitude = longitude
        return self

    def set_result_options(self, return_images: bool = None, return_videos: bool = None,
                          return_questions: bool = None) -> "Config":
        """Set result content options.

        Args:
            return_images: Include images in search results
            return_videos: Include videos in search results
            return_questions: Include related follow-up questions

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_result_options(
            ...     return_images=True,
            ...     return_videos=True,
            ...     return_questions=True
            ... )
        """
        if return_images is not None:
            self.return_images = return_images
        if return_videos is not None:
            self.return_videos = return_videos
        if return_questions is not None:
            self.return_related_questions = return_questions
        return self

    def set_date_filters(self, after_date: str = None, before_date: str = None,
                        updated_after: str = None, updated_before: str = None) -> "Config":
        """Set date-based filtering parameters.

        Args:
            after_date: Filter results published after this date (MM/DD/YYYY)
            before_date: Filter results published before this date (MM/DD/YYYY)
            updated_after: Filter results updated after this date (MM/DD/YYYY)
            updated_before: Filter results updated before this date (MM/DD/YYYY)

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_date_filters(
            ...     after_date="01/01/2024",
            ...     before_date="12/31/2024"
            ... )
        """
        if after_date is not None:
            self.search_after_date = after_date
        if before_date is not None:
            self.search_before_date = before_date
        if updated_after is not None:
            self.last_updated_after = updated_after
        if updated_before is not None:
            self.last_updated_before = updated_before
        return self

    def set_llm_params(self, temperature: float = None, top_p: float = None,
                      max_tokens: int = None, frequency_penalty: float = None,
                      presence_penalty: float = None) -> "Config":
        """Set LLM response control parameters.

        Args:
            temperature: Randomness control (0-2, default 0.2)
            top_p: Nucleus sampling threshold (0-1, default 0.9)
            max_tokens: Maximum completion tokens
            frequency_penalty: Penalty for repeated words (0-2)
            presence_penalty: Penalty for repeated topics (0-2)

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_llm_params(
            ...     temperature=0.5,
            ...     top_p=0.8,
            ...     max_tokens=2000
            ... )
        """
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if frequency_penalty is not None:
            self.frequency_penalty = frequency_penalty
        if presence_penalty is not None:
            self.presence_penalty = presence_penalty
        return self

    def set_search_control(self, disable_search: bool = None,
                          enable_classifier: bool = None,
                          context_size: str = None) -> "Config":
        """Set advanced search control parameters.

        Args:
            disable_search: Disable web search (use only LLM knowledge)
            enable_classifier: Enable automatic search detection
            context_size: Retrieval scope: "low", "medium", or "high"

        Returns:
            Config: Self for method chaining

        Example:
            >>> config = Config().set_search_control(
            ...     context_size="high",
            ...     enable_classifier=True
            ... )
        """
        if disable_search is not None:
            self.disable_search = disable_search
        if enable_classifier is not None:
            self.enable_search_classifier = enable_classifier
        if context_size is not None:
            self.search_context_size = context_size
        return self

    def get_web_search_options(self) -> dict:
        """Build web_search_options object for API requests.

        Returns a dictionary containing web_search_options configuration with:
        - search_context_size: Retrieval scope (low/medium/high)
        - user_location: Geographic refinement (if any location fields are set)
        - image_search_relevance_enhanced: Image relevance enhancement

        Returns:
            dict: web_search_options object ready for API requests
        """
        web_search_options = {
            "search_context_size": self.search_context_size,
            "image_search_relevance_enhanced": self.image_search_relevance_enhanced,
        }

        # Only include user_location if at least one location field is set
        if any([
            self.user_location_latitude,
            self.user_location_longitude,
            self.user_location_region,
            self.user_location_city,
            self.iso_country_code,
        ]):
            user_location = {}
            if self.user_location_latitude is not None:
                user_location["latitude"] = self.user_location_latitude
            if self.user_location_longitude is not None:
                user_location["longitude"] = self.user_location_longitude
            if self.iso_country_code:
                user_location["country"] = self.iso_country_code
            if self.user_location_region:
                user_location["region"] = self.user_location_region
            if self.user_location_city:
                user_location["city"] = self.user_location_city

            if user_location:
                web_search_options["user_location"] = user_location

        return web_search_options

    def set_domain_filter_by_query(self, query: str, count: int = 10,
                                   model: str = "sonar-pro") -> "Config":
        """Discover and set domain filter based on search query using domain search.

        Uses the domain search functionality to intelligently suggest authoritative
        domains relevant to the search query, then sets them as the domain filter.

        Args:
            query: The search query to discover domains for
            count: Number of domains to discover (1-20, default: 10)
            model: Perplexity model to use (default: sonar-pro)

        Returns:
            Config: Self for method chaining

        Raises:
            Exception: If domain discovery fails

        Example:
            >>> config = Config().set_domain_filter_by_query(
            ...     "quantum computing breakthroughs",
            ...     count=15
            ... )
        """
        try:
            searcher = DomainSearcher()
            result = searcher.get_domains_by_query(query, count=count, model=model)
            self.search_domain_filter = result.domains
            print(f"✓ Discovered {len(result.domains)} authoritative domains for: {query}")
            return self
        except Exception as e:
            raise Exception(f"Failed to discover domains: {str(e)}") from e

    def set_domain_filter_by_topic(self, topic: str, count: int = 10,
                                   model: str = "sonar-pro") -> "Config":
        """Discover and set domain filter based on topic using domain search.

        Similar to set_domain_filter_by_query but optimized for structured topics.

        Args:
            topic: The topic/subject to discover domains for
            count: Number of domains to discover (1-20, default: 10)
            model: Perplexity model to use (default: sonar-pro)

        Returns:
            Config: Self for method chaining

        Raises:
            Exception: If domain discovery fails

        Example:
            >>> config = Config().set_domain_filter_by_topic(
            ...     "artificial intelligence",
            ...     count=12
            ... )
        """
        try:
            searcher = DomainSearcher()
            result = searcher.get_domains_by_topic(topic, count=count, model=model)
            self.search_domain_filter = result.domains
            print(f"✓ Discovered {len(result.domains)} authoritative domains for topic: {topic}")
            return self
        except Exception as e:
            raise Exception(f"Failed to discover domains: {str(e)}") from e


# -------------------------------
# Perplexity Search Client
# -------------------------------
class PerplexitySearchClient:
    def __init__(self, config: Config):
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise EnvironmentError("❌ PERPLEXITY_API_KEY environment variable not set.")
        self.config = config
        self.client = Perplexity(
            api_key=api_key,
  #          max_retries=3,
  #          timeout=httpx.Timeout(30.0, read=10.0, write=5.0, connect=2.0)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def search(self, query: str):
        """Perform a single Perplexity search with retries."""
        # Build search parameters - only include valid parameters for search.create()
        # Valid parameters: query, max_results, search_domain_filter
        params = {
            "query": query,
            "max_results": self.config.max_results,
        }

        # Only add optional parameters if they're provided
        if self.config.search_domain_filter:
            params["search_domain_filter"] = self.config.search_domain_filter

        return self.client.search.create(**params)

    def batch_search(self, queries: List[str]):
        """Run multiple queries sequentially with delays for rate limiting."""
        all_results = []
        for i, q in enumerate(queries, start=1):
            print(f"🔍 [{i}/{len(queries)}] Searching for: {q}")
            try:
                result = self.search(q)
                formatted_results = []
                for r in result.results:
                    formatted_results.append({
                        "title": r.title,
                        "url": r.url,
                        "snippet": r.snippet,
                        "date": r.date,
                        "last_updated": r.last_updated,
                    })
                all_results.append({"query": q, "results": formatted_results})
            except Exception as e:
                print(f"❌ Error for '{q}': {e}")
                all_results.append({"query": q, "error": str(e)})
            time.sleep(1.5)  # polite delay between requests
        return all_results

    def save_results_json(self, responses, output_path: str):
        """Save all search results to a JSON file."""
        Path(output_path).write_text(
            json.dumps(responses, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\n✅ Results saved to {output_path}")

    def discover_domains(self, query: str, count: int = 10) -> DomainResult:
        """Discover authoritative domains for a given query.

        Uses the domain search functionality to find the top authoritative domains
        relevant to a search query.

        Args:
            query: The search query to discover domains for
            count: Number of domains to discover (1-20, default: 10)

        Returns:
            DomainResult: Object containing discovered domains and reasoning

        Raises:
            Exception: If domain discovery fails

        Example:
            >>> client = PerplexitySearchClient(config)
            >>> domains = client.discover_domains("quantum computing", count=15)
            >>> print(f"Found {len(domains.domains)} domains")
        """
        try:
            searcher = DomainSearcher()
            result = searcher.get_domains_by_query(query, count=count)
            print(f"🔍 Discovered {len(result.domains)} authoritative domains for: {query}")
            return result
        except Exception as e:
            raise Exception(f"Failed to discover domains: {str(e)}") from e


# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    # Example 1: Traditional search with manual domain filtering
    print("=" * 60)
    print("Example 1: Search with manual domain filter")
    print("=" * 60)
    config = Config(
        max_results=5,
        search_domain_filter=["nature.com", "science.org"]
    )
    client = PerplexitySearchClient(config)
    queries = [
        "How genetic engineering is shaping the biology",
        "How black holes are being detected"
    ]
    results = client.batch_search(queries)
    client.save_results_json(results, "perplx_search_results.json")

    # Example 2: Search with discovered domains
    print("\n" + "=" * 60)
    print("Example 2: Search with discovered domains")
    print("=" * 60)
    config2 = Config(max_results=5)
    client2 = PerplexitySearchClient(config2)

    # Discover domains first
    domain_result = client2.discover_domains(
        "quantum computing",
        count=10
    )

    # Update config with discovered domains
    client2.config.search_domain_filter = domain_result.domains

    # Now search with those domains
    search_result = client2.search("latest breakthroughs in quantum computing")
    print(f"✅ Found {len(search_result.results)} results from {len(domain_result.domains)} authoritative domains")

    # Example 3: Using Config helper methods with domain discovery
    print("\n" + "=" * 60)
    print("Example 3: Config with domain discovery helpers")
    print("=" * 60)
    config3 = Config(max_results=5).set_domain_filter_by_query(
        "machine learning applications",
        count=8
    )
    client3 = PerplexitySearchClient(config3)
    results3 = client3.search("machine learning in healthcare")
    print("✅ Search completed with discovered domains")
