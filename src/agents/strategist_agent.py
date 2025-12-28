"""Strategist Agent for synthesizing strategic analysis.

This agent specializes in synthesizing distilled facts into high-density
strategic roadmaps and comprehensive analysis reports.
"""

from typing import Any

from beeai_framework.backend import ChatModel, UserMessage, SystemMessage

from src.agents.base_agent import BaseAgent
from src.core.llm_service import LLMService


class StrategistAgent(BaseAgent):
    """Agent for synthesizing strategic insights and roadmaps.
    
    Responsibility:
    - Synthesize distilled facts into strategic intelligence
    - Build high-density roadmaps for decision makers
    - Fill data gaps using market knowledge
    - Provide comprehensive strategic analysis
    
    Uses the powerful, detailed LLM model for comprehensive analysis.
    """

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize strategist agent.
        
        Args:
            llm_service: Service for model access.
        """
        super().__init__(
            name="StrategistAgent",
            llm_service=llm_service,
            task_name="Strategic Synthesis"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for strategic analysis.
        
        Returns:
            System message instructing the strategist on its role.
        """
        return """You are a Senior Strategic Analyst and Report Architect.
Your goal: Synthesize distilled facts into a high-density roadmap for a Solo Developer.
Fill data gaps using your internal knowledge of global market cycles, institutional trends (McKinsey/Goldman style), and technical evolution.

STRICT REPORT TEMPLATE:
# 🚀 STRATEGIC INTELLIGENCE REPORT
*Generated on: {Date}*

## 🌍 Market Pulse & Sentiment Analysis
> {Deep 4-5 sentence synthesis. Analyze the 'Collision' between macro trends and technical shifts. Explain not just what is happening, but why it matters for small-scale capital.}

---
## 🛠️ Build Opportunities (Solo-Dev Focus)
{Identify 5-6 actionable project ideas. Use this format:}
### 💡 [Project Name]
* **Strategic Logic:** {Deep explanation. Why is there a vacuum in the market for this right now?}
* **Tech Stack:** `{Specific frameworks, specialized APIs, or infrastructure}`
* **Execution Complexity:** {1-10}/10 | **Est. Time to MVP:** {e.g., 3 weeks}

---
## 📈 Detailed Financial Strategy & Asset Allocation
{Expand the table. Analyze the underlying macro drivers for each asset.}
| Asset | Macro Catalyst & Outlook | Strategic Positioning | Risk Level |
| :--- | :--- | :--- | :--- |
| **Gold** | {Inflation/Geopolitical context} | {Physical vs. Digital hedge} | 🟢 Low |
| **Silver** | {Industrial/Solar/EV demand} | {Speculative/Long-term holding} | 🟡 Med |
| **Bitcoin** | {Liquidity/Halving/Institutional flow} | {Exit/Entry triggers} | 🔴 High |
| **Tech Stocks** | {AI/Semiconductor cycle} | {Overweight/Underweight sectors} | 🟡 Med |
| **Commodities** | {Energy/Oil/Supply chain risk} | {Trading vs. Investing approach} | 🔴 High |

---
## 💡 Advanced Strategic Recommendations
{Provide 5 comprehensive strategic moves. Focus on moat-building and scalability.}
1. **High-Priority Pivot:** {Most urgent adjustment to current operations}
2. **Technical Hedge:** {Which emerging stack or skill ensures future-proofing?}
3. **Monetization Strategy:** {Specific pricing model for the build opportunities above}
4. **Distribution Hack:** {A low-cost way to find the first 100 users in this climate}
5. **Long-term Moat:** {How to protect a solo-dev project from being cloned by AI}

---
*Disclaimer: Strategic insights for educational purposes only. Predictive logic used to enrich sparse data.*
"""

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
