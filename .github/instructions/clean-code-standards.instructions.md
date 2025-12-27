---
applyTo: "**"
---
# AI Coding Rules: Python Clean Code Standards

This file contains mandatory Python Clean Code standards. Follow every rule strictly.

## 1. Design & Architecture
- **SOLID & DRY:** Apply strictly. Extract logic repeated 2+ times into helper methods.
- **KISS & YAGNI:** Prefer simplicity. No speculative "future-use" code or abstractions.
- **Complexity:** Max 3 levels of indentation. Use **guard clauses** and early returns.
- **Functions:** Keep methods < 30 lines. Each function must have a single responsibility.
- **Decoupling:** Use **Dependency Injection** (pass dependencies via `__init__` or params).

## 2. Python Specifics (PEP 8+)
- **Naming:** `snake_case` (funcs/vars), `PascalCase` (classes), `UPPER_SNAKE` (constants).
- **Typing:** **Mandatory** type hints for all public parameters and return types.
- **Docstrings:** **Mandatory** Google Style docstrings for all public modules/classes/methods.
- **Modern Python:** Use `f-strings`, `list[T]` (3.9+), `Union` types as `int | str` (3.10+).

## 3. Reliability & Testing
- **Error Handling:** No bare `except:`. Catch specific exceptions. Log context, then re-raise.
- **Testing:** 70%+ coverage. Use **AAA (Arrange-Act-Assert)** pattern and `pytest.mark.parametrize`.
- **Async:** Use `async/await` for I/O. Prefer `asyncio.TaskGroup` (3.11+) for concurrency.
- **Pure Functions:** Prefer functions with no side effects for core business logic.

## 4. Performance & Security
- **Data Structures:** Use `set` for membership checks, `dict` for lookups (O(1)).
- **Optimization:** Do not optimize unless profiled. Prefer readability.
- **Security:** Zero hardcoded secrets. Use `.env.local`. Validate all external API inputs.

## 5. Review Checklist (AI Instructions)
- Remove unused imports and dead code paths immediately.
- Extract magic numbers to named constants at the top of the file/class.
- If logic takes 5+ lines to explain, extract it to a boolean predicate method.
- Use explicit loops over complex/nested list comprehensions.
