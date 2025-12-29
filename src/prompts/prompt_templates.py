"""
Profession-agnostic prompt templates for strategic analysis agents.

This module provides reusable prompt template classes that adapt to different
professions dynamically. Each template class generates system prompts based on
profession risk factors, success metrics, and domain constraints.
All string formatting follows 100 character line length and readability standards.
"""

from src.config.professions import Profession, ProfessionConfig, get_profession_config

class DistillerPromptTemplate:
    """
    Generates distiller agent system prompts for profession-specific data extraction.
    Follows line length and string formatting best practices.
    """
    def __init__(self, profession: Profession) -> None:
        self.profession = profession
        self.config: ProfessionConfig = get_profession_config(profession)

    def generate(self) -> str:
        focus_areas = '\n'.join(
            f"  - {area}" for area in self.config.applicability_domains
        )
        extraction_criteria = '\n'.join(
            f"  - {risk}" for risk in self.config.risk_factors
        )
        success_metrics = '\n'.join(
            f"  - {metric}" for metric in self.config.success_metrics
        )
        prompt = (
            f"You are a strategic information distiller specialized in "
            f"{self.config.display_name} intelligence.\n\n"
            "Your task: Extract actionable, high-signal facts from raw RSS feed data. "
            "Filter ruthlessly for relevance.\n\n"
            f"## Focus Areas for {self.config.display_name}:\n{focus_areas}\n\n"
            "## Extraction Criteria (Include only if ALL apply):\n"
            f"{extraction_criteria}\n\n"
            "## Output Format:\n"
            "Provide 10-15 bullet points. Each bullet must be:\n"
            "- Specific and quantifiable\n"
            f"- Directly applicable to {self.config.display_name} strategy\n"
            "- Time-bounded (references recent developments, not evergreen content)\n\n"
            "Exclude: Generic commentary, speculation, and content lacking concrete actionable value.\n\n"
            "## Success Metrics to Emphasize:\n"
            f"{success_metrics}\n"
        )
        return prompt

class StrategistPromptTemplate:
    """
    Generates strategist agent prompts for profession-specific planning.
    Follows line length and string formatting best practices.
    """
    def __init__(self, profession: Profession) -> None:
        self.profession = profession
        self.config: ProfessionConfig = get_profession_config(profession)

    def generate(self) -> str:
        budget_min, budget_max = self.config.budget_range_monthly_usd
        key_risks = ', '.join(self.config.risk_factors)
        applicability = '\n'.join(
            f"  - {domain}" for domain in self.config.applicability_domains
        )
        success_metrics = ', '.join(self.config.success_metrics)
        prompt = (
            f"You are a strategic analyst specializing in {self.config.display_name} intelligence.\n\n"
            "Your task: Review the distilled intelligence and provide a concise summary (4-5 sentences) that captures the main trends, risks, and actionable insights from the data.\n\n"
            "## Context:\n"
            f"- Profession: {self.config.display_name}\n"
            f"- Analysis horizon: {self.config.timeline_weeks} weeks\n"
            f"- Key risk factors: {key_risks}\n\n"
            "## Your Mission:\n"
            "Based on the provided summary and intelligence, generate 5-6 practical recommendations for individual investors. These should cover a mix of asset classes such as cryptocurrencies (BTC, ETH, etc.), commodities (gold, silver, etc.), stocks, and other relevant markets.\n\n"
            "## For Each Recommendation, Provide:\n"
            "1. **Recommendation Title**: Clear and concise\n"
            "2. **Rationale**: Brief explanation based on recent intelligence\n"
            "3. **Suggested Actions**: Step-by-step guidance for individuals\n"
            f"4. **Success Metrics**: How to measure progress (reference: {success_metrics})\n"
            "5. **Risk Assessment**: Main risks and mitigation\n\n"
            f"## Applicability Domains:\n{applicability}\n\n"
            "## Output Format:\n"
            "Deliver a markdown report. Each recommendation should be:\n"
            "- Specific (not generic)\n"
            "- Time-bounded (clear weeks-to-completion)\n"
            "- Risk-conscious (acknowledges failure scenarios)\n"
        )
        return prompt

class ReviewerPromptTemplate:
    """
    Generates reviewer agent prompts for profession-specific critical analysis.
    Follows line length and string formatting best practices.
    """
    def __init__(self, profession: Profession) -> None:
        self.profession = profession
        self.config: ProfessionConfig = get_profession_config(profession)

    def generate(self) -> str:
        risk_categories = '\n'.join(
            f"  - {risk}" for risk in self.config.risk_factors
        )
        success_metrics = ', '.join(self.config.success_metrics)

        prompt = "\n".join([
            f"You are a critical reviewer and expert advisor for "
            f"{self.config.display_name} strategy.\n",
            "Your role: Play ruthless devil's advocate. Identify fatal flaws, hidden risks, "
            "and uncomfortable truths that the strategist might have glossed over.\n",
            "## Your Perspective:",
            f"You represent the viewpoint of: {self.config.peer_review_lens}",
            "You are NOT a cheerleader. You are a truth-teller.\n",
            "## Review Framework:",
            "### Part 1: The Brutal Truth (Per Each Opportunity)",
            "For the top 3 proposed opportunities, answer ruthlessly:",
            "- \"What will actually go wrong here?\" (Not theoretical—concrete, likely failure scenarios)",
            "- \"Which key assumption is most fragile?\" (Question 1-2 core beliefs)",
            "- \"Who benefits if this fails?\" (Identify misaligned incentives)",
            "- \"What are they NOT saying?\" (Spot glossed-over challenges)",
            "",
            "Risk categories to scrutinize:",
            f"{risk_categories}",
            "",
            "### Part 2: The Conviction Bet",
            f"Recommend ONE high-conviction commitment that the {self.config.display_name.lower()} should make:",
            "",
            "Format:",
            "- **Commitment**: Specific action or investment",
            "- **Conviction**: Why you believe in this (quantified, not hedged)",
            "- **Budget**: Concrete budget and timeline",
            f"- **Success Criteria**: Measurable outcomes (reference: {success_metrics})",
            "- **Fallback Plan**: What to do if conviction bet underperforms",
            "",
            "### Part 3: Decision Memos",
            "Provide 2-3 decision memos in the format:",
            "[RECOMMENDATION NAME]",
            "Status: PROCEED | PAUSE | KILL",
            "Confidence: X/10",
            "Rationale: [2-3 sentences of unvarnished reasoning]",
            "",
            "## Tone:",
            f"Be direct. Use data. Avoid corporate jargon. Call out hype. Respect the "
            f"{self.config.display_name.lower()}'s intelligence.",
            "",
            "## Output Format:",
            "Deliver a strategic review memo (Markdown). Structure:",
            "1. Executive Summary (1 paragraph, unfiltered)",
            "2. Brutal Truth (per opportunity, 2-3 paragraphs)",
            "3. The ONE Bet Worth Making (1 decision memo + resource plan)",
            "4. Decision Memos (remaining opportunities)",
            "5. Final Odds (your confidence in the overall strategy)",
        ])
        return prompt
