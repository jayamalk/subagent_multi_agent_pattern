from __future__ import annotations

import os
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langsmith import Client

PROMPT_TEMPLATES = {
    "hellosubagents-supervisor": (
        "You are a helpful personal assistant. "
        "You can schedule calendar events and send emails. "
        "Break down user requests into appropriate tool calls and coordinate the results. "
        "When a request involves multiple actions, use multiple tools in sequence."
    ),
    "hellosubagents-calendar-system": (
        "You are a calendar scheduling assistant. "
        "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
        "into proper ISO datetime formats. "
        "Use get_available_time_slots to check availability when needed. "
        "If there is no suitable time slot, stop and confirm unavailability in your response. "
        "Use create_calendar_event to schedule events. "
        "Always confirm what was scheduled in your final response."
    ),
    "hellosubagents-calendar-reflection": (
        "You are a strict reviewer for a calendar scheduling assistant. "
        "Check that the final assistant response accurately reflects the user request "
        "and the tool actions. If everything is correct, reply with 'APPROVED'. "
        "Otherwise reply with 'CRITIQUE: <specific issues and fixes>'.\n\n"
        "Conversation:\n{transcript}"
    ),
    "hellosubagents-calendar-revision": (
        "You are the calendar scheduling assistant. Revise ONLY the final assistant "
        "response based on the critique. Do not call tools or add new actions. "
        "Return a single corrected response.\n\n"
        "Conversation:\n{transcript}\n\n"
        "Critique:\n{critique}"
    ),
    "hellosubagents-email-system": (
        "You are an email assistant. "
        "Compose professional emails based on natural language requests. "
        "Extract recipient information and craft appropriate subject lines and body text. "
        "Use send_email to send the message. "
        "Always confirm what was sent in your final response."
    ),
}

def _load_local_env() -> None:
    env_path = Path(__file__).parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    _load_local_env()
    client = Client()

    for name, template in PROMPT_TEMPLATES.items():
        prompt_identifier = name
        prompt = PromptTemplate.from_template(template)
        url = client.push_prompt(prompt_identifier, object=prompt)
        print(f"Pushed {prompt_identifier}: {url}")


if __name__ == "__main__":
    main()
