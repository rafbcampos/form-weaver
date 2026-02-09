# Interview Server

Python backend for the conversational interview system. Built with FastAPI and DSPy.

## Setup

```bash
# Create virtual environment and install
uv venv
uv pip install -e ".[dev]"

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Running

```bash
# Development server with auto-reload
.venv/bin/python -m uvicorn interview.main:app --reload

# Or using the module directly
.venv/bin/python -m interview.main
```

The server starts on <http://localhost:8000>. API docs at <http://localhost:8000/docs>.

## Configuration

Environment variables:

| Variable            | Default                                | Description                     |
| ------------------- | -------------------------------------- | ------------------------------- |
| `LLM_MODEL`         | `anthropic/claude-sonnet-4-5-20250929` | LLM model identifier            |
| `ANTHROPIC_API_KEY` | --                                     | Required for Anthropic models   |
| `OPENAI_API_KEY`    | --                                     | Required for OpenAI models      |
| `CORS_ORIGINS`      | `http://localhost:5173`                | Comma-separated allowed origins |
| `HOST`              | `0.0.0.0`                              | Server bind address             |
| `PORT`              | `8000`                                 | Server port                     |

## DSPy Modules

### InterviewStep (Primary)

The core data collection module. Given the schema, collected data, missing fields, and conversation history, it generates structured form elements — typed inputs (`text`, `integer`, `email`, etc.), radio buttons, selects, checkboxes, textareas, and arrays — that enforce validation rules and correct data types through UI constraints. Each step produces a conversational `TextBlock` plus a `FormBlock` containing elements for the next 3-5 fields. This forms-first approach ensures data quality by design: the user interacts with purpose-built UI elements rather than typing free text.

### TextDataExtractor (Supplementary)

Handles the edge case where a user types a free-text message instead of filling the form. Maps natural language ("I'm 25 and work at Acme Corp") to schema field paths (`personal.age: 25`, `employment.company: "Acme Corp"`). Extracted values are validated against schema rules before being merged into session data — invalid extractions (e.g., `age=15` when the minimum is 18) are discarded so that `InterviewStep` can re-collect them via proper form elements.

Both modules use `dspy.ChainOfThought` and can be optimized using the CLI tool.

## Engine

### Orchestrator

The `InterviewOrchestrator` manages the interview lifecycle:

- `start(schema, initial_data)` -- Creates a session and generates the first step
- `submit(session_id, request)` -- Handles form submissions or text messages
- Validates submitted data, merges with session state, checks completion
- Supports optional injection of pre-optimized DSPy modules

### Schema Analyzer

- `flatten_schema()` -- Converts nested schema to flat dot-notation paths
- `get_missing_fields()` -- Returns required fields not yet collected (respects conditions)
- `is_complete()` -- Checks if all required fields are valid

### Conditions

Fields can be conditionally shown/hidden based on other field values:

```json
{
  "conditions": [
    { "field": "personal.marital_status", "op": "eq", "value": "married" }
  ]
}
```

Supported operators: `eq`, `neq`, `in`, `not_in`, `gt`, `lt`, `gte`, `lte`, `exists`, `not_exists`.

## CLI Tool

### Generate Training Data

Generates synthetic interview examples by simulating complete data records:

```bash
.venv/bin/python -m interview.cli generate \
  --schema ../schemas/user_profile.json \
  --count 10 \
  --output data/examples/user_profile.json
```

For each synthetic record, generates:

- **First turn examples** -- empty state, all fields missing
- **Intermediate examples** -- partially collected data at various stages
- **Near-completion examples** -- 1-2 fields remaining
- **Text extraction examples** -- natural language messages with expected field mappings

### Optimize Prompts

Runs a DSPy optimizer to improve module prompts:

```bash
.venv/bin/python -m interview.cli optimize \
  --module interview_step \
  --examples data/examples/user_profile.json \
  --optimizer miprov2 \
  --max-demos 4 \
  --num-trials 15
```

Optimizers: `miprov2` (default), `bootstrap`, `gepa`.

### Optimizers

- **BootstrapFewShot** (`bootstrap`): Runs the program on training examples and keeps successful traces as few-shot demos. Fast, no search, good baseline.
- **MIPROv2** (`miprov2`, default): Uses Bayesian optimization (Optuna) to jointly search over candidate instruction phrasings and few-shot demo selections across `num_trials` trials. Most thorough but requires more LLM calls.
- **GEPA** (`gepa`): Generates grounded instructions from successful examples and optimizes the prompt. Middle ground between bootstrap simplicity and MIPROv2's search.

### Evaluate

Scores a program (optimized or baseline) against a dataset:

```bash
.venv/bin/python -m interview.cli evaluate \
  --module interview_step \
  --examples data/examples/user_profile.json \
  --program data/optimized/interview_step.json
```

### Metrics

**InterviewStep** is scored on:

- Binding coverage (0.4) -- fraction of expected fields present in generated form elements
- Structural validity (0.3) -- correct block kinds, valid bindings, starts with text
- Conciseness (0.3) -- asks for 2-5 fields, avoids already-collected fields

**TextDataExtractor** is scored on:

- Extraction accuracy (0.6) -- correct key-value pairs, penalizes spurious extractions
- Type correctness (0.4) -- extracted values match expected types

### Server Integration

Optimized programs saved to `data/optimized/` are automatically loaded at server startup:

```
data/optimized/interview_step.json    -> Loaded into InterviewOrchestrator
data/optimized/text_extractor.json    -> Loaded into InterviewOrchestrator
```

## Testing

```bash
# Run all checks
.venv/bin/ruff check src/ tests/     # Linting (50+ rule categories)
.venv/bin/mypy src/                   # Strict type checking
.venv/bin/python -m pytest tests/ -q  # 118 unit tests
```
