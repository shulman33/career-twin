---
title: career-twin
emoji: 💼
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.47.1
app_file: app.py
pinned: false
---

# Career Twin

An AI-powered chatbot that represents Sam Shulman to recruiters. Built with LangChain, Google Gemini, and Gradio.

## Features

- Answers questions about Sam's background, skills, and experience
- Uses context from resume, LinkedIn profile, and personal Q&A document
- Allows recruiters to send messages directly to Sam via email
- Deployed on Hugging Face Spaces for free hosting

## Local Development

```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the app
uv run python app.py
```

## Environment Variables

- `GOOGLE_API_KEY` - Google AI API key for Gemini
- `EMAIL_ADDRESS` - Gmail address for sending recruiter messages
- `EMAIL_PASSWORD` - Gmail app password

## Deployment

Push to Hugging Face Spaces - the app will auto-deploy using the Gradio SDK.
