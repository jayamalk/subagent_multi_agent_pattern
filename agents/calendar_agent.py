from typing import Annotated, NotRequired

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langchain.tools import tool
from langgraph.types import Command

from agents.reflection_agent_factory import ReflectionAgentFactory
from state.calendar_state import EventfulAgentState, build_calendar_event


_REFLECTION_PROMPT = (
    "You are a strict reviewer for a calendar scheduling assistant. "
    "Check that the final assistant response accurately reflects the user request "
    "and the tool actions. If everything is correct, reply with 'APPROVED'. "
    "Otherwise reply with 'CRITIQUE: <specific issues and fixes>'.\n\n"
    "Conversation:\n{transcript}"
)

_REVISION_PROMPT = (
    "You are the calendar scheduling assistant. Revise ONLY the final assistant "
    "response based on the critique. Do not call tools or add new actions. "
    "Return a single corrected response.\n\n"
    "Conversation:\n{transcript}\n\n"
    "Critique:\n{critique}"
)


class CalendarAgentState(EventfulAgentState):
    reflection_count: NotRequired[int]
    reflection_approved: NotRequired[bool]


@tool
def create_calendar_event(
    title: str,
    start_time: str,  # ISO format: "2024-01-15T14:00:00"
    end_time: str,    # ISO format: "2024-01-15T15:00:00"
    attendees: list[str],  # email addresses
    location: str = "",
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Create a calendar event. Requires exact ISO datetime format."""
    created_event = build_calendar_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        location=location,
    )
    summary = (
        f"Event created: {title} from {start_time} to {end_time} "
        f"with {len(attendees)} attendees"
    )
    return Command(
        update={
            "created_event": created_event,
            "messages": [
                ToolMessage(content=summary, tool_call_id=tool_call_id),
            ],
        }
    )


@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int
) -> list[str]:
    """Check calendar availability for given attendees on a specific date."""
    return ["09:00", "14:00", "16:00"]


def build_calendar_agent(model, max_reflections: int = 1):
    base_calendar_agent = create_agent(
        model,
        tools=[create_calendar_event, get_available_time_slots],
        state_schema=CalendarAgentState,
        system_prompt=(
            "You are a calendar scheduling assistant. "
            "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
            "into proper ISO datetime formats. "
            "Use get_available_time_slots to check availability when needed. "
            "If there is no suitable time slot, stop and confirm unavailability in your response. "
            "Use create_calendar_event to schedule events. "
            "Always confirm what was scheduled in your final response."
        )
    )

    factory = ReflectionAgentFactory(
        model,
        reflection_prompt=_REFLECTION_PROMPT,
        revision_prompt=_REVISION_PROMPT,
        max_reflections=max_reflections,
    )
    return factory.build(base_calendar_agent, CalendarAgentState)
