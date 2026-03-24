from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, StateGraph


def _default_format_messages(messages: list) -> str:
    lines = []
    for message in messages:
        role = getattr(message, "type", message.__class__.__name__)
        content = getattr(message, "content", "")
        if isinstance(message, AIMessage) and message.tool_calls:
            content = f"{content}\nTool calls: {message.tool_calls}"
        if isinstance(message, ToolMessage) and message.name:
            content = f"{message.name}: {content}"
        lines.append(f"{role}: {content}".strip())
    return "\n".join(lines)


class ReflectionAgentFactory:
    def __init__(
        self,
        model,
        reflection_prompt: str,
        revision_prompt: str,
        max_reflections: int = 1,
        formatter: Callable[[list], str] | None = None,
    ) -> None:
        self._model = model
        self._reflection_prompt = reflection_prompt
        self._revision_prompt = revision_prompt
        self._max_reflections = max_reflections
        self._formatter = formatter or _default_format_messages

    def build(self, base_agent, state_schema):
        def reflect(state) -> dict:
            messages = state.get("messages", [])
            if not messages:
                return {}

            transcript = self._formatter(messages)
            reflection = self._model.invoke(
                [
                    HumanMessage(
                        content=self._reflection_prompt.format(transcript=transcript)
                    )
                ]
            )
            critique = (reflection.content or "").strip()
            approved = critique.upper().startswith("APPROVED")
            reflection_count = state.get("reflection_count", 0) + 1

            if approved:
                return {
                    "reflection_approved": True,
                    "reflection_count": reflection_count,
                }

            revised = self._model.invoke(
                [
                    HumanMessage(
                        content=self._revision_prompt.format(
                            transcript=transcript,
                            critique=critique,
                        )
                    )
                ]
            )
            revised_text = (revised.content or "").strip()
            if revised_text:
                if isinstance(messages[-1], AIMessage):
                    messages = [*messages[:-1], AIMessage(content=revised_text)]
                else:
                    messages = [*messages, AIMessage(content=revised_text)]

            return {
                "messages": messages,
                "reflection_approved": False,
                "reflection_count": reflection_count,
            }

        def should_continue(state) -> str:
            if state.get("reflection_approved"):
                return END
            if state.get("reflection_count", 0) >= self._max_reflections:
                return END
            return "reflect"

        graph = StateGraph(state_schema)
        graph.add_node("generate", base_agent)
        graph.add_node("reflect", reflect)
        graph.set_entry_point("generate")
        graph.add_edge("generate", "reflect")
        graph.add_conditional_edges("reflect", should_continue)
        return graph.compile()
