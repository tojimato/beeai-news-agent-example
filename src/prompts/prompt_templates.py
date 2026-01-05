from src.prompts.header_translations import HEADER_TRANSLATIONS
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
    Generates distiller agent system prompts for data cleaning and topic grouping.
    Follows line length and string formatting best practices.
    """
    def __init__(self) -> None:
        pass

    def generate(self) -> str:
        prompt = (
            "You are a data distiller agent.\n\n"
            "Your task: Clean and organize raw RSS feed data. Remove duplicates, irrelevant, or low-signal entries. Group similar topics together for clarity.\n\n"
            "## Output Format:\n"
            "- Provide 5-8 grouped bullet points.\n"
            "- For each group: write a bolded group title, then a short 1-2 sentence summary, then at the end of the group, list all related links (one per line, as a block).\n"
            "- Do not repeat links in the summary text.\n"
            "- No unnecessary explanation, only group title, summary, and links.\n"
            "\nExample:\n"
            "- **[Example Title]**\n"
            "  [Example Description.]\n"
            "  Links:\n"
            "    https://www.example.com/ai-research-overview\n"
            "    ..."
            "    ..."
        )
        return prompt

class StrategistPromptTemplate:
    """
    Generates strategist agent prompts for profession-specific planning.
    Follows line length and string formatting best practices.
    """
    def __init__(self, profession: Profession, language: str = "tr") -> None:
        self.profession = profession
        self.config: ProfessionConfig = get_profession_config(profession)
        self.language = language

    def generate(self) -> str:
        lang = self.language if self.language in HEADER_TRANSLATIONS else "en"
        h = HEADER_TRANSLATIONS[lang]
        applicability = '\n'.join(
            f"  - {domain}" for domain in self.config.applicability_domains
        )
        success_metrics = ', '.join(self.config.success_metrics)
        key_risks = ', '.join(self.config.risk_factors)
        prompt = (
            f"Return all results in {self.language.upper()} language.\n\n"
            f"You are a strategic analyst specializing in {self.config.display_name} intelligence.\n\n"
            "Your task: Analyze the distilled data provided and summarize most important global developments for your profession.\n\n"
            "Identify 3-4 concrete opportunities or actions that directly help achieve the following Success Metrics, considering the Key Risks.\n"
            "If the data is missing or unclear on any important point, use your own expertise and general knowledge to fill in the gaps.\n\n"
            f"## Success Metrics:\n- {success_metrics}\n\n"
            f"## Key Risks:\n- {key_risks}\n\n"
            f"## Output Format (Markdown, always use this structure):\n"
            f"# {h['report_title']}\n"
            f"## {h['summary']}\n"
            f"- [Short summary: what matters today for your profession, 2-3 sentences]\n"
            f"\n## {h['opportunities']} (3-4 items)\n"
            "For each, use this format:\n"
            f"### [{h['opportunity_title']}]\n"
            f"- **{h['why_now']}:** [1 sentence, why this is timely]"
            f"- **{h['action_steps']}:** [How to achieve the relevant success metric(s)]"
            f"- **{h['risk_note']}:** [Which key risk(s) are most relevant, and how to mitigate]"
            f"- **{h['sources']}:** [List source urls as external link markdown format][External link to title](https://www.genome.gov/)\n"
            f"\n## {h['applicability']} in {self.language.upper()} language.\n"
            f"{applicability}\n"
        )
        return prompt

class ReviewerPromptTemplate:
    """
    Generates reviewer agent prompts for profession-specific critical analysis.
    Follows line length and string formatting best practices.
    """
    def __init__(self, profession: Profession, language: str = "tr") -> None:
        self.profession = profession
        self.config: ProfessionConfig = get_profession_config(profession)
        self.language = language

    def generate(self) -> str:
        risk_categories = ', '.join(self.config.risk_factors)
        success_metrics = ', '.join(self.config.success_metrics)
        prompt = (
            f"Return all results in {self.language.upper()} language.\n\n"
            f"You are a critical reviewer for {self.config.display_name} strategy.\n\n"
            "Your task: For each opportunity/action, briefly identify the most critical risk, the weakest assumption, and any missing perspective.\n\n"
            f"## Key Risks: {risk_categories}\n"
            f"## Success Metrics: {success_metrics}\n"
            "## Output Format:\n"
            "- For each opportunity: 1-2 sentence critique (risk, assumption, missing view).\n"
            "- At the end: 1 sentence overall confidence level with percentage.\n"
        )
        return prompt