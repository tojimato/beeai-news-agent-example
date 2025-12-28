"""Distiller Agent for data extraction and condensing.

This agent specializes in stripping away fluff from raw data and extracting
only technical facts and financial data points in structured format.
"""

from typing import Any

from beeai_framework.backend import ChatModel, UserMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.core.llm_service import LLMService


class DistillerAgent(BaseAgent):
    """Agent for condensing raw data into structured facts.
    
    Responsibility:
    - Strip away fluff from news entries
    - Extract technical facts and financial data points
    - Output in condensed bullet-point format
    - Group related news items
    
    Uses the fast, lightweight LLM model for quick processing.
    """

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize distiller agent.
        
        Args:
            llm_service: Service for model access.
        """
        super().__init__(
            name="DistillerAgent",
            llm_service=llm_service,
            task_name="Data Distillation"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for data distillation.
        
        Returns:
            System message instructing the distiller on its role.
        """
        return """You are a Data Distiller.
Your goal is to strip away the fluff from news entries and extract only technical facts and financial data points.

TASKS:
1. Group related news.
2. Extract specific numbers, tech stacks, and regulatory mentions.
3. Output in a condensed bullet-point format.

OUTPUT FORMAT:
- CATEGORY: <Name>
- FACTS: <Technical/Financial fact 1>, <Fact 2>
- KEY_TECHS: <Tools/APIs mentioned>
"""

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
