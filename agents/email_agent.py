from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, PIIMiddleware
from langchain.tools import tool

from config.prompt_config import get_email_system_prompt


@tool
def send_email(
    to: list[str],      # email addresses
    subject: str,
    body: str,
    cc: list[str] = []
) -> str:
    """Send an email via email API. Requires properly formatted addresses."""
    return f"Email sent to {', '.join(to)} - Subject: {subject}"


def build_email_agent(model):
    return create_agent(
        model,
        tools=[send_email],
        system_prompt=get_email_system_prompt(),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    # Require approval for sensitive operations
                    "send_email": True,
                }
            ),
            PIIMiddleware(
                "email",
                strategy="redact",
                apply_to_input=True,
            ),
            # Mask credit cards in user input
            PIIMiddleware(
                "credit_card",
                strategy="mask",
                apply_to_input=True,
            ),
            # Block API keys - raise error if detected
            PIIMiddleware(
                "api_key",
                detector=r"sk-[a-zA-Z0-9]{32}",
                strategy="block",
                apply_to_input=True,
            ),
        ],
    )
