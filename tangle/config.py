"""Configuration for available models and vision processing parameters."""

from dataclasses import dataclass, field
from typing import Optional, Type, Any, List
from pydantic import BaseModel

# Vision model defaults
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 2000
DEFAULT_PROMPT = "Describe this image in detail"

# Image processing
SUPPORTED_IMAGE_TYPES = ("jpg", "jpeg", "png", "gif", "webp")
IMAGE_MIME_TYPE = "image/jpeg"


@dataclass
class SearchFilter:
    """High-level search filtering interface for users.

    Domain filtering supports both broad domains (e.g., "nasa.gov") and
    granular URL patterns. Maximum 20 domains/URLs per filter.
    Note: Use allowlist (allowed_domains) OR denylist (blocked_domains),
    not both simultaneously.
    """

    # Domain filtering
    allowed_domains: Optional[list[str]] = None
    """Whitelist: Only search these domains/URLs (max 20).
    Examples: ["nasa.gov", "wikipedia.org", "https://arxiv.org/"]
    Important: Test URLs for accessibility before using in production."""

    blocked_domains: Optional[list[str]] = None
    """Blacklist: Exclude these domains/URLs (max 20).
    Domains: Use format "domain.com" (e.g., ["reddit.com", "pinterest.com"])
    URLs: Use full URL format (e.g., ["https://en.wikipedia.org/wiki/FIDE_rankings"])
    Note: The minus sign (-) prefix is added automatically during conversion."""

    # Time filtering - choose one approach
    recency: Optional[str] = None
    """Quick filtering: "day", "week", "month", or "year" (relative to today)"""

    published_after: Optional[str] = None
    """Filter by publication date - earliest date (format: m/d/Y, e.g., "3/1/2025")"""

    published_before: Optional[str] = None
    """Filter by publication date - latest date (format: m/d/Y, e.g., "3/1/2025")"""

    updated_after: Optional[str] = None
    """Filter by last update date - earliest date (format: m/d/Y, e.g., "3/1/2025")"""

    updated_before: Optional[str] = None
    """Filter by last update date - latest date (format: m/d/Y, e.g., "3/1/2025")"""

    def __post_init__(self):
        """Validate filter configuration."""
        # Domain filtering validation
        if self.allowed_domains and self.blocked_domains:
            raise ValueError("Cannot use both allowed_domains and blocked_domains simultaneously. Choose allowlist or denylist mode.")

        if self.allowed_domains and len(self.allowed_domains) > 20:
            raise ValueError(f"Maximum 20 domains/URLs allowed in allowed_domains, got {len(self.allowed_domains)}")

        if self.blocked_domains and len(self.blocked_domains) > 20:
            raise ValueError(f"Maximum 20 domains/URLs allowed in blocked_domains, got {len(self.blocked_domains)}")

        # Date filtering validation
        if self.recency and (self.published_after or self.published_before or
                            self.updated_after or self.updated_before):
            raise ValueError("Cannot combine 'recency' with specific date filters. Choose one approach.")

        if self.recency and self.recency not in ("day", "week", "month", "year"):
            raise ValueError("recency must be one of: 'day', 'week', 'month', 'year'")

    def to_model_config(self) -> dict:
        """Convert to ModelConfig parameters.

        Automatically handles:
        - Converting blocked_domains to search_domain_filter with minus sign prefix
        - Keeping allowed_domains as-is in search_domain_filter
        """
        params = {}

        if self.allowed_domains:
            params["search_domain_filter"] = self.allowed_domains
        elif self.blocked_domains:
            # Add minus prefix for denylist mode
            params["search_domain_filter"] = [f"-{domain}" for domain in self.blocked_domains]

        if self.recency:
            params["search_recency_filter"] = self.recency
        if self.published_after:
            params["search_after_date_filter"] = self.published_after
        if self.published_before:
            params["search_before_date_filter"] = self.published_before
        if self.updated_after:
            params["last_updated_after_filter"] = self.updated_after
        if self.updated_before:
            params["last_updated_before_filter"] = self.updated_before

        return params


@dataclass
class ModelConfig:
    """Configuration for model interactions.

    Attributes:
        model: Model name (sonar, sonar-pro)
        temperature: Randomness/creativity (0.0-2.0), default 0.2
        top_p: Nucleus sampling (0.0-1.0), default 0.9
        top_k: Top-k sampling (0 disabled), default 0
        max_tokens: Maximum response length, default 8000
        frequency_penalty: Penalize frequent tokens, default 0.0
        presence_penalty: Penalize token repetition, default 0.0
        disable_search: Disable web search, default False
        search_mode: Type of search - 'web', 'academic', or 'sec', default 'web'
        language_preference: Language code (e.g., 'en', 'es', 'fr'), default 'en'
        reasoning_effort: Reasoning level - 'low', 'medium', or 'high', default 'medium'
        return_images: Include images in results, default False
        return_related_questions: Include related questions, default False
        return_citations: Include citations in results, default True
        stream: Stream responses, default False
    """

    model: str = "sonar"
    disable_search: bool = False
    frequency_penalty: float = 0.0
    language_preference: str = "en"
    max_tokens: int = 8000
    presence_penalty: float = 0.0
    reasoning_effort: str = "medium"
    return_images: bool = False
    return_related_questions: bool = False
    return_citations: bool = True
    search_mode: str = "web"
    stream: bool = False
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 0


@dataclass
class ChatConfig:
    """Configuration for chat session management."""

    max_history: int = 10
    auto_save: bool = False
    save_dir: str = "."


@dataclass
class ModelInput:
    """Input parameters for model interactions."""

    user_prompt: str = ""
    image_path: Optional[str] = None
    pdf_path: Optional[str] = None
    system_prompt: Optional[str] = None
    response_model: Optional[Type[BaseModel]] = None

    def __post_init__(self):
        """Validate input after initialization."""
        if not self.user_prompt or not self.user_prompt.strip():
            if not self.image_path and not self.pdf_path:
                raise ValueError("user_prompt cannot be empty unless an image_path or pdf_path is provided")
            self.user_prompt = DEFAULT_PROMPT

        # Normalize empty system_prompt to None
        if self.system_prompt is not None and not self.system_prompt.strip():
            self.system_prompt = None

        # Validate response_model is a Pydantic BaseModel
        if self.response_model is not None:
            try:
                if not (isinstance(self.response_model, type) and issubclass(self.response_model, BaseModel)):
                    raise ValueError("response_model must be a Pydantic BaseModel class")
            except TypeError:
                raise ValueError("response_model must be a Pydantic BaseModel class")


@dataclass
class ModelOutput:
    """Output from LLM model interactions.

    Either 'text' or 'json' will be populated depending on whether response_model was provided.
    If response_model was provided, 'json' contains the parsed model instance and 'text' may be None.
    If no response_model was provided, 'text' contains the response and 'json' will be None.
    """

    model: str
    """Model identifier used for the request."""

    finish_reason: str
    """Reason for finishing the response (e.g., 'stop', 'max_tokens')."""

    prompt_tokens: int
    """Number of tokens in the input prompt."""

    completion_tokens: int
    """Number of tokens in the completion."""

    total_tokens: int
    """Total number of tokens used."""

    text: Optional[str] = None
    """The main response text from the model (available when no response_model provided)."""

    json: Optional[BaseModel] = None
    """Parsed model instance if response_model was provided (available only when response_model provided)."""

    search_results: List[dict] = field(default_factory=list)
    """Search results returned by the API if available."""

    related_questions: List[str] = field(default_factory=list)
    """Related questions suggested by the model if available."""

    images: List[str] = field(default_factory=list)
    """Image URLs returned by the model if return_images was enabled."""

    search_context_size: Optional[int] = None
    """Size of search context window if available."""

    citation_tokens: Optional[int] = None
    """Number of citation tokens if available."""

    num_search_queries: Optional[int] = None
    """Number of search queries performed if available."""
