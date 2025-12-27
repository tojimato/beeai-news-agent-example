---
applyTo: "**"
---
# Instructions

## 1. Core Mission
We are building a multi-agent LLM pipeline using the **BeeAI framework**. The project is currently in active development; prioritize flexibility and scalable architecture over fixed legacy patterns.

## 2. Global Standards (Mandatory)
- **Primary Source:** You MUST strictly follow every rule defined in `.github/instructions/clean-code-standards.instructions.md`.
- **Compliance Check:** Before finalizing any code, verify it against the Clean Code checklist in the standards file.

## 3. Framework & Technical Constraints
- **Cost/Token Tracking:** Ensure every LLM response is processed for token/cost metrics using available utility patterns.
- **Environment:** Secrets must stay in `.env.local` (never hardcode keys).

## 4. Coding Behavior
- **Refactoring:** Proactively suggest refactors for "Legacy" or "Messy" code based on our Clean Code standards.
- **Language:** All new code, docstrings, and comments must be in **English**.
- **Efficiency:** Prioritize readability and maintainability as defined in the primary standards file.