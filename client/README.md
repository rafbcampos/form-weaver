# Interview Client

React frontend for the conversational interview system. Built with Vite, TypeScript, and Tailwind CSS.

## Setup

```bash
pnpm i
```

## Running

```bash
# Development server (port 5173)
pnpm dev

# Production build
pnpm build

# Preview production build
pnpm preview
```

The dev server proxies `/api` requests to `http://localhost:8000` (the backend server).

## How It Works

### Interview Flow

1. `App.tsx` loads a schema (currently `schemas/user_profile.json`) and renders the `Interview` component.
2. `Interview` uses the `useInterview` hook to manage session state.
3. On mount, it calls `POST /api/interview/start` with the schema.
4. The server returns UI blocks (text + form elements) which render as a chat message.
5. **Forms are the primary data collection path.** The server's `InterviewStep` module generates structured form elements (typed inputs, selects, radios, checkboxes, textareas, arrays) that enforce validation rules and correct data types through UI constraints. Users interact with these purpose-built elements to provide data.
6. **Free-text input is supplementary.** Users can type messages in `MessageInput` as a fallback. The server's `TextDataExtractor` attempts to parse the text into schema fields, but extracted values are validated before being accepted — invalid extractions are discarded and re-collected via forms.
7. Each submission returns the next set of UI blocks until all required fields are collected.

### UI Blocks

The server returns a list of `UIBlock` objects that the client renders:

- **TextBlock** -- Conversational text from the assistant
- **FormBlock** -- Contains form elements:
  - `input` (text, integer, float, email, date, phone)
  - `select` (dropdown)
  - `radio` (radio button group)
  - `checkbox`
  - `textarea`
  - `array` (dynamic list of field groups)

### State Management

- `useInterview` -- Manages the session lifecycle: messages array, loading/error states, current data, completion status. Exposes `start()`, `submitFormData()`, and `sendTextMessage()`.
- `useFormBlock` -- Manages form-level state: field values keyed by binding path, handles form submission.

### Client-Side Validation

The `lib/` directory mirrors server-side logic for responsive UX:

- `validation.ts` -- Validates fields against schema rules before submission
- `conditions.ts` -- Shows/hides conditional fields based on current form values
- `bindings.ts` -- Utilities for working with dot-notation field paths

## Quality Checks

```bash
npx tsc --noEmit                           # Type checking (strict mode)
npx oxlint .                               # Linting
npx prettier --check 'src/**/*.{ts,tsx}'   # Format checking
```
