from functools import lru_cache
from typing import Annotated

from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langchain.tools import tool
from langgraph.types import Command

from agents.calendar_agent import build_calendar_agent
from agents.email_agent import build_email_agent
from config.ollama_config import (
    build_chat_model,
    format_ollama_runtime_error,
    get_ollama_settings,
)
from config.prompt_config import get_supervisor_system_prompt
from state.calendar_state import EventfulAgentState


def _get_last_message_text(result: dict, agent_name: str) -> str:
    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError(f"{agent_name} returned no messages.")

    return messages[-1].text.strip()


@lru_cache(maxsize=1)
def build_supervisor_agent():
    # Delay model creation until runtime so configuration errors are actionable.
    model = build_chat_model()

    # =====================================================================
    # Step 2: Create specialized sub-agents
    # =====================================================================

    calendar_agent = build_calendar_agent(model, max_reflections=1)
    email_agent = build_email_agent(model)

    # Registry of available sub-agents
    SUBAGENTS = {
        "calendar": calendar_agent,
        "email": email_agent,
    }

    @tool
    def task(
            agent_name: str,
            description: str
    ) -> str:
        """Launch an ephemeral subagent for a task.

        Available agents:
        - calendar: Schedule calendar events using natural language
        - email: Send emails using natural language
        """
        agent = SUBAGENTS[agent_name]
        result = agent.invoke({
            "messages": [
                {"role": "user", "content": description}
            ]
        })
        return result["messages"][-1].content

    # =====================================================================
    # Step 3: Wrap sub-agents as tools for the supervisor
    # =====================================================================


    @tool
    def schedule_event(
        request: str,
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
    ) -> Command:
        """Schedule calendar events using natural language.

        Use this when the user wants to create, modify, or check calendar appointments.
        Handles date/time parsing, availability checking, and event creation.

        Input: Natural language scheduling request (e.g., 'meeting with design team
        next Tuesday at 2pm')
        """
        result = calendar_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        update = {
            "messages": [
                ToolMessage(
                    content=_get_last_message_text(result, "Calendar agent"),
                    tool_call_id=tool_call_id,
                )
            ]
        }
        if created_event := result.get("created_event"):
            update["created_event"] = created_event
        return Command(update=update)

    @tool
    def manage_email(request: str) -> str:
        """Send emails using natural language.

        Use this when the user wants to send notifications, reminders, or any email
        communication. Handles recipient extraction, subject generation, and email
        composition.

        Input: Natural language email request (e.g., 'send them a reminder about
        the meeting')
        """
        result = email_agent.invoke({
            "messages": [{"role": "user", "content": request}]
        })
        return result["messages"][-1].text

    # =====================================================================
    # Step 4: Create the supervisor agent
    # =====================================================================

    """ Agent registry with task dispatcher """
    return create_agent(
        model,
        tools=[task],
        state_schema=EventfulAgentState,
        system_prompt=get_supervisor_system_prompt(),
    )

    """ Tool per agent, comment above to use this """
    return create_agent(
        model,
        tools=[schedule_event, manage_email],
        state_schema=EventfulAgentState,
        system_prompt=get_supervisor_system_prompt(),
    )




def invoke_supervisor(request: str) -> str:
    model_name, base_url = get_ollama_settings()

    try:
        result = build_supervisor_agent().invoke(
            {"messages": [{"role": "user", "content": request}]}
        )
    except Exception as exc:
        raise RuntimeError(
            format_ollama_runtime_error(base_url, model_name)
        ) from exc

    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError("Supervisor agent returned no messages.")

    return _get_last_message_text(result, "Supervisor agent")


def make_graph(_config=None):
    """LangGraph CLI entrypoint."""
    return build_supervisor_agent()


# =====================================================================
# Step 5: Use the supervisor
# =====================================================================

if __name__ == "__main__":
    # Example: User request requiring both calendar and email coordination
    user_request = (
        "Schedule a meeting with the design team next Tuesday at 2pm for 1 hour, "
        "and send them an email reminder about reviewing the new mockups."
    )

    print("User Request:", user_request)
    print("\n" + "=" * 80 + "\n")
    print(invoke_supervisor(user_request))
