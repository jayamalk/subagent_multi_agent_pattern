from langchain.agents import create_agent
from langchain.tools import tool


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
        system_prompt=(
            "You are an email assistant. "
            "Compose professional emails based on natural language requests. "
            "Extract recipient information and craft appropriate subject lines and body text. "
            "Use send_email to send the message. "
            "Always confirm what was sent in your final response."
        )
    )
