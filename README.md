# HelloSubAgents

FastAPI + LangGraph demo with a supervisor agent that delegates to:
- A calendar agent with a reflection node that critiques and revises its final response.
- An email agent for sending reminders.

## Project Layout

- `agents/` — agent implementations (calendar, email, supervisor, reflection factory)
- `state/` — shared state types for agents
- `config/` — runtime configuration (Ollama settings)
- `tests/` — trajectory evals

## Setup

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Install dependencies:
   - `uv sync`

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
uv run langgraph dev
```

This uses `langgraph.json` and the `assistant` graph entrypoint.
