"""
Simplified Perplexity AI Client - High-level API for common tasks.

Provides intuitive methods for reasoning, research, querying, and chatting.
No low-level configuration needed for typical use cases.
"""

import os
import logging
from typing import Optional, List, Dict
from enum import Enum

try:
    from perplexity import Perplexity
except ImportError:
    raise ImportError(
        "The 'perplexity' package is required. Install it with: pip install perplexity-ai"
    )


# ============================================================================
# ENUMS - Task and parameter types
# ============================================================================

class ReasoningEffort(Enum):
    """Reasoning effort levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResearchDepth(Enum):
    """Research depth levels."""
    BRIEF = "brief"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


# ============================================================================
# MAIN CLIENT
# ============================================================================

class PerplexityTextClient:
    """
    Simplified Perplexity AI Client for common tasks.

    Provides high-level methods for:
    - Simple queries
    - Step-by-step reasoning
    - Deep research with citations
    - Multi-turn conversations

    All methods automatically select the best model and parameters
    for the task at hand.
    """

    def __init__(self):
        """Initialize the Perplexity client."""
        self.logger = logging.getLogger(self.__class__.__name__)

        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError(
                "API key must be set as PERPLEXITY_API_KEY environment variable"
            )

        try:
            self.client = Perplexity(api_key=api_key)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Perplexity client: {e}")

    def query(self, prompt: str) -> str:
        """
        Execute a simple query and get a response.

        Args:
            prompt: The query/question

        Returns:
            The AI response
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        return self._call_api("sonar-pro", [{"role": "user", "content": prompt}])

    def reason(
        self,
        prompt: str,
        effort: Optional[ReasoningEffort] = None,
        use_pro: bool = True,
        step_by_step: bool = True
    ) -> str:
        """
        Get step-by-step reasoning about a question.

        Uses the reasoning model to provide detailed logical analysis
        with explicit reasoning steps.

        Args:
            prompt: The question to reason about
            effort: Reasoning effort level (default: MEDIUM)
            use_pro: Use pro model if True (default: True)
            step_by_step: Request explicit step-by-step reasoning (default: True)

        Returns:
            Detailed reasoning response
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        model = "sonar-reasoning-pro" if use_pro else "sonar-reasoning"
        effort_level = effort or ReasoningEffort.MEDIUM

        formatted_prompt = prompt
        if step_by_step:
            formatted_prompt = f"{prompt}\n\nPlease provide your reasoning step-by-step."

        messages = [{"role": "user", "content": formatted_prompt}]

        return self._call_api(
            model,
            messages,
            reasoning_effort=effort_level.value,
            max_tokens=4000
        )

    def research(
        self,
        topic: str,
        depth: Optional[ResearchDepth] = None,
        sources: Optional[List[str]] = None
    ) -> str:
        """
        Conduct deep research on a topic with web search.

        Uses the deep research model to investigate topics comprehensively
        with proper citations and source references.

        Args:
            topic: The topic to research
            depth: Research depth (default: STANDARD)
            sources: Optional list of sources to emphasize

        Returns:
            Comprehensive research response with citations
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")

        depth_level = depth or ResearchDepth.STANDARD

        # Map depth to token limits
        depth_tokens = {
            ResearchDepth.BRIEF: 1500,
            ResearchDepth.STANDARD: 2500,
            ResearchDepth.COMPREHENSIVE: 4000
        }
        max_tokens = depth_tokens.get(depth_level, 2500)

        prompt = f"Conduct a thorough research on: {topic}"
        if sources:
            source_list = ", ".join(sources)
            prompt += f"\n\nKey sources to address: {source_list}"

        messages = [{"role": "user", "content": prompt}]

        return self._call_api(
            "sonar-deep-research",
            messages,
            max_tokens=max_tokens,
            max_search_results=10
        )

    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        creative: bool = False
    ) -> str:
        """
        Have a conversation with support for history.

        Continues multi-turn conversations with context awareness.
        Set creative=True for more creative, varied responses.

        Args:
            message: The current message
            conversation_history: Previous messages in format [{"role": "user"/"assistant", "content": "..."}]
            creative: Use creative mode (higher temperature) if True

        Returns:
            The assistant's response
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        messages = conversation_history or []
        messages = messages + [{"role": "user", "content": message}]

        temperature = 0.7 if creative else 0.2

        return self._call_api(
            "sonar-pro",
            messages,
            temperature=temperature,
            max_tokens=2000
        )

    def _call_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        reasoning_effort: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_search_results: Optional[int] = None
    ) -> str:
        """
        Internal method to call the Perplexity API.

        Args:
            model: Model name
            messages: Messages list
            reasoning_effort: For reasoning models
            temperature: Randomness (0-2)
            max_tokens: Max response tokens
            max_search_results: Max search results to consider

        Returns:
            API response text
        """
        params = {
            "model": model,
            "messages": messages,
        }

        if reasoning_effort:
            params["reasoning_effort"] = reasoning_effort
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens:
            params["max_tokens"] = max_tokens
        if max_search_results:
            params["max_search_results"] = max_search_results

        try:
            self.logger.info(f"Calling {model}...")
            completion = self.client.chat.completions.create(**params)
            response = completion.choices[0].message.content
            self.logger.info("Response received successfully")
            return response

        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            raise


# ============================================================================
# SETUP UTILITIES
# ============================================================================

def setup_logging(level: str = "INFO", log_file: str = "app.log") -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file (default: app.log)
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = getattr(logging, level.upper())
    date_format = '%Y-%m-%d %H:%M:%S'

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
