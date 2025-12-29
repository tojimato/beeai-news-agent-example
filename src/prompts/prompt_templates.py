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
        key_risks = ', '.join(self.config.risk_factors[:3])
        applicability = '\n'.join(
            f"  - {domain}" for domain in self.config.applicability_domains
        )
        success_metrics = ', '.join(self.config.success_metrics[:2])
        prompt = (
            f"You are a strategic analyst specializing in "
            f"{self.config.display_name} intelligence.\n\n"
            "Your task: Synthesize intelligence into a cohesive strategic action plan.\n\n"
            "## Context:\n"
            f"- Profession: {self.config.display_name}\n"
            f"- Monthly budget range: ${budget_min:,} - ${budget_max:,}\n"
            f"- Project timeline horizon: {self.config.timeline_weeks} weeks\n"
            f"- Key risk factors: {key_risks}\n\n"
            "## Your Mission:\n"
            f"Based on the distilled intelligence provided, identify **5-6 concrete, actionable "
            f"opportunities** that a {self.config.display_name.lower()} can pursue within "
            f"{self.config.timeline_weeks} weeks.\n\n"
            "## For Each Opportunity, Provide:\n"
            "1. **Opportunity Name**: Clear, memorable title\n"
            "2. **Why Now**: Time-sensitive trigger from recent intelligence\n"
            f"3. **Execution Plan**: Step-by-step (Week 1-4, Weeks 5-8, Weeks 9-"
            f"{self.config.timeline_weeks})\n"
            "4. **Resource Needs**: Team, tools, budget breakdown\n"
            f"5. **Success Metrics**: How to measure progress (reference: {success_metrics})\n"
            "6. **Risk Assessment**: Biggest execution blockers and mitigation\n\n"
            f"## Financial Hedging Strategy:\n"
            f"Allocate {self.config.display_name.lower()} resources across 3-5 hedges:\n"
            "- Primary play (highest conviction, 50% of budget)\n"
            "- Secondary plays (30% of budget)\n"
            "- Hedge positions (20% of budget)\n\n"
            f"## Applicability Domains:\n{applicability}\n\n"
            "## Output Format:\n"
            "Deliver a comprehensive markdown strategic roadmap. Each opportunity should be:\n"
            "- Specific (not generic)\n"
            "- Time-bounded (clear weeks-to-completion)\n"
            "- Budget-aware (respects monthly burn)\n"
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
