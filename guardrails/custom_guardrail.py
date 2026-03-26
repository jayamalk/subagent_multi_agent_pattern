from typing import Any

from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime

class ContentFilterMiddleware(AgentMiddleware):
    """Deterministic guardrail: Block requests containing banned keywords."""

    def __init__(self, banned_keywords: list[str]):
        super().__init__()
        self.banned_keywords = [kw.lower() for kw in banned_keywords]

    @hook_config(can_jump_to=["end"])
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Get the first user message
        if not state["messages"]:
            return None

        first_message = state["messages"][0]
        if first_message.type != "human":
            return None

        content = first_message.content.lower()

        # Check for banned keywords
        for keyword in self.banned_keywords:
            if keyword in content:
                # Block execution before any processing
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I cannot process requests containing inappropriate content. Please rephrase your request."
                    }],
                    "jump_to": "end"
                }

        return None


class EmailApprovalGuardrail(AgentMiddleware):
    """Guardrail for email operations: Requires explicit user approval before sending emails.
    
    In test/automation mode, can be configured to auto-approve email sends.
    """
    
    # Class variable to track execution count across instances for testing
    execution_count = 0

    def __init__(self, auto_approve: bool = False):
        """Initialize the email approval guardrail.
        
        Args:
            auto_approve: If True, automatically approve email sends (for testing/automation).
                         If False, requires explicit user approval (production mode).
        """
        super().__init__()
        self.auto_approve = auto_approve
        self.pending_approval = None
        self.email_approvals_processed = 0

    @hook_config(can_jump_to=["tool_execution", "rejection"])
    def before_tool(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """Intercept tool calls to check for email sending operations."""
        if not state.get("messages"):
            return None

        # Get the last message (should be AI message with tool calls)
        last_message = state["messages"][-1]
        
        # Check for send_email tool call
        if hasattr(last_message, 'tool_calls'):
            for tool_call in last_message.tool_calls:
                if tool_call.get("name") == "send_email":
                    # Increment execution tracking
                    self.email_approvals_processed += 1
                    EmailApprovalGuardrail.execution_count += 1
                    
                    if self.auto_approve:
                        # Auto-approve in test mode
                        self.pending_approval = tool_call
                        return None
                    else:
                        # In production, request user approval
                        email_args = tool_call.get("args", {})
                        approval_msg = (
                            f"Approval Required: Email Operation Detected\n"
                            f"To: {email_args.get('to', 'unknown')}\n"
                            f"Subject: {email_args.get('subject', 'no subject')}\n"
                            f"Do you approve this email? (yes/no)"
                        )
                        self.pending_approval = tool_call
                        return {
                            "messages": [{
                                "role": "system",
                                "content": approval_msg
                            }]
                        }
        
        return None
    
    @classmethod
    def reset_execution_count(cls):
        """Reset the execution count. Useful for testing."""
        cls.execution_count = 0
