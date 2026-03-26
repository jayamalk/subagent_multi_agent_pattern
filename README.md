# HelloSubAgents

FastAPI + LangGraph demo with a supervisor agent that delegates to:
- A calendar agent with a reflection node that critiques and revises its final response.
- An email agent for sending reminders.

## Project Layout

- `agents/` — agent implementations (calendar, email, supervisor, reflection factory)
  - `AGENT_STANDARDS.md` — standards and best practices for creating agents
- `state/` — shared state types for agents
- `config/` — runtime configuration (Ollama settings)
- `tests/` — trajectory evals
- `guardrails/` — custom middleware and guardrails
- `openspec/` — change documentation and archived changes

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                         │
│                         (main.py)                                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    GET /          GET /health       POST /assistant
   (status)      (config info)     (user request)
                                        │
                                        ▼
                    ┌───────────────────────────────────┐
                    │   Supervisor Agent                │
                    │   (subagent.py)                   │
                    │                                   │
                    │  - Routes requests to sub-agents  │
                    │  - Manages coordination           │
                    └──┬──────────────────────────────┬─┘
                       │                              │
          ┌────────────┴────────────┐               │
          │                         │               │
          ▼                         ▼               │
    ┌──────────────┐         ┌──────────────┐      │
    │ Calendar     │         │   Email      │      │
    │ Agent        │         │   Agent      │      │
    │              │         │              │      │
    │ Tools:       │         │ Tools:       │      │
    │ - schedule   │         │ - send_email │      │
    │   event      │         │              │      │
    │              │         │              │      │
    └──┬───────────┘         └────┬─────────┘      │
       │                          │                │
       ▼                          ▼                ▼
    ┌─────────────────────────────────────────────────┐
    │          Middleware Stack (All Agents)          │
    ├─────────────────────────────────────────────────┤
    │ 1. Guardrails                                   │
    │    - EmailApprovalGuardrail (requires approval)│
    │    - ContentFilterMiddleware (block keywords)   │
    │                                                 │
    │ 2. PII Protection                               │
    │    - Redact emails                              │
    │    - Mask credit cards                          │
    │    - Block API keys                             │
    │                                                 │
    │ 3. Reflection (Calendar Agent Only)             │
    │    - Critique responses                         │
    │    - Revise if needed                           │
    └──────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    ┌─────────────────┐         ┌──────────────┐
    │  LLM Model      │         │  Tool        │
    │  (via Ollama)   │         │  Execution   │
    │                 │         │              │
    │ Configured via: │         │ - Database   │
    │ OLLAMA_MODEL    │         │ - Email API  │
    │ OLLAMA_BASE_URL │         │ - External   │
    └─────────────────┘         │   services   │
                                └──────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                         Configuration System                        │
├─────────────────────────────────────────────────────────────────────┤
│ .env File (loaded by config/ollama_config.py)                      │
│ ┌─────────────────────────────────────────────────────────────┐    │
│ │ - OLLAMA_MODEL: LLM model name                             │    │
│ │ - OLLAMA_BASE_URL: Ollama server URL                       │    │
│ │ - EMAIL_GUARDRAIL_AUTO_APPROVE: true/false for approval    │    │
│ │ - LANGSMITH_*: LangSmith tracing configuration            │    │
│ └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                    Development & Documentation                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ OpenSpec Change Management          Agent Standards                │
│ ├── changes/                         └── AGENT_STANDARDS.md        │
│ │   └── {new-change}/                   - Agent anatomy            │
│ │       ├── .openspec.yaml              - Tool standards           │
│ │       ├── proposal.md                 - Middleware patterns      │
│ │       ├── tasks.md                    - Testing guides           │
│ │       └── design.md                                              │
│ │                                                                   │
│ └── archive/                                                       │
│     └── {date}-{completed-change}/                                 │
│         ├── proposal.md                                            │
│         ├── tasks.md                                               │
│         └── ARCHIVE_SUMMARY.md                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Example: "Schedule meeting and send email"

```
User Request
    │
    ├─► Supervisor Agent
    │   ├─► Parses request
    │   ├─► Identifies tasks: schedule + email
    │   │
    │   ├─► Delegates to Calendar Agent
    │   │   ├─► Middleware checks
    │   │   ├─► LLM processes with schedule_event tool
    │   │   └─► Returns scheduled event
    │   │
    │   └─► Delegates to Email Agent
    │       ├─► EmailApprovalGuardrail intercepts
    │       ├─► Requests/auto-approves send_email
    │       ├─► PII Middleware protects email addresses
    │       ├─► LLM processes with send_email tool
    │       └─► Returns confirmation
    │
    └─► Response to User
        "Meeting scheduled for March 25 at 14:00"
        "Email reminder sent to alice@example.com"
```

### Setup

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Install dependencies:
   - `uv sync`
3. Set up Ollama locally:
   - Install Ollama from https://ollama.com and start the Ollama service.
   - Pull a model that matches `OLLAMA_MODEL` in `.env`, for example:
     - `ollama pull qwen3.5:latest`
   - If you change the model name in `.env`, pull that model with `ollama pull <model>`.
4. Configure LangSmith prompts:
   - run `uv run python scripts/push_prompts.py` to upload the default prompts.

## Run the API

```
uv run uvicorn main:app --reload
```

The API exposes:
- `GET /` for basic status
- `GET /health` for config info
- `POST /assistant` for agent responses

## Run Tests

```
uv run python -m pytest -q
```

Trajectory evals require a reachable Ollama server and a locally available model.

## Run LangGraph Dev

```
uv run langgraph dev --allow-blocking
```

This uses `langgraph.json` and the `assistant` graph entrypoint.

