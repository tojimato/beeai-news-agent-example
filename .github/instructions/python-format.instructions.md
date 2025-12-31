---
applyTo: "**"
---

# Python Formatting & Line Length Standard

- **Maximum line length:** 100 characters (PEP 8 recommended, enforced for all code and docstrings)

- **Import Placement:**
  - All imports must be at the top of the file, after any module comments or docstrings, and before module globals or constants.
  - Do not place imports inside functions, classes, or code blocks unless absolutely necessary (e.g., to avoid circular imports or for optional dependencies).
  - Group imports in the following order, separated by a single blank line:
    1. Standard library imports
    2. Related third-party imports
    3. Local application/library-specific imports
  - Use absolute imports whenever possible.

- **Blank Line Usage:**
  - Use a single blank line between functions, methods, and class definitions.
  - Use two blank lines before top-level function and class definitions.
  - Do not use extra blank lines between statements inside a function, method, or class unless separating logical sections.
  - Always add a single blank line between distinct logical blocks within a function (e.g., input validation, data preparation, main logic, output/return). This improves readability and makes code easier to follow.
  - Avoid multiple consecutive blank lines anywhere in the file.

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
import os
import sys

import requests

from src.utils.logger import log_info

class MyClass:
    def foo(self):
        pass

def bar():
    pass

prompt = (
    f"You are a reviewer for {self.config.display_name}. "
    f"Your task: {self.config.peer_review_lens}. "
    f"\n\nKey risks: {', '.join(self.config.risk_factors)}."
)
```

> This standard is mandatory for all Python code in this repository.
