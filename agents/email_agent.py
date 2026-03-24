from langchain.agents import create_agent
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
    )
