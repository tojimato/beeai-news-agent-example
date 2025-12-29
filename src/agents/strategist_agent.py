"""Strategist Agent for synthesizing strategic analysis.

This agent specializes in synthesizing distilled facts into high-density
strategic roadmaps and comprehensive analysis reports.
"""

from typing import Any

from beeai_framework.backend import ChatModel, UserMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.core.llm_service import LLMService
from src.prompts.prompt_templates import StrategistPromptTemplate
from src.config.professions import Profession


class StrategistAgent(BaseAgent):
    """Agent for synthesizing strategic insights and roadmaps.
    Now supports profession-specific prompt templates.
    """

    def __init__(self, llm_service: LLMService, profession: Profession) -> None:
        """Initialize strategist agent with profession.
        
        Args:
            llm_service: Service for model access.
            profession: Profession enum for prompt adaptation.
        """
        super().__init__(
            name="StrategistAgent",
            llm_service=llm_service,
            task_name="Strategic Synthesis"
        )
        self.profession = profession
        self.prompt_template = StrategistPromptTemplate(profession)

    def get_system_prompt(self) -> str:
        """Get system prompt for strategic analysis (profession-specific)."""
        return self.prompt_template.generate()

    def _initialize_model(self) -> ChatModel:
        """Initialize the powerful analyzer model.
        
        Returns:
            Analyzer ChatModel (Groq Strategy Model).
        """
        return self.llm_service.get_analyzer_model()

    async def execute(self, input_data: str) -> Any:
        """Execute strategic analysis on distilled data.
        
        Args:
            input_data: Distilled data to analyze strategically.
        
        Returns:
            Model response with strategic intelligence report.
        
        Raises:
            RuntimeError: If LLM execution fails.
        """
        try:
            model: ChatModel = self.get_llm_model()

            response: Any = await model.run(
                [
                    SystemMessage(self.get_system_prompt()),
                    UserMessage(f"Using these distilled facts, build the final report:\n\n{input_data}")
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

    def get_report_text(self, response: Any) -> str:
        """Extract text content from strategist response.
        
        Args:
            response: Model response object.
        
        Returns:
            Text content of the strategic report.
        """
        try:
            return response.get_text_content()
        except Exception as e:
            self.handle_error(e, "get_report_text()")
