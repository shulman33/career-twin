"""Email tool for sending recruiter messages to Sam via Resend API."""

import logging
import os
import re

import resend
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, field_validator

load_dotenv()

logger = logging.getLogger(__name__)


class SendEmailInput(BaseModel):
    """Input schema for the send_email tool."""

    recruiter_email: str = Field(description="The recruiter's email address for follow-up")
    message: str = Field(description="The recruiter's message or reason for reaching out")
    conversation_history: str = Field(
        description="The full conversation history between the recruiter and the agent"
    )

    @field_validator("recruiter_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v


def _summarize_conversation(conversation: str) -> str:
    """Generate a concise summary of the conversation using Gemini."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

    prompt = f"""# Role
You are a conversation summarizer.

# Instructions
1. Summarize this recruiter-agent conversation in 3-5 bullet points
2. Focus on: what the recruiter asked about, key topics discussed, and any specific interests they expressed
3. Keep it concise and actionable for Sam to quickly understand the context

# Input
{conversation}"""

    response = llm.invoke(prompt)
    return response.content


def _send_resend_email(to_email: str, subject: str, html: str) -> None:
    """Send an HTML email via Resend API."""
    resend.api_key = os.getenv("RESEND_API_KEY")

    if not resend.api_key:
        raise ValueError("RESEND_API_KEY must be set in environment")

    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    resend.Emails.send(params)


def _format_email_html(recruiter_email: str, message: str, summary: str) -> str:
    """Format the email as HTML with clean, minimal styling."""
    # Convert markdown bullet points to HTML list items
    summary_lines = summary.strip().split("\n")
    summary_html_items = []
    for line in summary_lines:
        # Remove leading bullet characters (*, -, •) and whitespace
        clean_line = line.lstrip("*-• ").strip()
        if clean_line:
            summary_html_items.append(f"<li>{clean_line}</li>")
    summary_list = "\n".join(summary_html_items)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #ffffff; color: #1a1a1a; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto;">
        <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 12px 0; color: #1a1a1a;">Message from Recruiter</h2>
        <p style="margin: 0 0 24px 0; white-space: pre-wrap;">{message}</p>

        <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;">

        <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 12px 0; color: #1a1a1a;">Conversation Summary</h2>
        <ul style="margin: 0 0 24px 0; padding-left: 20px;">
            {summary_list}
        </ul>

        <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;">

        <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 12px 0; color: #1a1a1a;">Contact</h2>
        <p style="margin: 0;"><a href="mailto:{recruiter_email}" style="color: #0066cc; text-decoration: none;">{recruiter_email}</a></p>
    </div>
</body>
</html>"""


@tool(args_schema=SendEmailInput)
def send_email_to_samuel(
    recruiter_email: str, message: str, conversation_history: str
) -> str:
    """
    Send an email to Sam with the recruiter's message and conversation summary.

    Use this tool when a recruiter wants to get in touch with Sam directly,
    express interest in his profile, or schedule a conversation.
    """
    try:
        recipient_email = os.getenv("RECIPIENT_EMAIL", "samshulman6@gmail.com")
        summary = _summarize_conversation(conversation_history)
        html = _format_email_html(recruiter_email, message, summary)
        _send_resend_email(
            to_email=recipient_email,
            subject=f"Career Twin: Message from recruiter ({recruiter_email})",
            html=html,
        )
        return (
            "Your message has been sent to Sam. "
            "He typically responds within 24-48 hours. "
            "Thanks for reaching out!"
        )
    except Exception as e:
        logger.error(f"Failed to send email: {type(e).__name__}: {e}")
        return (
            "I wasn't able to send your message due to a technical issue. "
            "You can reach Sam directly at samshulman6@gmail.com."
            "Sorry for the inconvenience!"
        )
