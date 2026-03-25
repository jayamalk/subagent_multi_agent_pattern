from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from langchain_core.prompts import BasePromptTemplate
from langsmith import Client

DEFAULT_PROMPT_NAMES = {
    "supervisor": "hellosubagents-supervisor",
    "calendar_system": "hellosubagents-calendar-system",
    "calendar_reflection": "hellosubagents-calendar-reflection",
    "calendar_revision": "hellosubagents-calendar-revision",
    "email_system": "hellosubagents-email-system",
}


def _load_local_env() -> None:
    """Load a simple .env file from the project directory if present."""
    env_path = Path(__file__).parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _get_prompt_name(env_var: str, default_name: str) -> str:
    _load_local_env()
    return os.getenv(env_var, default_name)

def _resolve_prompt_identifier(prompt_name: str) -> str:
    return prompt_name

@lru_cache(maxsize=None)
def _pull_prompt(prompt_name: str) -> BasePromptTemplate:
    client = Client()
    prompt_identifier = _resolve_prompt_identifier(prompt_name)
    prompt = client.pull_prompt(prompt_identifier)

    if not isinstance(prompt, BasePromptTemplate):
        raise TypeError(
            f"LangSmith prompt {prompt_identifier!r} did not return a PromptTemplate."
        )
    return prompt


def _render_prompt_text(
    prompt: BasePromptTemplate,
    prompt_name: str,
    **kwargs: str,
) -> str:
    try:
        return prompt.format(**kwargs)
    except Exception as exc:
        raise RuntimeError(
            f"LangSmith prompt {prompt_name!r} could not be formatted with the "
            "provided inputs."
        ) from exc


def get_supervisor_system_prompt() -> str:
    prompt_name = _get_prompt_name(
        "LANGSMITH_PROMPT_SUPERVISOR",
        DEFAULT_PROMPT_NAMES["supervisor"],
    )
    return _render_prompt_text(_pull_prompt(prompt_name), prompt_name)


def get_calendar_system_prompt() -> str:
    prompt_name = _get_prompt_name(
        "LANGSMITH_PROMPT_CALENDAR_SYSTEM",
        DEFAULT_PROMPT_NAMES["calendar_system"],
    )
    return _render_prompt_text(_pull_prompt(prompt_name), prompt_name)


def get_email_system_prompt() -> str:
    prompt_name = _get_prompt_name(
        "LANGSMITH_PROMPT_EMAIL_SYSTEM",
        DEFAULT_PROMPT_NAMES["email_system"],
    )
    return _render_prompt_text(_pull_prompt(prompt_name), prompt_name)


def get_calendar_reflection_prompt() -> BasePromptTemplate:
    prompt_name = _get_prompt_name(
        "LANGSMITH_PROMPT_CALENDAR_REFLECTION",
        DEFAULT_PROMPT_NAMES["calendar_reflection"],
    )
    return _pull_prompt(prompt_name)


def get_calendar_revision_prompt() -> BasePromptTemplate:
    prompt_name = _get_prompt_name(
        "LANGSMITH_PROMPT_CALENDAR_REVISION",
        DEFAULT_PROMPT_NAMES["calendar_revision"],
    )
    return _pull_prompt(prompt_name)
