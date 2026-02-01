# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Career-twin is an AI-powered chatbot that represents Sam Shulman to recruiters. It uses LangChain with Google's Gemini models to answer recruiter questions based on personal context (resume, LinkedIn profile).

**The problem:** Recruiters find my LinkedIn, visit my portfolio, get curious—but then we fall into slow email tag.

**The solution:** An AI agent that acts as a virtual version of me, answering questions about my background in real-time. The agent runs on Gemini 3.0 Flash (good balance of speed and cost) and includes a custom SMTP tool so interested recruiters can send me an email directly from the conversation.

The SMTP tool summarizes the conversation the recruiter had with the agent, then emails me that summary along with the recruiter's message.

## Architecture Patterns

### Simplicity First
Prefer simple, straightforward solutions. Any added complexity must be justified—don't over-engineer or add abstractions "just in case." If a simple function solves the problem, don't wrap it in a class.

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run the application
uv run python app.py

# Add a new dependency
uv add <package-name>
```

## Architecture

- **`app.py`** - Gradio application entry point (runs on HuggingFace Spaces)
- **`agent.py`** - LangChain agent configuration and streaming logic
- **`me/`** - Personal context directory containing:
  - `resume.pdf` - Resume document
  - `linkedin.pdf` - LinkedIn profile export
  - `summary.md` - Pre-written Q&A content that gets included directly in the agent's prompt

## Key Dependencies

- **LangChain** + **langchain-google-genai** - AI orchestration with Google Gemini models
- **python-dotenv** - Environment variable management
- **smtplib** (stdlib) - SMTP email sending for the recruiter contact tool

When adding or using libraries, always verify you're using the latest API patterns as of January 2026. Library APIs (especially LangChain) evolve quickly—check current documentation before implementing.

For LangChain documentation, use https://docs.langchain.com/llms.txt for easy parsing and follow links to specific topics.

## Environment Setup

Copy `.env.example` to `.env` and configure:
- `GOOGLE_API_KEY` - Required for Gemini model access
- `EMAIL_ADDRESS` / `EMAIL_PASSWORD` - For email notification features

## LLM Prompt Structure

All prompts must follow this structure with markdown headers:

```
# Role
[One-line identity statement]

# Context  (optional, only if domain background needed)
[Domain-specific context]

# Instructions
[Numbered task rules]

# Input
{placeholder}
```

**Key principles:**
- **Role**: Single line defining the LLM's identity
- **Instructions**: Numbered list of specific rules, kept concise
- **Input**: Always last, with a format placeholder (e.g., `{resume_text}`)
- **No duplication**: Put detailed extraction guidance in Pydantic Field descriptions, not prompts

Since `with_structured_output()` passes the Pydantic schema to the LLM, Field descriptions become part of the extraction context:

```python
# Good: Guidance in Field description
start_date: str | None = Field(
    default=None,
    description="Start date preserved exactly as written (e.g., 'Jan 2020', '2020')",
)

# Bad: Duplicating in both prompt AND Field
# Prompt: "For dates, preserve the original format (e.g., 'Jan 2020')"
# Field: description="Start date (e.g., 'Jan 2020')"
```
