"""Distiller Agent for data extraction and condensing.

This agent specializes in stripping away fluff from raw data and extracting
only technical facts and financial data points in structured format.
"""

from typing import Any

from beeai_framework.backend import ChatModel, UserMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.core.llm_service import LLMService
from src.prompts.prompt_templates import DistillerPromptTemplate
from src.config.professions import Profession


class DistillerAgent(BaseAgent):
    """Agent for condensing raw data into structured facts.
    Uses a generic, profession-agnostic prompt template.
    """

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize distiller agent (profession-agnostic). 
        Args:
            llm_service: Service for model access.
        """
        super().__init__(
            name="DistillerAgent",
            llm_service=llm_service,
            task_name="Data Distillation"
        )
        self.prompt_template = DistillerPromptTemplate()

    def get_system_prompt(self) -> str:
        """Get system prompt for data distillation (profession-agnostic)."""
        return self.prompt_template.generate()

    def _initialize_model(self) -> ChatModel:
        """Initialize the fast distiller model.
        
        Returns:
            Distiller ChatModel (Groq Llama 8B).
        """
        return self.llm_service.get_distiller_model()

    async def execute(self, input_data: str) -> Any:
        """Execute data distillation on raw feed data.
        
        Args:
            input_data: Raw feed data to distill.
        
        Returns:
            Model response with distilled structured facts.
        
        Raises:
            RuntimeError: If LLM execution fails.
        """
        try:
            model: ChatModel = self.get_llm_model()

            response: Any = await model.run(
                [
                    SystemMessage(self.get_system_prompt()),
                    UserMessage(f"Distill this raw feed data:\n\n{input_data}")
                ]
            ).observe(
                lambda emitter: emitter.on(
                    "*",
                    lambda data, event: self.log_debug(
                        f"Event: {event.path} | Target: {type(event.creator).__name__}"
                    )
                )
            )

            # Log metrics
            self.log_execution("Completion", response)

            return response

        except Exception as e:
            self.handle_error(e, "execute()")

    def get_distilled_text(self, response: Any) -> str:
        """Extract text content from distiller response.
        
        Args:
            response: Model response object.
        
        Returns:
            Text content of the distilled data.
        """
        try:
            return response.get_text_content()
        except Exception as e:
            self.handle_error(e, "get_distilled_text()")
