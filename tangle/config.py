"""Configuration for available models and vision processing parameters."""

from dataclasses import dataclass
from typing import Optional, Type, Any
from pydantic import BaseModel

# Vision model defaults
DEFAULT_TEMPERATURE = 0.7
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
    """Configuration for model interactions."""

    model: str = "sonar"
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False
    search_mode: str = "web"
    reasoning_effort: str = "medium"
    return_images: bool = False
    return_related_questions: bool = False
    language_preference: str = "en"
    top_k: int = 0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    disable_search: bool = False


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
