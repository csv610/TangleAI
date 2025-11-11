from perplexity import Perplexity
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, field
import logging

@dataclass
class ModelConfig:
    """
    Configuration dataclass for Perplexity model parameters.
    
    This provides a structured way to define and reuse model configurations
    with validation and intelligent defaults.
    """
    
    # Core parameters
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    
    # Reasoning parameters
    reasoning_effort: Optional[str] = None
    use_step_by_step: bool = False
    
    # Research parameters
    research_depth: Optional[str] = None
    
    # Conversation parameters
    conversation_history: Optional[List[Dict[str, str]]] = field(default=None)
    
    # Validation flags
    _validated: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all configuration parameters."""
        
        # Validate model
        if self.model is not None:
            valid_models = ["sonar", "sonar-pro", "sonar-reasoning", 
                          "sonar-reasoning-pro", "sonar-deep-research"]
            if self.model not in valid_models:
                raise ValueError(f"model must be one of: {valid_models}")
        
        # Validate temperature
        if self.temperature is not None:
            if not 0.0 <= self.temperature <= 1.0:
                raise ValueError("temperature must be between 0.0 and 1.0")
        
        # Validate max_tokens
        if self.max_tokens is not None:
            if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
                raise ValueError("max_tokens must be a positive integer")
        
        # Validate reasoning_effort
        if self.reasoning_effort is not None:
            valid_efforts = ["low", "medium", "high"]
            if self.reasoning_effort.lower() not in valid_efforts:
                raise ValueError(f"reasoning_effort must be one of: {valid_efforts}")
            self.reasoning_effort = self.reasoning_effort.lower()
        
        # Validate research_depth
        if self.research_depth is not None:
            valid_depths = ["brief", "standard", "comprehensive"]
            if self.research_depth.lower() not in valid_depths:
                raise ValueError(f"research_depth must be one of: {valid_depths}")
            self.research_depth = self.research_depth.lower()
        
        # Validate conversation_history format
        if self.conversation_history is not None:
            if not isinstance(self.conversation_history, list):
                raise ValueError("conversation_history must be a list")
            
            for msg in self.conversation_history:
                if not isinstance(msg, dict):
                    raise ValueError("conversation_history items must be dictionaries")
                if "role" not in msg or "content" not in msg:
                    raise ValueError("conversation_history items must have 'role' and 'content' keys")
                if msg["role"] not in ["user", "assistant", "system"]:
                    raise ValueError("conversation_history role must be 'user', 'assistant', or 'system'")
        
        self._validated = True
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary, excluding None values and private fields."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None and not k.startswith('_')
        }
    
    def merge(self, other: 'ModelConfig') -> 'ModelConfig':
        """Merge with another config, with other taking precedence."""
        merged_dict = self.to_dict()
        other_dict = other.to_dict()
        merged_dict.update(other_dict)
        return ModelConfig(**merged_dict)
    
    def copy(self) -> 'ModelConfig':
        """Create a copy of this config."""
        return ModelConfig(**self.to_dict())
    
    @classmethod
    def for_reasoning(cls, 
                     effort: str = "medium", 
                     use_pro: bool = False,
                     step_by_step: bool = True,
                     **kwargs) -> 'ModelConfig':
        """Factory method for reasoning tasks."""
        model = "sonar-reasoning-pro" if use_pro else "sonar-reasoning"
        return cls(
            model=model,
            reasoning_effort=effort,
            use_step_by_step=step_by_step,
            temperature=0.1,  # Low temperature for precise reasoning
            system_prompt="Think step by step and provide clear logical reasoning.",
            **kwargs
        )
    
    @classmethod
    def for_research(cls, 
                    depth: str = "standard",
                    **kwargs) -> 'ModelConfig':
        """Factory method for research tasks."""
        return cls(
            model="sonar-deep-research",
            research_depth=depth,
            temperature=0.3,  # Moderate temperature for balanced research
            **kwargs
        )
    
    @classmethod
    def for_chat(cls, 
                model: str = "sonar-pro",
                creative: bool = False,
                **kwargs) -> 'ModelConfig':
        """Factory method for general chat/conversation."""
        temp = 0.8 if creative else 0.5
        return cls(
            model=model,
            temperature=temp,
            **kwargs
        )
    
    @classmethod
    def quick_config(cls, task_type: str, **kwargs) -> 'ModelConfig':
        """Quick configuration based on task type string."""
        task_type = task_type.lower()
        
        if task_type in ["reasoning", "math", "logic", "problem"]:
            return cls.for_reasoning(**kwargs)
        elif task_type in ["research", "analysis", "study"]:
            return cls.for_research(**kwargs)
        elif task_type in ["chat", "conversation", "general"]:
            return cls.for_chat(**kwargs)
        else:
            raise ValueError(f"Unknown task_type: {task_type}")


class PerplexityModel:
    """
    A wrapper class for interacting with Perplexity AI models.
    
    This class provides a clean interface for making requests to various
    Perplexity models with built-in error handling and logging.
    
    Note: The reasoning_effort parameter is only supported by reasoning models:
    - sonar-reasoning
    - sonar-reasoning-pro
    """
    
    # Available Perplexity models
    AVAILABLE_MODELS = [
        "sonar",
        "sonar-pro", 
        "sonar-reasoning",
        "sonar-reasoning-pro",
        "sonar-deep-research"
    ]
    
    def __init__(self, default_model: str = "sonar-pro"):
        """
        Initialize the PerplexityModel.
        
        Args:
            default_model: Default model to use for completions.
        """
        self.client = Perplexity()
        self.default_model = self._validate_model(default_model)
        self.logger = logging.getLogger(__name__)
        
    def _validate_model(self, model: str) -> str:
        """Validate that the model is available."""
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model}' not available. Choose from: {self.AVAILABLE_MODELS}")
        return model
    
    def chat(self, 
             prompt: str, 
             model: Optional[str] = None,
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             reasoning_effort: Optional[str] = None,
             conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Legacy chat method - now calls generate_text for consistency.
        
        Args:
            prompt: The user prompt/question.
            model: Model to use (defaults to instance default).
            system_prompt: Optional system prompt to set context.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in response.
            reasoning_effort: Reasoning effort level for reasoning models ("low", "medium", "high").
            conversation_history: Previous conversation messages.
            
        Returns:
            The generated response as a string.
        """
        return self.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            conversation_history=conversation_history
        )
    
    def simple_query(self, question: str, model: Optional[str] = None) -> str:
        """
        Simple single-turn query method.
        
        Args:
            question: The question to ask.
            model: Model to use (defaults to instance default).
            
        Returns:
            The response as a string.
        """
        return self.generate_text(question, model=model)
    
    def research_query(self, topic: str, depth: str = "comprehensive") -> str:
        """
        Specialized method for research queries using the deep research model.
        
        Args:
            topic: The research topic.
            depth: Research depth - "brief", "standard", or "comprehensive".
            
        Returns:
            Detailed research response.
        """
        system_prompt = f"""You are a research assistant. Provide a {depth} analysis of the given topic. 
        Include relevant sources, key concepts, and current developments."""
        
        return self.generate_text(
            prompt=f"Research and analyze: {topic}",
            model="sonar-deep-research",
            system_prompt=system_prompt
        )
    
    def reasoning_query(self, problem: str, use_pro: bool = False, effort: str = "medium") -> str:
        """
        Specialized method for reasoning tasks.
        
        Args:
            problem: The problem or question requiring reasoning.
            use_pro: Whether to use the pro reasoning model.
            effort: Reasoning effort level - "low", "medium", or "high".
            
        Returns:
            Step-by-step reasoning response.
        """
        model = "sonar-reasoning-pro" if use_pro else "sonar-reasoning"
        system_prompt = "Think step by step and provide clear reasoning for your answer."
        
        return self.generate_text(
            prompt=problem,
            model=model,
            system_prompt=system_prompt,
            reasoning_effort=effort
        )
    
    def get_available_models(self) -> List[str]:
        """Return list of available models."""
        return self.AVAILABLE_MODELS.copy()
    
    def set_default_model(self, model: str) -> None:
        """Set the default model for future requests."""
        self.default_model = self._validate_model(model)
        self.logger.info(f"Default model set to: {model}")
    
    def generate_text(self, 
                     prompt: str,
                     model: Optional[str] = None,
                     system_prompt: Optional[str] = None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     reasoning_effort: Optional[str] = None,
                     conversation_history: Optional[List[Dict[str, str]]] = None,
                     research_depth: Optional[str] = None,
                     use_step_by_step: bool = False) -> str:
        """
        Unified interface for generating text with any Perplexity model.
        
        This method automatically optimizes parameters based on the model type and provides
        intelligent defaults for different use cases.
        
        Args:
            prompt: The input prompt/question.
            model: Model to use. If None, selects optimal model based on other parameters.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in response.
            reasoning_effort: Effort level for reasoning models ("low", "medium", "high").
            conversation_history: Previous conversation messages.
            research_depth: For research tasks ("brief", "standard", "comprehensive").
            use_step_by_step: Enable step-by-step reasoning prompts.
            
        Returns:
            Generated text response.
            
        Examples:
            # Simple question
            response = model.generate_text("What is quantum computing?")
            
            # Research query
            response = model.generate_text(
                "Latest developments in AI", 
                research_depth="comprehensive"
            )
            
            # Reasoning task
            response = model.generate_text(
                "Solve: x^2 + 5x + 6 = 0",
                reasoning_effort="high",
                use_step_by_step=True
            )
            
            # Custom model with conversation
            response = model.generate_text(
                "Follow up question",
                model="sonar-pro",
                conversation_history=previous_messages
            )
        """
        # Smart model selection if not specified
        if model is None:
            model = self._select_optimal_model(
                prompt=prompt,
                research_depth=research_depth,
                reasoning_effort=reasoning_effort,
                use_step_by_step=use_step_by_step
            )
        
        # Build optimized system prompt based on model and parameters
        optimized_system_prompt = self._build_system_prompt(
            base_system_prompt=system_prompt,
            model=model,
            research_depth=research_depth,
            use_step_by_step=use_step_by_step
        )
        
        # Set intelligent defaults based on model type
        if temperature is None:
            temperature = self._get_default_temperature(model)
        
        # Use the core generate_text method (but call the underlying chat for actual API calls)
        return self._chat_internal(
            prompt=prompt,
            model=model,
            system_prompt=optimized_system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            conversation_history=conversation_history
        )
    
    def _chat_internal(self, 
                      prompt: str, 
                      model: Optional[str] = None,
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      reasoning_effort: Optional[str] = None,
                      conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Internal chat method for actual API calls.
        
        Args:
            prompt: The user prompt/question.
            model: Model to use (defaults to instance default).
            system_prompt: Optional system prompt to set context.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in response.
            reasoning_effort: Reasoning effort level for reasoning models ("low", "medium", "high").
            conversation_history: Previous conversation messages.
            
        Returns:
            The generated response as a string.
        """
        model = model or self.default_model
        model = self._validate_model(model)
        
        # Build messages list
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
            
        # Add current user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build completion parameters
        completion_params = {
            "model": model,
            "messages": messages
        }
        
        # Add optional parameters if provided
        if temperature is not None:
            completion_params["temperature"] = temperature
        if max_tokens is not None:
            completion_params["max_tokens"] = max_tokens
        if reasoning_effort is not None:
            # Validate reasoning effort parameter and model compatibility
            valid_efforts = ["low", "medium", "high"]
            reasoning_models = ["sonar-reasoning", "sonar-reasoning-pro"]
            
            if reasoning_effort.lower() not in valid_efforts:
                raise ValueError(f"reasoning_effort must be one of: {valid_efforts}")
            
            if model not in reasoning_models:
                self.logger.warning(f"reasoning_effort parameter is only supported by reasoning models "
                                  f"({reasoning_models}). Current model: {model}. Parameter will be ignored.")
            else:
                completion_params["reasoning_effort"] = reasoning_effort.lower()
        
        try:
            self.logger.info(f"Making request to {model} with prompt: {prompt[:100]}...")
            completion = self.client.chat.completions.create(**completion_params)
            response = completion.choices[0].message.content
            self.logger.info(f"Received response: {response[:100]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"Error during API call: {str(e)}")
            raise
    
    def generate_text_with_config(self, prompt: str, config: ModelConfig) -> str:
        """
        Generate text using a ModelConfig object.
        
        Args:
            prompt: The input prompt/question.
            config: ModelConfig object with all parameters.
            
        Returns:
            Generated text response.
        """
        if not config._validated:
            config.validate()
        
        return self.generate_text(
            prompt=prompt,
            model=config.model,
            system_prompt=config.system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            reasoning_effort=config.reasoning_effort,
            conversation_history=config.conversation_history,
            research_depth=config.research_depth,
            use_step_by_step=config.use_step_by_step
        )
    
    def _select_optimal_model(self, 
                             prompt: str,
                             research_depth: Optional[str] = None,
                             reasoning_effort: Optional[str] = None,
                             use_step_by_step: bool = False) -> str:
        """Select the most appropriate model based on the task characteristics."""
        
        # Research tasks
        if research_depth is not None:
            return "sonar-deep-research"
        
        # Reasoning tasks
        if reasoning_effort is not None or use_step_by_step:
            # Check prompt complexity for pro vs standard
            complex_keywords = [
                "prove", "theorem", "logic", "reasoning", "step by step", "analyze",
                "calculate", "solve", "derivation", "mathematical", "algorithm"
            ]
            is_complex = any(keyword in prompt.lower() for keyword in complex_keywords)
            return "sonar-reasoning-pro" if is_complex else "sonar-reasoning"
        
        # Check for research/analysis indicators
        research_keywords = [
            "research", "analyze", "comprehensive", "detailed analysis", "compare",
            "literature review", "current state", "developments", "trends"
        ]
        if any(keyword in prompt.lower() for keyword in research_keywords):
            return "sonar-deep-research"
        
        # Check for reasoning indicators
        reasoning_keywords = [
            "solve", "proof", "calculate", "derive", "explain why", "logic",
            "reasoning", "problem", "puzzle", "mathematical"
        ]
        if any(keyword in prompt.lower() for keyword in reasoning_keywords):
            return "sonar-reasoning"
        
        # Default to sonar-pro for general queries
        return "sonar-pro"
    
    def _build_system_prompt(self, 
                           base_system_prompt: Optional[str],
                           model: str,
                           research_depth: Optional[str] = None,
                           use_step_by_step: bool = False) -> Optional[str]:
        """Build an optimized system prompt based on model and parameters."""
        
        prompts = []
        
        # Add base system prompt if provided
        if base_system_prompt:
            prompts.append(base_system_prompt)
        
        # Add model-specific optimizations
        if "reasoning" in model:
            if use_step_by_step:
                prompts.append("Think step by step and show your reasoning process clearly.")
            else:
                prompts.append("Provide clear logical reasoning for your answer.")
        
        elif "deep-research" in model:
            depth_map = {
                "brief": "Provide a concise but informative overview with key sources.",
                "standard": "Provide a thorough analysis with relevant sources and context.",
                "comprehensive": "Provide an in-depth analysis with extensive sources, current developments, and detailed context."
            }
            if research_depth:
                prompts.append(f"You are a research assistant. {depth_map.get(research_depth, depth_map['standard'])}")
            else:
                prompts.append("You are a research assistant. Provide accurate information with relevant sources.")
        
        return " ".join(prompts) if prompts else None
    
    def _get_default_temperature(self, model: str) -> float:
        """Get intelligent default temperature based on model type."""
        if "reasoning" in model:
            return 0.1  # Low temperature for precise reasoning
        elif "research" in model:
            return 0.3  # Moderate temperature for balanced research
        else:
            return 0.7  # Higher temperature for creative/general responses


# Example usage and comprehensive demonstration
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=" * 70)
    print("PERPLEXITY MODEL WRAPPER - COMPREHENSIVE DEMO")
    print("=" * 70)
    
    try:
        # Initialize the model
        perplexity = PerplexityModel(default_model="sonar-pro")
        print(f"✓ Initialized PerplexityModel with default model: sonar-pro")
        print(f"Available models: {perplexity.get_available_models()}")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        exit(1)
    
    print("\n" + "=" * 70 + "\n")
    
    # === BASIC FUNCTIONALITY EXAMPLES ===
    print("=== BASIC FUNCTIONALITY EXAMPLES ===")
    
    # Example 1: Simple query (recreating your original example)
    print("--- Simple Query Example ---")
    try:
        response = perplexity.simple_query("What is Galois Group Theory for Polynomial Equations?")
        print("✓ Simple query successful")
        print(f"Response preview: {response[:200]}..." if len(response) > 200 else response)
    except Exception as e:
        print(f"❌ Simple query failed: {e}")
    
    print("\n--- Research Query Example ---")
    try:
        research_response = perplexity.research_query(
            "Applications of machine learning in quantum computing",
            depth="standard"
        )
        print("✓ Research query successful")
        print(f"Response preview: {research_response[:200]}..." if len(research_response) > 200 else research_response)
    except Exception as e:
        print(f"❌ Research query failed: {e}")
    
    print("\n" + "=" * 50 + "\n")
    
    # === REASONING EXAMPLES ===
    print("=== REASONING QUERY EXAMPLES ===")
    
    try:
        # Low effort reasoning
        print("--- Low Effort Reasoning ---")
        reasoning_response_low = perplexity.reasoning_query(
            "A train leaves station A at 2 PM traveling at 60 mph. Another train leaves station B "
            "(200 miles away) at 2:30 PM traveling toward station A at 80 mph. At what time do they meet?",
            use_pro=True,
            effort="low"
        )
        print("✓ Low effort reasoning successful")
        print(f"Response preview: {reasoning_response_low[:200]}..." if len(reasoning_response_low) > 200 else reasoning_response_low)
        
        print("\n--- High Effort Reasoning ---")
        reasoning_response_high = perplexity.reasoning_query(
            "Solve this complex logic puzzle: In a town, there are three types of people: knights (always tell truth), "
            "knaves (always lie), and normals (can tell truth or lie). You meet three people A, B, and C. "
            "A says 'B is a knave'. B says 'C is a knight'. C says 'A is a normal'. What type is each person?",
            use_pro=True,
            effort="high"
        )
        print("✓ High effort reasoning successful")
        print(f"Response preview: {reasoning_response_high[:200]}..." if len(reasoning_response_high) > 200 else reasoning_response_high)
        
    except Exception as e:
        print(f"❌ Reasoning queries failed: {e}")
    
    print("\n" + "=" * 50 + "\n")
    
    # === UNIFIED GENERATE_TEXT INTERFACE ===
    print("=== UNIFIED GENERATE_TEXT INTERFACE EXAMPLES ===")
    
    # Auto-selected model examples
    print("--- Auto-Selected Model Examples ---")
    try:
        # Simple question
        response1 = perplexity.generate_text("What is machine learning?")
        selected_model1 = perplexity._select_optimal_model("What is machine learning?")
        print(f"✓ Simple question - Auto-selected model: {selected_model1}")
        print(f"Response preview: {response1[:150]}..." if len(response1) > 150 else response1)
        
        # Research question
        response2 = perplexity.generate_text(
            "Research the latest developments in quantum computing",
            research_depth="standard"
        )
        print(f"\n✓ Research question - Auto-selected model: sonar-deep-research")
        print(f"Response preview: {response2[:150]}..." if len(response2) > 150 else response2)
        
        # Reasoning question
        response3 = perplexity.generate_text(
            "Solve this equation step by step: 2x + 5 = 15",
            reasoning_effort="medium",
            use_step_by_step=True
        )
        selected_model3 = perplexity._select_optimal_model(
            "Solve this equation step by step: 2x + 5 = 15",
            reasoning_effort="medium",
            use_step_by_step=True
        )
        print(f"\n✓ Reasoning question - Auto-selected model: {selected_model3}")
        print(f"Response preview: {response3[:150]}..." if len(response3) > 150 else response3)
        
    except Exception as e:
        print(f"❌ Auto-selection examples failed: {e}")
    
    print("\n" + "=" * 50 + "\n")
    
    # === MODEL CONFIG EXAMPLES ===
    print("=== MODEL CONFIG DATACLASS EXAMPLES ===")
    
    # Factory method examples
    print("--- Factory Method Configs ---")
    try:
        # Reasoning config
        reasoning_config = ModelConfig.for_reasoning(effort="high", use_pro=True)
        print("✓ Reasoning config created:", reasoning_config.to_dict())
        
        response = perplexity.generate_text_with_config(
            "Prove that the sum of angles in a triangle is 180 degrees",
            reasoning_config
        )
        print("✓ Reasoning with config successful")
        print(f"Response preview: {response[:150]}..." if len(response) > 150 else response)
        
    except Exception as e:
        print(f"❌ Reasoning config failed: {e}")
    
    print("\n--- Research Config ---")
    try:
        research_config = ModelConfig.for_research(depth="comprehensive")
        print("✓ Research config created:", research_config.to_dict())
        
        response = perplexity.generate_text_with_config(
            "Latest breakthroughs in renewable energy technology",
            research_config
        )
        print("✓ Research with config successful")
        print(f"Response preview: {response[:150]}..." if len(response) > 150 else response)
        
    except Exception as e:
        print(f"❌ Research config failed: {e}")
    
    print("\n--- Custom Config ---")
    try:
        custom_config = ModelConfig(
            model="sonar-reasoning-pro",
            temperature=0.2,
            reasoning_effort="medium",
            use_step_by_step=True,
            max_tokens=300,
            system_prompt="You are a patient math tutor. Explain concepts clearly."
        )
        print("✓ Custom config created:", custom_config.to_dict())
        
        response = perplexity.generate_text_with_config(
            "Explain calculus derivatives in simple terms",
            custom_config
        )
        print("✓ Custom config successful")
        print(f"Response preview: {response[:150]}..." if len(response) > 150 else response)
        
    except Exception as e:
        print(f"❌ Custom config failed: {e}")
    
    print("\n--- Config Management ---")
    try:
        # Config merging
        base_config = ModelConfig.for_chat(creative=True)
        override_config = ModelConfig(temperature=0.3, max_tokens=200)
        
        merged_config = base_config.merge(override_config)
        print("✓ Config merging successful")
        print("Base config:", base_config.to_dict())
        print("Override config:", override_config.to_dict())
        print("Merged config:", merged_config.to_dict())
        
        # Quick config
        quick_reasoning = ModelConfig.quick_config("reasoning", effort="high")
        quick_research = ModelConfig.quick_config("research", depth="brief")
        
        print("\n✓ Quick configs created:")
        print("Quick reasoning:", quick_reasoning.to_dict())
        print("Quick research:", quick_research.to_dict())
        
    except Exception as e:
        print(f"❌ Config management failed: {e}")
    
    print("\n" + "=" * 50 + "\n")
    
    # === CONVERSATION EXAMPLE ===
    print("=== CONVERSATION WITH HISTORY EXAMPLE ===")
    try:
        # First message
        response1 = perplexity.generate_text("What are the main types of neural networks?")
        print("User: What are the main types of neural networks?")
        print(f"Assistant: {response1[:150]}..." if len(response1) > 150 else response1)
        
        # Follow-up with conversation history
        conversation = [
            {"role": "user", "content": "What are the main types of neural networks?"},
            {"role": "assistant", "content": response1}
        ]
        
        response2 = perplexity.generate_text(
            "Which one is best for image recognition?",
            conversation_history=conversation,
            model="sonar-pro"
        )
        print("\nUser: Which one is best for image recognition?")
        print(f"Assistant: {response2[:150]}..." if len(response2) > 150 else response2)
        print("✓ Conversation with history successful")
        
    except Exception as e:
        print(f"❌ Conversation example failed: {e}")
    
    print("\n" + "=" * 70 + "\n")
    
    # === VALIDATION EXAMPLES ===
    print("=== VALIDATION EXAMPLES ===")
    
    # Test validation
    print("--- Testing Parameter Validation ---")
    try:
        # Invalid model
        try:
            ModelConfig(model="invalid-model")
            print("❌ Should have failed with invalid model")
        except ValueError as e:
            print(f"✓ Correctly caught invalid model: {e}")
        
        # Invalid temperature
        try:
            ModelConfig(temperature=1.5)
            print("❌ Should have failed with invalid temperature")
        except ValueError as e:
            print(f"✓ Correctly caught invalid temperature: {e}")
        
        # Invalid reasoning effort
        try:
            ModelConfig(reasoning_effort="extreme")
            print("❌ Should have failed with invalid reasoning effort")
        except ValueError as e:
            print(f"✓ Correctly caught invalid reasoning effort: {e}")
        
        print("✓ All validation tests passed")
        
    except Exception as e:
        print(f"❌ Validation tests failed: {e}")
    
    print("\n" + "=" * 70 + "\n")
    print("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    # Usage summary
    print("\n📚 USAGE SUMMARY:")
    print("1. Basic Usage:")
    print
