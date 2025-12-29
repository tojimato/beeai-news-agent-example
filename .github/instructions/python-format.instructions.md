---
applyTo: "**"
---
# Python Formatting & Line Length Standard

- **Maximum line length:** 100 characters (PEP 8 recommended, enforced for all code and docstrings)
- **String formatting:**
  - Use multi-line strings (triple quotes) or parentheses for long f-strings.
  - Prefer breaking up long format expressions for readability.
  - For prompt templates, use dedented multi-line strings and avoid single-line f-strings >100 chars.
- **General:**
  - Break up long function calls and argument lists across multiple lines.
  - Use implicit line joining inside parentheses, brackets, and braces.
  - Never concatenate long strings with `+` for line length reasons; use multi-line strings instead.

**Example:**

```
prompt = (
    f"You are a reviewer for {self.config.display_name}. "
    f"Your task: {self.config.peer_review_lens}. "
    f"\n\nKey risks: {', '.join(self.config.risk_factors)}."
)
```

> This standard is mandatory for all Python code in this repository.
