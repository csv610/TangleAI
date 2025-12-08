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
