from typing import Annotated, NotRequired

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langchain.tools import tool
from langgraph.types import Command

from agents.reflection_agent_factory import ReflectionAgentFactory
from config.prompt_config import (
    get_calendar_reflection_prompt,
    get_calendar_revision_prompt,
    get_calendar_system_prompt,
)
from state.calendar_state import EventfulAgentState, build_calendar_event


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
        system_prompt=get_calendar_system_prompt(),
    )

    factory = ReflectionAgentFactory(
        model,
        reflection_prompt=get_calendar_reflection_prompt(),
        revision_prompt=get_calendar_revision_prompt(),
        max_reflections=max_reflections,
    )
    return factory.build(base_calendar_agent, CalendarAgentState)
