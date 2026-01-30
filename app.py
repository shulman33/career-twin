"""Gradio app for the Career Twin chatbot."""

import gradio as gr

from agent import build_agent, run_agent_stream

# Create agent once at startup
agent = build_agent()


async def chat(message: str, history: list) -> str:
    """
    Handle chat messages and stream responses.

    Args:
        message: The user's message (can be string or dict with content)
        history: List of previous messages in Gradio 6 format

    Yields:
        Accumulated response text for streaming display
    """
    # Handle message format (Gradio 6 may pass dict or string)
    if isinstance(message, dict):
        message_text = message.get("text", "")
    else:
        message_text = message

    async for response in run_agent_stream(agent, message_text, history):
        yield response


demo = gr.ChatInterface(
    fn=chat,
    title="Chat with Samuel's AI Twin",
    description=(
        "Hi! I'm an AI representing Samuel Shulman. "
        "Ask me about his background, skills, experience, or projects. "
        "If you'd like to connect with Samuel directly, just let me know!"
    ),
    examples=[
        "Tell me about yourself",
        "What are your technical skills?",
        "What projects have you worked on?",
        "Are you open to new opportunities?",
        "I'd like to get in touch with Samuel",
    ],
    cache_examples=False,
)
