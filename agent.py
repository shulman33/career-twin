"""LangChain agent for the Career Twin chatbot."""

import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from context_loader import load_context
from prompts import get_system_prompt
from tools import send_email_to_samuel

load_dotenv()


def build_agent():
    """Create and return a ReAct agent with tools."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")

    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.7,
    )

    context = load_context()
    system_prompt = get_system_prompt(context)

    agent = create_agent(
        model=model,
        tools=[send_email_to_samuel],
        system_prompt=system_prompt,
    )

    return agent


def _extract_text_content(content) -> str:
    """Extract text from Gradio 6 content format.

    Gradio 6 uses: [{"type": "text", "text": "..."}] or just a string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif isinstance(block, str):
                texts.append(block)
        return " ".join(texts)
    return ""


def _convert_history_to_messages(history: list) -> list:
    """Convert Gradio message history to LangChain message format."""
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        raw_content = msg.get("content", "")

        # Extract text from Gradio 6 content format
        content = _extract_text_content(raw_content)

        # Skip empty messages or tool metadata messages
        if not content.strip():
            continue

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    return messages


async def run_agent_stream(
    agent, message: str, history: list
) -> AsyncGenerator[str, None]:
    """
    Stream agent responses for Gradio ChatInterface.

    Yields text chunks as they arrive from the model.
    """
    # Convert history and add new message
    messages = _convert_history_to_messages(history)
    messages.append(HumanMessage(content=message))

    # Stream the response
    collected_content = ""

    async for event in agent.astream_events(
        {"messages": messages},
        version="v2",
    ):
        event_type = event.get("event", "")

        # Handle text streaming from the model
        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            raw_content = getattr(chunk, "content", None) if chunk else None
            if raw_content:
                text = _extract_text_content(raw_content)
                if text:
                    collected_content += text
                    yield collected_content

        # Handle final response (fallback if streaming doesn't work)
        elif event_type == "on_chat_model_end":
            output = event.get("data", {}).get("output")
            raw_content = getattr(output, "content", None) if output else None
            if raw_content and not collected_content:
                collected_content = _extract_text_content(raw_content)
                yield collected_content

    # Ensure we always yield something if nothing was collected
    if not collected_content:
        yield "I apologize, but I wasn't able to generate a response. Please try again."
