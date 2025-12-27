# BeeAI Strategic Intelligence Agent - Copilot Instructions

## Architecture Overview

This is a **three-tier LLM pipeline** that converts RSS news feeds into strategic market analysis reports. It uses the BeeAI framework (a multi-agent orchestration system) to coordinate specialized LLM models for different reasoning tasks.

### Data Flow
1. **Feed Aggregation** → Raw RSS feeds from 10 strategic sources (McKinsey, MIT Tech Review, CoinTelegraph, etc.)
2. **Distillation** (Llama 8B) → Strips news to facts/keywords; groups by topic
3. **Strategic Synthesis** (Groq 120B) → Builds structured roadmap with project ideas + financial allocation
4. **Peer Review** (Gemini Flash) → Critiques viability; identifies highest-conviction opportunities
5. **HTML Report** → Saves styled markdown-to-HTML with token usage tracking

## Key Components & Their Responsibilities

### `main_local.py` - Core Pipeline (StrategicConsultant Class)
- **Intelligence Source Configuration**: Maintains curated RSS feed dictionary with specific URLs known to be active
- **Smart Content Filtering**: Dual-keyword system (VALUABLE_KEYWORDS + NOISE_KEYWORDS) to eliminate low-signal news; ~15 feeds checked, max 5 relevant entries per source
- **LLM Model Initialization**: Creates three separate ChatModel instances with distinct temperatures (0, 0.2, 0.1) for different reasoning types
- **Pipeline Execution**: Async three-stage processing with middleware logging via BeeAI's Logger/TrajectoryMiddleware
- **Token/Cost Tracking**: Logs all model calls to `agent_usage.log` and console summary

### `config.py` - Model Configuration
- Maps model shortcuts to BeeAI provider syntax (e.g., `"groq:llama-3.1-8b-instant"`)
- Loads API keys from `.env.local` using `python-dotenv`
- **Critical Detail**: Uses Groq for fast/cheap distillation and analysis; Gemini for review (cost optimization pattern)

### `logger_utils.py` - Observability & Cost Tracking
- **Polymorphic Extraction**: Handles both `RequirementAgentOutput` (with `.state` object) and `ChatModelOutput` (direct access)
- **Token Breakdown**: Separately tracks prompt, completion, cached, and total tokens
- **Cost Aggregation**: Sums USD cost across multiple model calls; key for budgeting multi-model pipelines

### `report_utils.py` - HTML Generation
- Converts markdown (with tables/code) to styled HTML using the `markdown` library with `tables` extension
- Generates timestamped reports in `reports/` directory for archival

## Development Patterns & Conventions

### Prompt Engineering
- **Structured Output Templates**: Each LLM receives a detailed MARKDOWN template with explicit sections (see `get_strategist_instructions()`)
- **Persona-Based Prompting**: Different roles for each model (Data Distiller, Senior Strategist, Venture Capitalist) to constrain reasoning
- **Multi-step Context Building**: Distiller output fed as input to Analyst, who feeds to Reviewer (chaining with context carry-over)

### Configuration & Model Selection
- **Temperature Tuning**: Distillation (0 = deterministic) → Analysis (0.2 = exploratory) → Review (0.1 = critical)
- **Provider Economics**: Groq models for speed/cost on known good problems; Gemini for reasoning on variable data
- **Environment Loading**: `.env.local` (not `.env`) - local development pattern; never commit API keys

### Content Processing
- **HTML Cleaning Regex**: Strips tags, unescapes entities, normalizes whitespace to reduce token consumption
- **Keyword Scoring**: Entries ranked by keyword overlap; low-signal entries (crossword, recipe, horoscope) filtered hard
- **Truncation**: Summaries capped to MAX_SUMMARY_WORDS (100) per entry to control prompt size

### Token & Cost Discipline
- Dual logging: Console (human-readable emoji summary) + File (JSON for analysis)
- Token metrics: separate prompt/completion/cached tracking (important for observing cache hit rates)
- Final aggregation across all 3 model calls to show total pipeline cost

## Critical Developer Workflows

### Running the Agent
```bash
# Activate venv
myenv\Scripts\activate

# Ensure .env.local exists with API keys:
# GROQ_API_KEY=xxx
# GOOGLE_API_KEY=xxx (for Gemini)

# Run pipeline
python main_local.py
```

### Monitoring & Debugging
- **BeeAI Logger TRACE level** in `run_pipeline()` captures all event emissions (middleware observations)
- **Debug output**: Distilled data printed mid-pipeline to catch filtering issues
- **Log file**: `agent_usage.log` contains timestamped JSON for retrospective cost analysis
- **Generated reports**: `reports/Strategy_Report_YYYYMMDD_HHMMSS.html` - always generated even on partial success

### Adding New RSS Sources
1. Add to `RSS_SOURCES` dict in StrategicConsultant.__init__ with active URL
2. Adjust VALUABLE_KEYWORDS/NOISE_KEYWORDS if source domain has domain-specific terms
3. Verify feedparser can parse it: wrap in try/except handles timeouts/malformed feeds

### Modifying LLM Behavior
- Edit prompt templates in `get_distiller_instructions()`, `get_strategist_instructions()`, `get_reviewer_instructions()`
- Adjust temperature in ChatModelParameters() if output is too deterministic or too random
- Change MAX_ENTRIES_PER_SOURCE (currently 5) if reports feel repetitive or sparse

## External Dependencies & Integration Points

### BeeAI Framework
- **Version**: 0.1.74 (pinned in requirements.txt)
- **Key APIs Used**:
  - `ChatModel.from_name()` - model instantiation with provider routing
  - `.run([messages])` - async execution with middleware attachment
  - `.observe(lambda emitter: ...)` - event subscription for logging (middleware pattern)
  - `SystemMessage/UserMessage` - message types for role separation
- **Note**: Framework handles provider auth via API key env vars (GROQ_API_KEY, GOOGLE_API_KEY, etc.)

### External Services
- **Groq API** (via BeeAI): Llama 8B, GPT-OSS-120B models for speed
- **Google Gemini API** (via BeeAI): Flash model for final review
- **RSS Feeds**: 10 curated sources (McKinsey, Forrester, MIT, Hacker News, etc.) - assumes internet connectivity

### Data Dependencies
- **No database**: All data ephemeral (feeds → processing → HTML report)
- **No file persistence** except HTML reports and logs
- **Async I/O**: feedparser.parse() is synchronous but wrapped in async context; no blocking issues expected

## Common Pitfalls & Gotchas

1. **Missing .env.local**: Agent will fail silently on API calls if keys missing; always check stdout for "Error" messages
2. **Inactive RSS URLs**: Feed sources occasionally go down; wrapped in try/except, but affects report comprehensiveness
3. **Token Budget Overflow**: With 3 LLM calls, a single pass can cost $0.01-0.05 depending on prompt size; monitor `agent_usage.log`
4. **HTML Entity Escaping**: Never pipe markdown output directly to HTML without markdown library (see report_utils.py for why)
5. **Temperature Tuning**: Temperature=0 can produce repetitive outputs if prompt is too generic; temperature too high causes incoherence in structured tasks

## Code Style & Naming Conventions

- **Turkish Comments**: Some inline comments in Turkish (legacy from course); English preferred for new code
- **Camel Case**: Methods (`get_strategist_instructions`), snake_case for functions (`log_token_usage`)
- **Emoji Prefixes**: Console logs use 📡, 🚀, 📊, etc. for visual scanning; not in logs files
- **Prompt Constant Strings**: Defined as methods (not module constants) so they stay close to usage
- **Error Handling**: Minimal try/except; failures logged but don't halt pipeline (graceful degradation)

## Adding Features

### To Add a New Analysis Stage
1. Create a new `get_new_stage_instructions()` method with role + template
2. Initialize a new ChatModel in `__init__` with appropriate model + temperature
3. Add async call in `run_pipeline()` with `.observe()` middleware
4. Log output via `log_token_usage()`
5. Append result to `full_report` markdown

### To Change Report Format
- Modify markdown template inside `get_strategist_instructions()` (defines section structure)
- Adjust HTML styling in `report_utils.py` if aesthetic changes needed
- Keep markdown valid for proper HTML generation (no unescaped special chars)

---

**Last Updated**: December 2025  
**Framework Version**: BeeAI 0.1.74  
**Python Version**: 3.8+
