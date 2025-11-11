import os
import sys
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any, List, Union
from enum import Enum

try:
    from perplexity import Perplexity
except ImportError:
    raise ImportError(
        "The 'perplexity' package is required. Install it with: pip install perplexity-ai"
    )

class PromptLength(Enum):
    """Enumeration for prompt length options."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    CONCISE = "concise"
    DETAILED = "detailed"


class PerplexityModel(Enum):
    """Enumeration for available Perplexity models."""
    SONAR = "sonar"
    SONAR_PRO = "sonar-pro"
    SONAR_REASONING = "sonar-reasoning"
    SONAR_REASONING_PRO = "sonar-reasoning-pro"
    SONAR_DEEP_RESEARCH = "sonar-deep-research"


@dataclass
class ModelConfig:
    """
    Configuration parameters for the language model API calls.
    
    Manages model selection and model-specific settings like temperature, 
    token limits, and other parameters that control the model's behavior.
    """
    model: Union[PerplexityModel, str] = PerplexityModel.SONAR
    temperature: Optional[float] = field(default=0.7)
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate model configuration parameters after initialization."""
        # Validate model parameter
        if isinstance(self.model, str):
            try:
                self.model = PerplexityModel(self.model)
            except ValueError:
                available = [m.value for m in PerplexityModel]
                raise ValueError(f"Invalid model '{self.model}'. Available: {available}")
        
        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        if self.top_p is not None and not (0.0 <= self.top_p <= 1.0):
            raise ValueError("Top-p must be between 0.0 and 1.0")
        
        if self.frequency_penalty is not None and not (-2.0 <= self.frequency_penalty <= 2.0):
            raise ValueError("Frequency penalty must be between -2.0 and 2.0")
        
        if self.presence_penalty is not None and not (-2.0 <= self.presence_penalty <= 2.0):
            raise ValueError("Presence penalty must be between -2.0 and 2.0")
        
        if self.stop_sequences is not None and len(self.stop_sequences) > 4:
            raise ValueError("Maximum of 4 stop sequences allowed")
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert configuration to API parameters dictionary."""
        params = {
            "model": self.model.value
        }
        
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.stop_sequences is not None:
            params["stop"] = self.stop_sequences
        
        return params


@dataclass
class PromptConfig:
    """
    Configuration parameters for language model prompts.
    
    Provides structured management of prompt settings including length,
    target audience, and persona.
    """
    length: PromptLength = PromptLength.MEDIUM
    audience: str = "general audience"
    persona: str = "You are a helpful assistant."


class BasePromptGenerator(ABC):
    """Abstract base class for prompt generators."""
    
    def __init__(self, config: PromptConfig):
        """Initialize with prompt configuration."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self, **kwargs) -> str:
        """Generate a prompt based on provided parameters."""
        pass
    
    def _format_base_prompt(self, content: str) -> str:
        """Add common formatting to all prompts."""
        return f"{self.config.persona}\n\n{content}"


class SimplePromptGenerator(BasePromptGenerator):
    """Generator for simple prompts."""
    
    def generate(self, user_question: str) -> str:
        """Generate a basic prompt with persona and user question."""
        if not user_question.strip():
            raise ValueError("User question cannot be empty")
        
        return self._format_base_prompt(user_question)


class ResearchPromptGenerator(BasePromptGenerator):
    """Generator for research-based prompts."""
    
    def generate(
        self, 
        topic: str, 
        sources: List[str], 
        tone: str = "professional",
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Generate a detailed research prompt."""
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        if not sources:
            raise ValueError("At least one source must be provided")
        
        source_list = ", ".join(sources)
        
        prompt_parts = [
            f"Your task is to provide a detailed analysis on: '{topic}'",
            f"Base your response on these key concepts/sources: {source_list}",
            f"Response length: {self.config.length.value}",
            f"Target audience: {self.config.audience}",
            f"Tone: {tone} and informative"
        ]
        
        if focus_areas:
            focus_list = ", ".join(focus_areas)
            prompt_parts.append(f"Pay special attention to: {focus_list}")
        
        content = "\n\n".join(prompt_parts)
        return self._format_base_prompt(content)


class CreativePromptGenerator(BasePromptGenerator):
    """Generator for creative writing prompts."""
    
    def generate(
        self, 
        theme: str, 
        characters: List[str], 
        setting: str, 
        genre: str = "story",
        constraints: Optional[List[str]] = None
    ) -> str:
        """Generate a creative writing prompt."""
        if not all([theme.strip(), characters, setting.strip()]):
            raise ValueError("Theme, characters, and setting are required")
        
        character_list = ", ".join(characters)
        
        prompt_parts = [
            f"Write a {genre} with the central theme: '{theme}'",
            f"Main characters: {character_list}",
            f"Setting: {setting}",
            f"Length: {self.config.length.value}",
            f"Target audience: {self.config.audience}"
        ]
        
        if constraints:
            constraint_list = "; ".join(constraints)
            prompt_parts.append(f"Additional constraints: {constraint_list}")
        
        prompt_parts.append("Be creative, engaging, and original.")
        
        content = "\n\n".join(prompt_parts)
        return self._format_base_prompt(content)


class PromptGeneratorFactory:
    """Factory for creating appropriate prompt generators."""
    
    _generators = {
        "simple": SimplePromptGenerator,
        "research": ResearchPromptGenerator,
        "creative": CreativePromptGenerator
    }
    
    @classmethod
    def create_generator(
        self, 
        prompt_type: Literal["simple", "research", "creative"], 
        config: PromptConfig
    ) -> BasePromptGenerator:
        """Create and return the appropriate generator instance."""
        if prompt_type not in self._generators:
            available = ", ".join(self._generators.keys())
            raise ValueError(f"Invalid prompt type '{prompt_type}'. Available: {available}")
        
        return self._generators[prompt_type](config)


class PerplexityClient:
    """
    Enhanced client for interacting with the Perplexity AI API.
    
    Features improved error handling, logging, and flexible prompt generation.
    """
    
    def __init__(
        self, 
        model_config: ModelConfig,
        generator: BasePromptGenerator,
    ):
        """
        Initialize the Perplexity client.
        
        Args:
            model_config: Model configuration parameters including model selection
            generator: Prompt generator instance for creating prompts
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.model_config = model_config
        self.generator = generator
        
        # Get API key from environment variable
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key must be provided as PPLX_API_KEY environment variable"
            )
        
        # Initialize Perplexity client
        try:
            self.client = Perplexity(api_key=self.api_key)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Perplexity client: {e}")
    
    def generate_text(
        self, 
        user_question: str
    ) -> str:
        """
        Generate and send a prompt to the API using the configured generator.
        
        Args:
            user_question: The question or prompt text to send to the model.
            
        Returns:
            AI response content or error message
        """
        try:
            # Generate prompt using the configured generator
            user_prompt = self.generator.generate(user_question=user_question)

            print("Prompt: ", user_prompt)
            
            self.logger.info(f"Sending request to model: {self.model_config.model.value}")
            self.logger.debug(f"Generated prompt: {user_prompt[:100]}...")
            
            # Prepare API parameters from model config
            api_params = self.model_config.to_api_params()
            api_params["messages"] = [{"role": "user", "content": user_prompt}]
            
            # Make API call
            completion = self.client.chat.completions.create(**api_params)
            
            response_content = completion.choices[0].message.content
            self.logger.info("Successfully received response from API")
            
            return response_content
            
        except ValueError as e:
            error_msg = f"Invalid parameters: {e}"
            self.logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"API request failed: {e}"
            self.logger.error(error_msg)
            return error_msg
    


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


# --- Example Usage ---
if __name__ == "__main__":
    # Setup logging
    setup_logging("INFO")
    
    try:
        # Enhanced configuration with separate model and prompt configs
        model_config = ModelConfig(
            model=PerplexityModel.SONAR,
            temperature=0.3,
            max_tokens=2000,
            top_p=0.9,
            frequency_penalty=0.1
        )
        
        prompt_config = PromptConfig(
            length=PromptLength.DETAILED,
            audience="Patient",
            persona="You are a Medical Professor in an Univseity."
        )
        
        # Initialize client with a specific generator
        client = PerplexityClient(
            model_config=model_config,
            generator=SimplePromptGenerator(prompt_config)
        )

        question = sys.argv[1]
        
        response = client.generate_text(question)

        print(f"Response: {response}\n")
        
    except Exception as e:
        print(f"Application error: {e}")

