import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest
from agentevals.trajectory.llm import (
    TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
    create_trajectory_llm_as_judge,
)
from langchain.messages import AIMessage, HumanMessage, ToolMessage

from agents.subagent import build_supervisor_agent
from config.ollama_config import build_chat_model, get_ollama_settings

pytestmark = pytest.mark.live_llm


@dataclass(frozen=True)
class TrajectoryEvalCase:
    name: str
    user_request: str
    reference_trajectory: list


def _skip_unless_ollama_model_is_available() -> None:
    model_name, base_url = get_ollama_settings()
    tags_url = f"{base_url.rstrip('/')}/api/tags"

    try:
        with urlopen(tags_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        pytest.skip(
            f"Ollama trajectory evals require a reachable server at {base_url}: {exc}"
        )

    installed_models = {
        model.get("name", "")
        for model in payload.get("models", [])
        if model.get("name")
    }
    if model_name not in installed_models:
        available = ", ".join(sorted(installed_models)) or "none"
        pytest.skip(
            f"Ollama model {model_name!r} is not installed at {base_url}. "
            f"Available models: {available}"
        )


@pytest.fixture(scope="module")
def supervisor_agent():
    _skip_unless_ollama_model_is_available()
    return build_supervisor_agent()


@pytest.fixture(scope="module")
def trajectory_judge():
    _skip_unless_ollama_model_is_available()
    return create_trajectory_llm_as_judge(
        judge=build_chat_model(),
        prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
    )


CASES = [
    TrajectoryEvalCase(
        name="schedule_event",
        user_request=(
            "Schedule a 30 minute meeting with alice@example.com on 2026-03-25 "
            "at 14:00."
        ),
        reference_trajectory=[
            HumanMessage(
                content=(
                    "Schedule a 30 minute meeting with alice@example.com on "
                    "2026-03-25 at 14:00."
                )
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "schedule_event",
                        "args": {
                            "request": (
                                "Schedule a 30 minute meeting with "
                                "alice@example.com on 2026-03-25 at 14:00"
                            )
                        },
                    }
                ],
            ),
            ToolMessage(
                content=(
                    "The 30 minute meeting with alice@example.com was scheduled "
                    "for 2026-03-25 from 14:00 to 14:30."
                ),
                tool_call_id="call_1",
            ),
            AIMessage(
                content=(
                    "The 30 minute meeting with alice@example.com has been "
                    "scheduled for March 25, 2026 at 14:00."
                )
            ),
        ],
    ),
    TrajectoryEvalCase(
        name="schedule_event_and_email",
        user_request=(
            "Schedule a 30 minute meeting with alice@example.com on 2026-03-25 "
            "at 14:00 and send her an email reminder about it."
        ),
        reference_trajectory=[
            HumanMessage(
                content=(
                    "Schedule a 30 minute meeting with alice@example.com on "
                    "2026-03-25 at 14:00 and send her an email reminder about it."
                )
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "schedule_event",
                        "args": {
                            "request": (
                                "30 minute meeting with alice@example.com on "
                                "2026-03-25 at 14:00"
                            )
                        },
                    },
                    {
                        "id": "call_2",
                        "name": "manage_email",
                        "args": {
                            "request": (
                                "send email reminder to alice@example.com "
                                "about the meeting scheduled for 2026-03-25 "
                                "at 14:00"
                            )
                        },
                    },
                ],
            ),
            ToolMessage(
                content=(
                    "The meeting was scheduled successfully for "
                    "alice@example.com."
                ),
                tool_call_id="call_1",
            ),
            ToolMessage(
                content="A reminder email was sent to alice@example.com.",
                tool_call_id="call_2",
            ),
            AIMessage(
                content=(
                    "The assistant could not schedule the meeting and no email "
                    "was sent."
                )
            ),
        ],
    )
]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_supervisor_trajectory_llm_judge_with_reference(
    case: TrajectoryEvalCase,
    supervisor_agent,
    trajectory_judge,
) -> None:
    result = supervisor_agent.invoke(
        {"messages": [{"role": "user", "content": case.user_request}]}
    )

    assert result["messages"], "Supervisor agent returned no messages."

    evaluation = trajectory_judge(
        outputs=result["messages"],
        reference_outputs=case.reference_trajectory,
    )

    assert evaluation["score"] is True, evaluation["comment"]
