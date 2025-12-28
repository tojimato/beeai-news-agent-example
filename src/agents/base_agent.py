"""Abstract base class for all pipeline agents.

This module implements the template method pattern for agents, providing
a common interface and shared functionality while allowing concrete agents
to implement their specific logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from beeai_framework.backend import ChatModel
from beeai_framework.logger import Logger

from src.core.llm_service import LLMService
from src.utils.logger import log_token_usage


class BaseAgent(ABC):
    """Abstract base class for all pipeline agents.
    
    Implements the template method pattern and Open/Closed Principle:
    - Base provides shared structure and utilities
    - Concrete agents implement specific execute() logic
    - Extensible for new agent types without modifying base
    
    Attributes:
        name: Agent identifier for logging and reporting
        llm_service: Service managing LLM model access
        llm_model: Cached ChatModel instance from service
        logger: BeeAI framework logger for observability
        task_name: Human-readable task name for metric tracking
    """

    def __init__(
        self,
        name: str,
        llm_service: LLMService,
        task_name: str | None = None
    ) -> None:
        """Initialize base agent with dependencies (Dependency Injection).
        
        Args:
            name: Agent identifier (e.g., 'DistillerAgent').
            llm_service: LLMService instance for model access.
            task_name: Human-readable task name. Defaults to agent name.
        """
        self.name: str = name
        self.llm_service: LLMService = llm_service
        self.llm_model: Optional[ChatModel] = None
        self.logger: Logger = Logger(name, level="TRACE")
        self.task_name: str = task_name or name

    @abstractmethod
    async def execute(self, input_data: str) -> Any:
        """Execute the agent's primary task (implemented by subclasses).
        
        Args:
            input_data: Input text for processing.
        
        Returns:
            Agent-specific output (model response, structured data, etc.).
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent (implemented by subclasses).
        
        Returns:
            System message instructing the LLM on its role and behavior.
        """
        pass

    def get_llm_model(self) -> ChatModel:
        """Get or initialize the LLM model for this agent.
        
        Returns:
            ChatModel instance configured for this agent.
        """
        if self.llm_model is None:
            self.llm_model = self._initialize_model()
        return self.llm_model

    @abstractmethod
    def _initialize_model(self) -> ChatModel:
        """Initialize the appropriate LLM model (implemented by subclasses).
        
        Concrete agents specify which model from LLMService to use.
        
        Returns:
            Configured ChatModel instance.
        """
        pass

    def log_execution(self, stage: str, output: Any) -> None:
        """Log execution metrics and token usage.
        
        Args:
            stage: Pipeline stage name for identification.
            output: LLM output with usage metrics.
        """
        log_token_usage(output, f"{self.task_name} - {stage}")

    def log_debug(self, message: str) -> None:
        """Log debug information via framework logger.
        
        Args:
            message: Debug message to log.
        """
        self.logger.info(f"[{self.name}] {message}")

    def handle_error(self, error: Exception, context: str = "") -> None:
        """Handle and log errors in a consistent manner.
        
        Args:
            error: Exception that occurred.
            context: Additional context about where error occurred.
        
        Raises:
            RuntimeError: Re-raises error with enhanced context.
        """
        error_msg = f"[{self.name}] Error in {context}: {str(error)}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg) from error

    def reset(self) -> None:
        """Reset agent state (clear cached models, logger, etc).
        
        Useful for reusing agent instances across multiple runs.
        """
        self.llm_model = None
        self.logger = Logger(self.name, level="TRACE")

    def get_info(self) -> dict[str, str]:
        """Get agent metadata and configuration info.
        
        Returns:
            Dictionary with agent name, task name, and model info.
        """
        return {
            "agent_name": self.name,
            "task_name": self.task_name,
            "model_config": str(self.llm_service.get_config()),
        }
