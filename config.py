"""Configuration module for BeeAI strategy analysis pipeline.

This module centralizes all LLM model configuration across the agent system.
Models are sourced from environment variables via the .env.local file to ensure
secrets and environment-specific settings remain decoupled from code.

Models are grouped by provider (Groq, OpenAI, XAI, Gemini) and use case
(strategy, translation, review, compound reasoning).
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env.local file (secrets, API keys)
load_dotenv(".env.local")

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
