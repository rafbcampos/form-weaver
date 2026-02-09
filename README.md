# FormWeaver: Conversational Interview System

A schema-driven conversational interview system that collects structured data through natural dialogue. An LLM orchestrates the conversation, dynamically generating UI form elements and extracting data from free-text messages.

## Architecture

```
formweaver/
├── client/          React + Vite + Tailwind frontend
├── server/          Python + FastAPI + DSPy backend
├── schemas/         Shared JSON schema definitions
```

### How It Works

1. A **JSON schema** defines the fields to collect (types, validation rules, conditional visibility, nested objects, arrays).
2. The **server** uses [DSPy](https://dspy.ai/) to power two LLM modules:
   - **InterviewStep** (primary) generates structured form elements — typed inputs, radio buttons, selects, checkboxes, textareas, and arrays — that enforce validation rules and correct data types through UI constraints. This is the primary data collection mechanism: the LLM decides which fields to ask for and produces the exact form elements to collect them.
   - **TextDataExtractor** (supplementary) handles the edge case where a user types a free-text message instead of using the form. Extracted values are validated against schema rules before being accepted — invalid extractions are discarded so the next InterviewStep can re-collect them via proper form elements.
3. The **client** renders the UI blocks as an interactive chat interface. Forms are the primary interaction path; free-text input is available as a fallback.
4. The **CLI tool** enables DSPy prompt optimization -- generating synthetic training data, running optimizers, and evaluating results.

### Data Flow

```
User <-> React Client <-> FastAPI Server <-> DSPy/LLM
                              |
                        Session Store
                        (in-memory)
```

## Prerequisites

- Python >= 3.11
- Node.js >= 18
- An LLM API key (Anthropic or OpenAI)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Quick Start

### 1. Install dependencies

```bash
# Root (git hooks)
pnpm install

# Server
cd server
uv venv
uv pip install -e ".[dev]"
cd ..

# Client
cd client
pnpm install
cd ..
```

### 2. Set environment variables

```bash
# For Anthropic (default)
export ANTHROPIC_API_KEY=sk-ant-...

# Or for OpenAI
export LLM_MODEL=openai/gpt-4o
export OPENAI_API_KEY=sk-...
```

### 3. Run the development servers

```bash
# Terminal 1: Backend
cd server && .venv/bin/python -m uvicorn interview.main:app --reload

# Terminal 2: Frontend
cd client && pnpm dev
```

Open <http://localhost:5173> to start an interview.

## Schema Format

Schemas are JSON files that define the fields to collect. See `schemas/user_profile.json` for a complete example.

```json
{
  "fields": {
    "name": {
      "type": "string",
      "label": "Full Name",
      "validation": [{ "type": "required" }]
    },
    "age": {
      "type": "integer",
      "label": "Age",
      "validation": [{ "type": "required" }, { "type": "min", "param": 18 }]
    }
  }
}
```

Supported field types: `string`, `text`, `integer`, `float`, `boolean`, `date`, `enum`, `object`, `array`.

Features:

- **Validation rules**: required, min, max, min_length, max_length, pattern, one_of
- **Conditional fields**: Show/hide fields based on other field values (eq, neq, in, gt, lt, exists, etc.)
- **Nested objects**: Group related fields into objects with dot-notation paths
- **Arrays**: Collect lists of structured items (e.g., children with name and age)

## DSPy Prompt Optimization CLI

Generate training data, optimize prompts, and evaluate results:

```bash
cd server

# Generate synthetic training examples from a schema
.venv/bin/python -m interview.cli generate \
  --schema ../schemas/user_profile.json \
  --count 10 \
  --output data/examples/user_profile.json

# Optimize the InterviewStep module
.venv/bin/python -m interview.cli optimize \
  --module interview_step \
  --examples data/examples/user_profile.json \
  --optimizer bootstrap \
  --max-demos 4

# Evaluate (optimized vs baseline)
.venv/bin/python -m interview.cli evaluate \
  --module interview_step \
  --examples data/examples/user_profile.json \
  --program data/optimized/interview_step.json
```

Optimized programs are automatically loaded by the server at startup when present in `server/data/optimized/`.

## Quality Tooling

### Pre-commit Hooks

Every commit runs automatically:

- **gitleaks** -- secret detection on staged files
- **lint-staged** -- ruff (Python), prettier + oxlint (TypeScript)
- **tsc --noEmit** -- TypeScript type checking
- **ruff check + mypy + pytest** -- Python linting, types, tests
- **commitlint** -- conventional commit message format

### Manual Checks

```bash
# Server (Python)
cd server
.venv/bin/ruff check src/ tests/    # Linting
.venv/bin/mypy src/                  # Type checking
.venv/bin/python -m pytest tests/ -q # Tests

# Client (TypeScript)
cd client
npx tsc --noEmit                           # Type checking
npx oxlint .                               # Linting
npx prettier --check 'src/**/*.{ts,tsx}'   # Formatting
```

### Commit Message Convention

Uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user authentication
fix: resolve session timeout bug
docs: update API documentation
refactor: extract validation logic
test: add schema analyzer edge cases
```

## API Endpoints

| Method | Path                         | Description                           |
| ------ | ---------------------------- | ------------------------------------- |
| POST   | `/api/interview/start`       | Start a new interview session         |
| POST   | `/api/interview/{id}/submit` | Submit form data or text message      |
| GET    | `/api/interview/{id}/status` | Get session status and missing fields |
