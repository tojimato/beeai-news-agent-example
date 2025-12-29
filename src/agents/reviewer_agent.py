"""Reviewer Agent for critical analysis and peer review.

This agent specializes in critically evaluating strategic reports and
providing high-conviction alternative perspectives.
"""

from typing import Any

from beeai_framework.backend import ChatModel, UserMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.core.llm_service import LLMService
from src.prompts.prompt_templates import ReviewerPromptTemplate
from src.config.professions import Profession


class ReviewerAgent(BaseAgent):
    """Agent for critical analysis and peer review of strategic reports.
    Now supports profession-specific prompt templates.
    """

    def __init__(self, llm_service: LLMService, profession: Profession) -> None:
        """Initialize reviewer agent with profession.
        
        Args:
            llm_service: Service for model access.
            profession: Profession enum for prompt adaptation.
        """
        super().__init__(
            name="ReviewerAgent",
            llm_service=llm_service,
            task_name="Peer Review"
        )
        self.profession = profession
        self.prompt_template = ReviewerPromptTemplate(profession)

    def get_system_prompt(self) -> str:
        """Get system prompt for critical review (profession-specific).
        
        Returns:
            System message instructing the reviewer on its role.
        """
        return self.prompt_template.generate()

    def _initialize_model(self) -> ChatModel:
        """Initialize the reviewer model.
        
        Returns:
            Reviewer ChatModel (Gemini for critical analysis).
        """
        return self.llm_service.get_reviewer_model()

    async def execute(self, input_data: str) -> Any:
        """Execute critical review of strategic report.
        
        Args:
            input_data: Strategic report to review.
        
        Returns:
            Model response with critical analysis and recommendations.
        
        Raises:
            RuntimeError: If LLM execution fails.
        """
        try:
            model: ChatModel = self.get_llm_model()

            response: Any = await model.run(
                [
                    SystemMessage(self.get_system_prompt()),
                    UserMessage(f"Critique and find the highest conviction plays in this report:\n\n{input_data}")
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

    def get_review_text(self, response: Any) -> str:
        """Extract text content from reviewer response.
        
        Args:
            response: Model response object.
        
        Returns:
            Text content of the critical review.
        """
        try:
            return response.get_text_content()
        except Exception as e:
            self.handle_error(e, "get_review_text()")
