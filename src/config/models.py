"""LLM Model configuration for BeeAI strategy analysis pipeline.

This module centralizes all LLM model definitions organized by provider
and use case. Models are sourced from environment variables via .env.local
to ensure secrets remain decoupled from code.
"""

from dataclasses import dataclass

# ============================================================================
# Groq Models - High-speed open-source LLM inference
# ============================================================================

GROQ_STRATEGY_MODEL: str = "groq:openai/gpt-oss-120b"
"""Groq-hosted GPT OSS 120B model for strategic analysis and planning."""

GROQ_TRANSLATOR_MODEL: str = "groq:openai/gpt-oss-20b"
"""Groq-hosted GPT OSS 20B model for language translation tasks."""

GROQ_COMPOUND_MODEL: str = "groq:groq/compound"
"""Groq compound model for complex reasoning chains."""

GROQ_LLAMA_8B_MODEL: str = "groq:llama-3.1-8b-instant"
"""Groq-hosted Llama 3.1 8B for lightweight, fast inference."""

# ============================================================================
# OpenAI Models - GPT-5 family for production workloads
# ============================================================================

OPENAI_STRATEGY_MODEL: str = "openai:gpt-5"
"""OpenAI GPT-5 for advanced strategic analysis and decision support."""

OPENAI_TRANSLATOR_MODEL: str = "openai:gpt-5-mini"
"""OpenAI GPT-5-mini for efficient translation with lower latency/cost."""

OPENAI_CHEAPEST_MODEL: str = "openai:gpt-5-nano"
"""OpenAI GPT-5-nano for cost-optimized lightweight tasks."""

# ============================================================================
# Specialized Models - Reasoning and review capabilities
# ============================================================================

XAI_REVIEWER_MODEL: str = "xai:grok-4-1-fast-reasoning"
"""XAI Grok-4.1 fast reasoning model for real-time analysis and review."""

GEMINI_REVIEWER_MODEL: str = "gemini:gemini-3-flash-preview"
"""Google Gemini 3 Flash for preview and review workflows."""


@dataclass(frozen=True)
class ModelConfig:
    """Immutable configuration for model selection across pipeline stages.
    
    Attributes:
        distiller_model: Model for data distillation (fast, lightweight)
        analyzer_model: Model for strategic synthesis (powerful, detailed)
        reviewer_model: Model for peer review and critical analysis
    """

    distiller_model: str = GROQ_LLAMA_8B_MODEL
    analyzer_model: str = GROQ_STRATEGY_MODEL
    reviewer_model: str = GEMINI_REVIEWER_MODEL
