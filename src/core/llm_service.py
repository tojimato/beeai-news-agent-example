"""LLM model management and initialization service.

This module implements a single-responsibility service for creating and managing
ChatModel instances from the BeeAI framework, decoupled from agent logic.
"""

from typing import Optional

from beeai_framework.backend import ChatModel, ChatModelParameters

from src.config.models import ModelConfig


class LLMService:
    """Service for managing LLM model initialization and access.
    
    Responsibility:
    - Create ChatModel instances with appropriate configurations
    - Manage model lifecycle (initialization, caching)
    - Provide typed access to models by use case
    
    NOT responsible for:
    - Prompt generation (Agents)
    - Data processing (DataProcessor)
    - Agent orchestration (Pipeline)
    
    Attributes:
        config: Model configuration object (Dependency Injection)
        _distiller_model: Cached distiller model instance
        _analyzer_model: Cached analyzer model instance
        _reviewer_model: Cached reviewer model instance
    """

    def __init__(self, config: ModelConfig | None = None) -> None:
        """Initialize LLM service with model configuration.
        
        Args:
            config: ModelConfig instance specifying which models to use.
                   If None, uses defaults from ModelConfig().
        """
        self.config: ModelConfig = config or ModelConfig()
        
        # Cache model instances to avoid recreating them
        self._distiller_model: Optional[ChatModel] = None
        self._analyzer_model: Optional[ChatModel] = None
        self._reviewer_model: Optional[ChatModel] = None

    def get_distiller_model(self) -> ChatModel:
        """Get or create the distiller model (fast, lightweight).
        
        Used for data distillation and extraction. Low temperature (0)
        for deterministic output.
        
        Returns:
            ChatModel configured for data distillation.
        """
        if self._distiller_model is None:
            self._distiller_model = ChatModel.from_name(
                self.config.distiller_model,
                ChatModelParameters(temperature=0)
            )
        return self._distiller_model

    def get_analyzer_model(self) -> ChatModel:
        """Get or create the analyzer model (powerful, detailed).
        
        Used for strategic synthesis and analysis. Medium temperature (0.2)
        for balanced creativity and consistency.
        
        Returns:
            ChatModel configured for strategic analysis.
        """
        if self._analyzer_model is None:
            self._analyzer_model = ChatModel.from_name(
                self.config.analyzer_model,
                ChatModelParameters(temperature=0.2)
            )
        return self._analyzer_model

    def get_reviewer_model(self) -> ChatModel:
        """Get or create the reviewer model (critical analysis).
        
        Used for peer review and critical evaluation. Low temperature (0.1)
        for focused, objective analysis.
        
        Returns:
            ChatModel configured for critical review.
        """
        if self._reviewer_model is None:
            self._reviewer_model = ChatModel.from_name(
                self.config.reviewer_model,
                ChatModelParameters(temperature=0.1)
            )
        return self._reviewer_model

    def get_model_by_name(
        self,
        model_name: str,
        temperature: float = 0.0
    ) -> ChatModel:
        """Get a ChatModel by name with custom temperature.
        
        Allows creating models outside the standard pipeline stages.
        Useful for custom processing or extensions.
        
        Args:
            model_name: Full model identifier (e.g., 'groq:llama-3.1-8b-instant')
            temperature: Sampling temperature for model output (0.0 to 1.0).
        
        Returns:
            ChatModel with specified configuration.
        
        Raises:
            ValueError: If model name is invalid.
        """
        if not model_name or not isinstance(model_name, str):
            raise ValueError(f"Invalid model name: {model_name}")
        
        return ChatModel.from_name(
            model_name,
            ChatModelParameters(temperature=temperature)
        )

    def reset_cache(self) -> None:
        """Clear all cached model instances.
        
        Useful for testing or switching configurations at runtime.
        Next access will reinitialize models.
        """
        self._distiller_model = None
        self._analyzer_model = None
        self._reviewer_model = None

    def get_config(self) -> ModelConfig:
        """Get the current model configuration.
        
        Returns:
            Current ModelConfig instance.
        """
        return self.config

    def update_config(self, config: ModelConfig) -> None:
        """Update model configuration and clear cache.
        
        Args:
            config: New ModelConfig instance.
        """
        self.config = config
        self.reset_cache()
