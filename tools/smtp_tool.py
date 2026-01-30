"""SMTP tool for sending recruiter messages to Samuel."""

import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
3. Keep it concise and actionable for Samuel to quickly understand the context

# Input
{conversation}"""

    response = llm.invoke(prompt)
    return response.content


def _send_smtp_email(to_email: str, subject: str, body: str) -> None:
    """Send an email via Gmail SMTP."""
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())


def _format_email_body(recruiter_email: str, message: str, summary: str) -> str:
    """Format the email body with message first, then summary and contact."""
    return f"""MESSAGE FROM RECRUITER
{message}

---

CONVERSATION SUMMARY
{summary}

---

CONTACT
{recruiter_email}
"""


@tool(args_schema=SendEmailInput)
def send_email_to_samuel(
    recruiter_email: str, message: str, conversation_history: str
) -> str:
    """
    Send an email to Samuel with the recruiter's message and conversation summary.

    Use this tool when a recruiter wants to get in touch with Samuel directly,
    express interest in his profile, or schedule a conversation.
    """
    try:
        recipient_email = os.getenv("RECIPIENT_EMAIL", "samshulman6@gmail.com")
        summary = _summarize_conversation(conversation_history)
        body = _format_email_body(recruiter_email, message, summary)
        _send_smtp_email(
            to_email=recipient_email,
            subject=f"Career Twin: Message from recruiter ({recruiter_email})",
            body=body,
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
            "You can reach Samuel directly at samshulman6@gmail.com. "
            "Sorry for the inconvenience!"
        )
