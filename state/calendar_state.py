from typing import NotRequired, TypedDict

from langchain.agents import AgentState


class CalendarEvent(TypedDict):
    title: str
    start_time: str
    end_time: str
    attendees: list[str]
    location: str


def build_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    attendees: list[str],
    location: str,
) -> CalendarEvent:
    return {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "location": location,
    }


class EventfulAgentState(AgentState):
    created_event: NotRequired[CalendarEvent | None]
