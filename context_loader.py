"""Load context documents from the me/ directory."""

import logging
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

ME_DIR = Path(__file__).parent / "me"


def _load_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(path)
        text_parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"Failed to load PDF {path}: {e}")
        return ""


def _load_markdown(path: Path) -> str:
    """Load a markdown file as plain text."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning(f"Failed to load markdown {path}: {e}")
        return ""


@lru_cache(maxsize=1)
def load_context() -> str:
    """
    Load all context documents and return as a single formatted string.

    Cached after first call to avoid re-reading files on every request.
    Raises RuntimeError if no context documents can be loaded.
    """
    summary = _load_markdown(ME_DIR / "summary.md")
    resume = _load_pdf(ME_DIR / "resume.pdf")
    linkedin = _load_pdf(ME_DIR / "linkedin.pdf")

    sections = []

    if summary:
        sections.append(f"## About Samuel\n{summary}")

    if resume:
        sections.append(f"## Resume\n{resume}")

    if linkedin:
        sections.append(f"## LinkedIn Profile\n{linkedin}")

    if not sections:
        raise RuntimeError(
            "Failed to load any context documents. "
            "Ensure files exist in the me/ directory: summary.md, resume.pdf, linkedin.pdf"
        )

    context = "\n\n---\n\n".join(sections)
    logger.info(f"Loaded context: {len(context)} characters")
    return context
