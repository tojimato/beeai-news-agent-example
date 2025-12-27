# Python Clean Code Standards & Architecture Principles

**A Comprehensive Guide for Senior Engineers & Development Teams**

---

## Overview

This document establishes baseline clean code standards for professional Python development. These principles apply to all projects and should guide code generation, reviews, and architectural decisions.

**Core Values**: Maintainability > Clever Code | Clarity > Conciseness | Testability > Performance (unless profiled)

---

## 1. DRY (Don't Repeat Yourself)

### Principle
Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.

### Rules & Guidelines

#### Extract Repeated Logic into Helper Methods
- **Identify**: Code blocks appearing 2+ times → Extract to method
- **Scope**: Extract at the method level first; promote to class/module level if needed across multiple classes
- **Naming**: Use descriptive names that explain the transformation (`extract_summary()` not `proc()`)
- **Testing**: Helper methods must be independently testable

#### Consolidate Configuration & Magic Numbers
- **Definition**: Any number or string appearing in code that could change → Named constant
- **Location**: Class-level constants at the top (Python convention)
- **Naming**: UPPERCASE_WITH_UNDERSCORES for module/class-level constants
- **Documentation**: Include inline comment explaining the constant's purpose/impact
- **Example**: `MAX_RETRIES = 3  # Max API retry attempts before circuit break`

#### Extract Keyword Collections & Data Structures
- **Reusability**: Shared keyword lists, enums, mappings → Class/module level
- **Discoverability**: Centralize related constants to one location for easier updates
- **Testability**: Allows unit testing without embedding test data in methods

#### Create Wrapper Methods for Repeated API Calls
- **Pattern**: Same external service called with minor variations → Single wrapper
- **Responsibility**: Wrapper handles authentication, error handling, logging
- **Flexibility**: Accept parameters for variation, keep boilerplate in wrapper
- **Example**: One `_run_llm_stage()` method instead of duplicating API calls across pipeline stages

#### Use Generators & Comprehensions Wisely
- **Generators**: Use for large sequences (memory-efficient iteration)
- **Comprehensions**: Use for simple transformations; extract to methods if complex
- **Rule**: One condition/operation per comprehension; beyond that → explicit loop

#### Avoid Copy-Paste Conditional Logic
- **Red Flag**: Same `if/elif/else` pattern repeated → Extract to boolean method
- **Naming**: Predicates should answer a yes/no question (`_should_skip()`, `_is_valid()`)
- **Complexity**: If condition takes 5+ lines to express → Extract immediately

#### DRY Applies to Tests
- **Test Fixtures**: Reuse setup code across test classes (don't duplicate test data)
- **Test Helpers**: Extract common assertions or object creation to utility functions
- **Parametrization**: Use `pytest.mark.parametrize` instead of copy-pasted test cases

---

## 2. KISS (Keep It Simple, Stupid)

### Principle
The simplest solution is usually the best. Avoid unnecessary complexity; optimize for readability first.

### Rules & Guidelines

#### Decompose Functions into Smaller Units
- **Target**: Each method < 30 lines of code
- **Red Flag**: If you can't explain the method in 1-2 sentences → Too broad
- **Strategy**: Extract helpers with clear names instead of dense logic
- **Benefit**: Easier to test, debug, and reason about independently

#### Use Early Returns & Guard Clauses
- **Pattern**: Check preconditions first; return early if unmet
- **Benefit**: Reduces nesting depth (max 3 levels)
- **Readability**: Happy path becomes main flow, not buried in nested blocks

#### Avoid Deep Nesting
- **Max Levels**: 3 levels of indentation maximum
- **Refactoring**: Extract inner loops/conditions to separate methods
- **Trade-off**: Slightly more methods beats reduced readability from nesting

#### Name Variables & Methods to Be Self-Documenting
- **Abbrevations**: Never use (except standard loop vars: `i`, `j`, `k`)
- **Length**: Longer names are fine if they clarify intent
- **Examples**: `feed_entries` not `d`, `relevance_score` not `x`
- **Boolean Names**: Prefix with `is_`, `has_`, `should_`, `can_` to make intent clear

#### Use Explicit Loops Over Complex Comprehensions
- **Rule**: If comprehension has multiple conditions or transformations → Use explicit loop
- **Clarity**: `for x in items if condition1 if condition2` is hard to read
- **Readability**: 5-line loop is clearer than dense one-liner

#### Minimize Conditional Branches
- **Polymorphism**: Use inheritance or composition instead of large switch statements
- **Strategy Pattern**: Different strategies per condition instead of one method with many branches
- **Guard Clauses**: Handle exceptions early, don't nest the main logic

#### Prefer Standard Library & Well-Known Patterns
- **Familiarity**: Developers know `dict.get()`, `if not x:`, etc.
- **Reinvention**: Don't write custom utility when standard library has it
- **Trade-off**: Small stdlib learning curve beats maintaining custom code

#### Avoid "Clever" Code
- **Red Flag**: Code that requires detailed explanation → Too clever
- **Principle**: Code is read 10x more than written; optimize for readers
- **Examples to Avoid**: Nested ternaries, complicated list comprehensions, bit-twiddling without necessity

---

## 3. YAGNI (You Aren't Gonna Need It)

### Principle
Don't implement features/abstraction until you have concrete use cases. Avoid speculative "nice-to-have" code.

### Rules & Guidelines

#### Delete Unused Imports
- **Pattern**: Regular cleanup; unused imports create false dependencies
- **Tooling**: Use linters (`pylint`, `flake8`) to identify unused imports
- **CI/CD**: Fail builds if unused imports are detected

#### Remove Dead Code Paths
- **Conditional Branches**: Delete code for features that don't exist yet
- **Deprecated Methods**: Remove old implementations (git history preserved)
- **Red Flag**: Code inside `if False:` or `# TODO: implement later` → Delete it

#### Avoid Speculative Error Handling
- **Rule**: Handle real failures, not hypothetical ones
- **Pattern**: Don't catch exceptions you've never seen in production
- **Balance**: Handle expected failures (network timeouts, malformed input); ignore rare edge cases

#### Don't Over-Engineer Abstractions
- **Interfaces**: Don't create abstract base classes without 2+ concrete implementations
- **Generics**: Don't parameterize code for "future flexibility" with no current use
- **Red Flag**: Interfaces/classes with zero current usage → Delete them

#### No Optional Parameters "Just in Case"
- **Rule**: Add parameters only when callers actually need them
- **Design**: If parameter unused by any caller → Remove it
- **Refactoring**: Add parameters later when needed; not premature

#### Eliminate TODO/FIXME Comments for Hypotheticals
- **Valid TODOs**: Known issues to fix; link to issue tracker
- **Invalid TODOs**: "We might want to support X" → Not a TODO, it's speculation
- **Action**: Convert speculative TODOs to feature requests in issue tracker, then delete comment

#### No Defensive Programming for Untrusted Input
- **Rule**: Trust your dependencies and standard library
- **Validate**: Only validate user input and external API responses
- **Example**: Don't check if `feed.entries` is None if feedparser guarantees it's a list

#### Feature Parity with Simplicity
- **Choice**: Simple solution covering 80% of use cases > Complex solution for 100%
- **Postpone**: Add edge cases later when they become requirements
- **Iterate**: Release MVP, gather feedback, then extend

---

## 4. SOLID Principles

### Single Responsibility Principle (SRP)

#### Definition
A class or function should have one reason to change.

#### Rules
- **One Reason**: Identify the class's primary responsibility; anything else belongs elsewhere
- **Cohesion**: Methods should closely relate to the class's core purpose
- **Change Impact**: If multiple unrelated requirements change together → Likely violates SRP

#### Anti-Patterns
- God Objects: Classes doing parsing, validation, transformation, and I/O
- Utility Classes: Classes mixing unrelated helpers (e.g., `StringUtils`, `DateUtils`)

#### Refactoring
- **Composition**: Delegate related responsibilities to helper objects
- **Separation**: Parse separately from transform, validate separately from save
- **Naming**: Class name should match its single responsibility (e.g., `FeedParser`, `EntryScorer`, `ReportGenerator`)

#### Testing Benefit
- Single responsibility → Easier unit tests (fewer mocks, fewer scenarios)
- Small focused test suite → Fast execution, clear failure messages

### Open/Closed Principle (OCP)

#### Definition
Software entities should be open for extension but closed for modification.

#### Rules
- **Extension**: New behaviors added without modifying existing code
- **Closed**: Existing code shouldn't change when new features arrive
- **Mechanism**: Inheritance, composition, or strategy pattern

#### Techniques
- **Inheritance**: Subclass to extend behavior without modifying parent
- **Composition**: Inject strategies/plugins to vary behavior
- **Polymorphism**: Accept abstract types, not concrete implementations

#### Anti-Patterns
- Large `if/elif/elif` chains for each new feature
- Modifying existing classes every time a feature is added
- Deep class hierarchies (max 3 levels)

#### Example: Pipeline Stages
- **Closed**: `_run_llm_stage()` method never changes
- **Open**: Add new stages by defining new `PipelineStage` objects
- **Benefit**: Adding a 4th LLM stage doesn't modify pipeline executor

### Liskov Substitution Principle (LSP)

#### Definition
Subclasses must be substitutable for their base classes without breaking behavior.

#### Rules
- **Contract**: Subclass must honor parent's interface and guarantees
- **No Surprises**: Subclass behavior shouldn't contradict parent expectations
- **Validation**: Child can be stricter on input, looser on output, but not vice versa

#### Anti-Patterns
- Subclass raising exception for method parent class supports
- Subclass changing return type in incompatible ways
- Silent behavior changes in overridden methods

### Interface Segregation Principle (ISP)

#### Definition
Clients shouldn't depend on interfaces they don't use. Prefer specific interfaces over general ones.

#### Rules
- **Separation**: Break large interfaces into smaller, focused ones
- **Minimal**: Expose only what clients need
- **Composability**: Combine small interfaces to build functionality

#### Anti-Patterns
- Monolithic interface that only 1 of 10 implementations uses
- Classes implementing interfaces with many unused methods

### Dependency Inversion Principle (DIP)

#### Definition
High-level modules shouldn't depend on low-level details. Both should depend on abstractions.

#### Rules
- **Abstraction**: Depend on interfaces/protocols, not concrete types
- **Injection**: Pass dependencies as parameters (constructor or method)
- **Testability**: Enables mocking for unit tests

#### Techniques
- **Constructor Injection**: Dependencies passed to `__init__`
- **Method Injection**: Dependencies passed to method calls
- **Factory Injection**: Injected factory creates dependencies as needed

#### Benefit
- Loose coupling: Can swap implementations without code changes
- Testability: Inject mock objects for testing
- Flexibility: Support multiple strategies/providers

---

## 5. Type Safety & Documentation

### Type Hints

#### Rules
- **All Public Methods**: Must have parameter and return type hints
- **Complex Private Methods**: Type hints for clarity (optional but recommended)
- **Consistency**: Use `Optional[T]` for nullable types, `Union[A, B]` for multiple types
- **Collection Types**: Prefer `list[T]`, `dict[K, V]` (3.9+) over `List[T]`, `Dict[K, V]`

#### Imports
```python
from typing import Optional, List, Dict, Union, Callable, Protocol, Any
```

#### Benefits
- IDE autocomplete and navigation
- Static type checking (mypy, Pylance)
- Self-documenting code
- Catch type mismatches before runtime

#### Annotations
- **Union Types**: `int | str` (3.10+) or `Union[int, str]`
- **Optional**: `T | None` (3.10+) or `Optional[T]`
- **Callables**: `Callable[[ParamType], ReturnType]`
- **Generics**: `TypeVar` for reusable generic code

### Docstrings

#### Google Style Format
```python
def method_name(param1: str, param2: int) -> bool:
    """Brief one-line description.
    
    Longer description explaining the method's behavior, edge cases,
    and context. Explain the "why" if non-obvious.
    
    Args:
        param1: Description of param1 and valid values
        param2: Description of param2; explain units or ranges
    
    Returns:
        Description of return value and when it's True/False/None
    
    Raises:
        ValueError: When param validation fails
        TimeoutError: When operation exceeds timeout threshold
    
    Example:
        >>> result = method_name("input", 42)
        >>> assert result is True
    """
```

#### Rules
- **Public Methods**: Always include docstring
- **Private Methods**: Docstring if logic is non-obvious
- **Classes**: Document purpose, key invariants, and usage
- **Modules**: Include module docstring explaining the file's purpose
- **Sync with Code**: Update docstring when behavior changes

### Inline Comments

#### Rules
- **Explain Why, Not What**: Code shows *what*, comments explain *why*
- **Avoid**: Comments that just restate code (`count += 1  # Add one to count`)
- **Valid**: Design decisions, trade-offs, non-obvious algorithms
- **Minimal**: Comments should be rare; code should be self-explanatory

#### Examples

**❌ Bad**:
```python
count = count + 1  # Add one to count
if x > 5:  # If x is greater than 5
    process(x)  # Process x
```

**✅ Good**:
```python
# Fallback inclusion: If we have few relevant entries in the second half
# of our scan window, include marginal entries to ensure comprehensiveness
is_in_fallback_zone = index > (total * 0.7)
```

---

## 6. Testing & Maintainability

### Testable Code Design

#### Principles
- **Pure Functions**: Same input → same output, no side effects
- **Dependency Injection**: Pass dependencies as parameters
- **Isolation**: Separate business logic from I/O (files, network, DB)
- **Mocking**: Enable mocking/stubbing external services

#### Patterns
- **Service Locator Anti-Pattern**: ❌ Objects finding dependencies globally
- **Dependency Injection Pattern**: ✅ Dependencies passed to constructor or method
- **Factory Pattern**: Create objects via factory methods for flexible instantiation

### Test Coverage

#### Targets
- **Business Logic**: 80%+ coverage on core algorithms
- **Utilities**: 100% coverage on helper functions (pure functions, low complexity)
- **Integration**: Separate integration tests from unit tests (slower, test real systems)
- **Edge Cases**: Test boundaries, None values, empty collections, large inputs

#### Avoid
- Testing private implementation details (test public API instead)
- 100% coverage requirement (diminishing returns; focus on critical paths)
- Brittle tests that break on harmless refactorings

### Test Organization

#### Naming
```python
def test_<unit>_<scenario>_<expectation>():
    """e.g., test_filter_entries_with_noise_keywords_skips_entry"""
    pass
```

#### Structure (AAA Pattern)
```python
def test_example():
    # Arrange: Setup test data
    input_data = {"title": "Crossword Puzzle"}
    
    # Act: Call the function
    result = filter_entries([input_data])
    
    # Assert: Verify expectations
    assert len(result) == 0
```

#### Fixtures & Parametrization
- **Fixtures**: Reusable setup for multiple tests (don't repeat test data)
- **Parametrize**: Use `pytest.mark.parametrize` for multiple scenarios
- **Factories**: Create test objects via factory functions

---

## 7. Naming Conventions

### Python Standards (PEP 8)

#### Variables & Constants
- **snake_case**: `my_variable`, `feed_entries`, `get_relevance_score()`
- **UPPERCASE_CONSTANTS**: `MAX_RETRIES = 3`, `DEFAULT_TIMEOUT = 30`
- **_private**: Leading underscore for internal implementation details

#### Classes
- **PascalCase**: `StrategicConsultant`, `FeedParser`, `EntryFilter`
- **Descriptive**: Class name should reflect its responsibility

#### Methods
- **snake_case**: `calculate_score()`, `fetch_feeds()`, `_is_valid_entry()`
- **Verbs**: Methods perform actions; use action names (`get_`, `fetch_`, `process_`)
- **Boolean Prefix**: `is_`, `has_`, `should_`, `can_` for methods returning bool

### Intention-Revealing Names

#### Rule
Code should read like prose; variable names should explain their purpose.

#### Examples
- **❌ Cryptic**: `d`, `x`, `proc_data()`
- **✅ Clear**: `feed_entries`, `relevance_score`, `process_feeds()`

#### Acronyms
- **Avoid**: Single-letter loop vars (`i`, `j` OK); no other single-letter names
- **Full Words**: `llm` is acceptable (known in context); `d` is not
- **Spelling**: Use correct spelling; abbreviations create confusion

### Project Consistency

#### Conventions
- **Case Style**: Match project conventions (not mixing camelCase and snake_case)
- **Abbreviations**: Standardize abbreviations (e.g., always `llm`, never `lm`)
- **Prefixes/Suffixes**: Consistent use of `_internal`, `_test`, `_deprecated`

---

## 8. Performance & Efficiency

### Profiling First

#### Rules
- **Measure**: Use profilers before optimizing (don't guess bottlenecks)
- **Tools**: `cProfile`, `line_profiler`, `memory_profiler`, flame graphs
- **Decision**: Only optimize if profiling shows it's slow

#### Trade-offs
- **Readability**: Prefer clear code unless profiling proves performance critical
- **Premature Optimization**: Evil (Knuth); avoid optimizing unproven bottlenecks
- **Documentation**: If optimization sacrifices clarity, document why in comments

### Common Optimizations

#### Data Structure Selection
- **Sets for Membership**: `O(1)` lookup vs lists `O(n)`
- **Caching**: Pre-compute expensive operations (e.g., lowercase strings)
- **Generators**: Use for large sequences (memory-efficient iteration)

#### Algorithmic Efficiency
- **Avoid O(n²)**: Nested loops over collections → Use sets or dicts
- **Early Exit**: Break/return from loops when condition met
- **Lazy Evaluation**: Compute only what's needed

#### I/O Optimization
- **Batch Operations**: Fewer API calls (batch size depends on limits)
- **Connection Pooling**: Reuse connections, don't create new ones per request
- **Async Operations**: Use async/await for concurrent I/O (network, file reads)

#### Avoid
- Micro-optimizations (e.g., `x += 1` vs `x = x + 1`)
- Trading clarity for nanoseconds
- Premature caching (cache only observed bottlenecks)

---

## 9. Code Organization & Structure

### File Organization

#### Directory Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── feed.py
│   │   └── entry.py
│   └── services/               # Business logic
│       ├── __init__.py
│       ├── feed_fetcher.py
│       ├── entry_filter.py
│       └── report_generator.py
├── tests/
│   ├── __init__.py
│   ├── test_feed_fetcher.py   # Parallel to src structure
│   └── test_entry_filter.py
├── requirements.txt            # Dependencies
├── .gitignore
├── .env.local                  # Secrets (GITIGNORE!)
└── README.md
```

### Import Organization
```python
# Standard library (alphabetical)
import asyncio
import logging
import re
from datetime import datetime
from typing import Optional, List

# Third-party (alphabetical)
import feedparser
from dotenv import load_dotenv

# Local (alphabetical)
import config
from logger_utils import log_token_usage
from report_utils import save_as_html
```

### Module Organization (Within Files)
1. **Module docstring**: Explain file's purpose
2. **Imports**: Standard → Third-party → Local
3. **Constants**: Module-level constants (UPPERCASE)
4. **Classes/Functions**: Public first, private after
5. **Main**: `if __name__ == "__main__":`

### Method Organization (Within Classes)
1. `__init__()`: Constructor
2. `__str__()`, `__repr__()`: String representations
3. Public methods: Core functionality
4. Private methods: Helper implementations
5. Properties: `@property` decorators
6. Class methods: `@classmethod`
7. Static methods: `@staticmethod`

---

## 10. Error Handling & Resilience

### Exception Handling

#### Rules
- **Specific Exceptions**: Catch specific exceptions, not bare `except:`
- **Re-raise**: Log then re-raise, don't swallow context
- **Custom Exceptions**: Create domain-specific exceptions for business logic
- **Validation**: Check inputs at API boundaries

#### Anti-Patterns
```python
# ❌ Bad: Bare except catches everything
try:
    operation()
except:
    pass

# ❌ Bad: Swallowing exceptions
try:
    operation()
except Exception:
    return default_value
```

#### Patterns
```python
# ✅ Good: Specific exception, logging context
try:
    result = api_call()
except TimeoutError as e:
    logger.error(f"API timeout for user_id={user_id}: {e}", exc_info=True)
    raise
except ConnectionError as e:
    logger.warning(f"Network issue, retrying: {e}")
    return retry_operation()
```

### Error Messages

#### Standards
- **Context**: Include what was being processed (user_id, item_name, etc.)
- **Expected vs. Actual**: Show what was expected vs. what happened
- **Actionable**: Help users understand and fix the issue
- **Sensitive Data**: Don't log secrets, passwords, API keys

#### Example
```python
# ❌ Vague
logger.error("Invalid input")

# ✅ Clear
logger.error(f"Invalid feed URL: {url}. Expected https:// or http://, got {scheme}")
```

### Circuit Breaker Pattern

#### When to Use
- **External Services**: API calls with high failure rates
- **Cascading Failures**: Prevent retry storms that cascade failures

#### Pattern
```python
# After N failures in time window T, fail-fast (don't retry)
# After recovery window, try one call; if succeeds, resume
```

### Graceful Degradation

#### Principle
Failures in optional features shouldn't crash the system.

#### Examples
- **Feed Timeout**: Skip that source, continue with others
- **API Rate Limit**: Use cached data, alert user
- **Logging Failure**: Continue operation, note that observability is compromised

#### Rule
- **Critical Failures**: Halt (unrecoverable errors)
- **Optional Features**: Log and continue

---

## 11. Async Programming Best Practices

### Async/Await Patterns

#### Rules
- **Mark Async**: Functions using `await` must be declared `async`
- **Minimize Blocking**: Use async libraries (aiohttp, not requests)
- **Avoid Mixing**: Don't mix sync/async without `run_in_executor()`
- **Context Managers**: Use `async with` for resource cleanup

#### Anti-Patterns
```python
# ❌ Mixing sync/async without adapter
async def fetch_data():
    data = requests.get(url)  # BLOCKING! Use aiohttp instead
    return data

# ❌ Fire-and-forget without error handling
asyncio.create_task(operation())  # No error handling!

# ❌ asyncio.run() inside async function
async def my_async_func():
    asyncio.run(other_async_func())  # Wrong! Use await
```

#### Patterns
```python
# ✅ Concurrent execution
import asyncio

async def fetch_multiple(urls):
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)  # Concurrent
    return results

# ✅ Timeout protection
try:
    result = await asyncio.wait_for(operation(), timeout=30)
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    raise

# ✅ Resource cleanup
async with aiohttp.ClientSession() as session:
    result = await session.get(url)
    return result  # Session closes automatically
```

### Structured Concurrency (Python 3.11+)

#### Pattern (Preferred over create_task)
```python
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(coro1())
        task2 = tg.create_task(coro2())
    # All tasks complete or exception raised
    return task1.result(), task2.result()
```

### Testing Async Code

#### Tools
- **pytest-asyncio**: `@pytest.mark.asyncio` decorator
- **Mocking**: `AsyncMock` for async functions
- **Fixtures**: `async_client`, `event_loop` fixtures

---

## 12. Version Control & Collaboration

### Commit Practices

#### Commit Messages
- **Format**: 50-char summary, blank line, detailed body
- **Tense**: Imperative ("Add feature" not "Added feature")
- **Scope**: One logical change per commit (atomic)
- **Reference**: Link to issue/PR (`Fixes #123`, `Relates to #456`)

#### Example
```
Fix token overflow in feed processing

- Reduce MAX_SUMMARY_WORDS from 200 to 100
- Add token budget check before LLM calls
- Log token usage per stage for visibility

Fixes #42
```

### Branching Strategy

#### Branch Naming
- **Features**: `feature/add-reviewer-stage`
- **Fixes**: `fix/token-budget-overflow`
- **Refactoring**: `refactor/extract-feed-parser`
- **Avoid**: `wip`, `test`, `temp` (non-descriptive)

#### Workflow (Git Flow variant)
1. Create feature branch from `main`
2. Commit atomically (one logical change per commit)
3. Push and create PR
4. Review and merge to `main`

### `.gitignore` Standards

#### Must Include
```
.env.local              # Secrets
.env                    # Local overrides
*.log                   # Logs
__pycache__/            # Python cache
*.pyc, *.pyo
*.egg-info/
dist/, build/           # Build artifacts
.venv/, myenv/          # Virtual environments
reports/                # Generated reports
.DS_Store               # macOS
.vscode/                # IDE settings (optional, use .editorconfig instead)
```

### Dependency Management

#### Requirements Files
- **Format**: Use `requirements.txt` with pinned versions
- **Pinning**: `package==1.2.3` (not `package>=1.2.3`)
- **Separate Files**: `requirements-dev.txt` for test/dev dependencies
- **Tools**: Use `pip freeze` to generate, `pip install -r` to install

#### Example
```
# requirements.txt
feedparser==6.0.12
aiohttp==3.9.1
python-dotenv==1.0.0

# requirements-dev.txt
pytest==7.4.0
pytest-asyncio==0.21.0
mypy==1.5.0
flake8==6.1.0
```

### Code Review Standards

#### What Reviewers Check
- **Logic**: Does the code do what the PR claims?
- **Tests**: New code should have tests (70%+ coverage)
- **Style**: Adherence to SOLID, KISS, DRY principles
- **Docs**: Public methods have docstrings
- **Types**: Parameter and return types annotated
- **Security**: No secrets, SQL injection, auth issues
- **Performance**: No obvious O(n²) algorithms (unless justified)

#### What Reviewers Approve
- Logic correctness
- Test coverage (70%+)
- Code style adherence
- Documentation clarity
- No regressions in existing tests

---

## Code Review Checklist for Generated/Changed Code

Before accepting Copilot-generated code or submitting for review:

### Correctness
- [ ] Code does what the request asked
- [ ] No logic errors or off-by-one mistakes
- [ ] Edge cases handled (None, empty collections, invalid input)
- [ ] All tests pass locally
- [ ] No regressions in existing functionality

### Style & Readability
- [ ] No unused imports
- [ ] No duplicate code (DRY applied)
- [ ] Magic numbers extracted to named constants
- [ ] Variable names are clear and descriptive
- [ ] Max 3 levels of nesting (guard clauses used)
- [ ] Methods < 30 lines
- [ ] Follows PEP 8 (snake_case, imports organized)

### Type Safety & Docs
- [ ] Type hints on all public methods
- [ ] Docstrings for public methods (Google style)
- [ ] Complex private methods documented
- [ ] Inline comments explain *why*, not *what*
- [ ] No ambiguous type hints (use Union, Optional)

### Testing
- [ ] New code has unit tests (70%+ coverage)
- [ ] Tests are focused and readable
- [ ] No hardcoded test data (use fixtures)
- [ ] Edge cases tested (boundaries, None, empty)
- [ ] Test names describe scenario + expectation

### Error Handling
- [ ] No bare `except:` clauses
- [ ] Specific exceptions caught
- [ ] Errors logged with context
- [ ] No swallowed exceptions

### Performance
- [ ] No obvious O(n²) operations
- [ ] Efficient data structures (sets for membership, not lists)
- [ ] No premature optimization
- [ ] Async used for concurrent operations

### Architecture
- [ ] Single Responsibility (one reason to change)
- [ ] Dependencies injected, not hardcoded
- [ ] YAGNI applied (no speculative code)
- [ ] Cohesive modules (related functionality grouped)
- [ ] Loose coupling (can swap implementations)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation at API boundaries
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize output)
- [ ] CSRF protection (if web app)

---

## Language-Specific Tips

### Python 3.8+

#### Type Hints
```python
from typing import Optional, Union, List, Dict, Callable

def process(items: list[str], count: int = 5) -> Optional[str]:
    """Python 3.9+ allows list[T] instead of List[T]."""
    pass
```

#### F-Strings
```python
# ✅ Preferred for string interpolation
name = "World"
message = f"Hello, {name}!"
logger.info(f"Processing user_id={user_id}, status={status}")
```

#### Dict Merge (3.9+)
```python
# ✅ Preferred
merged = {**dict1, **dict2}

# Instead of
merged = dict1.copy()
merged.update(dict2)
```

#### Match/Case (3.10+)
```python
# ✅ Use for complex conditionals
match status:
    case "active":
        process_active()
    case "pending":
        process_pending()
    case _:
        process_default()
```

### Virtual Environments

#### Setup
```bash
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
myenv\Scripts\activate      # Windows
pip install -r requirements.txt
```

#### Never Commit
- Virtual environment directory (huge, system-specific)
- `.env.local` files (contain secrets)
- `*.egg-info/`, `dist/`, `build/` directories

---

## Integration with Copilot

### When Generating Code

**Always Request**:
- Type hints on all parameters and returns
- Docstrings for public methods
- Unit tests with 70%+ coverage
- Error handling with specific exceptions

**Always Review**:
- Unused imports (remove them)
- Magic numbers (extract to constants)
- Complex conditionals (extract to boolean methods)
- Code duplication (refactor to helpers)

**Always Refactor**:
- Long methods (split into smaller units)
- Deep nesting (use early returns)
- Complex list comprehensions (use explicit loops)

### Acceptable Generated Code Patterns
- ✅ Boilerplate (type hints, imports, docstring templates)
- ✅ Tested algorithms (sorting, filtering, etc.)
- ✅ API call wrappers
- ✅ Data transformation pipelines
- ✅ Logging and observability

### Problematic Patterns (Always Verify)
- ❌ Hardcoded magic numbers
- ❌ Bare `except:` clauses
- ❌ Complex nested logic
- ❌ Missing error handling
- ❌ No test coverage
- ❌ Swallowed exceptions

---

## Quick Reference: Red Flags in Code Review

| Red Flag | Action |
|----------|--------|
| Unused imports | Remove immediately |
| Cryptic variable names | Rename or reject |
| Bare `except:` | Require specific exceptions |
| Magic numbers | Extract to named constants |
| Deep nesting (>3) | Request refactor with guard clauses |
| Methods >50 lines | Request decomposition |
| No tests | Require 70%+ coverage |
| No type hints | Add type annotations |
| No docstring (public) | Add Google-style docstring |
| Copy-pasted logic | Extract to helper method |
| Swallowed exceptions | Require logging + re-raise |
| Hardcoded secrets | Reject immediately (security) |
| Comments explaining *what* | Request self-documenting code |

---

## Summary

**Code Quality = Readability + Testability + Maintainability**

Prioritize in this order:
1. **Correctness**: Does it work and handle errors?
2. **Clarity**: Can others understand it in 5 minutes?
3. **Testability**: Can it be unit tested in isolation?
4. **Performance**: Is it fast enough (measured, not guessed)?
5. **Cleverness**: After all else is satisfied, optimize

**Remember**: Code is read 10x more than written. Optimize for readers, not writers.

---

**Last Updated**: December 2025  
**Python Versions**: 3.8+  
**Audience**: Senior Engineers, Code Reviewers, Development Teams

