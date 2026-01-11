"""de-ai-agent: Pre-commit hook that removes AI pollution from commit messages."""

__version__ = "0.1.0"

from de_ai_agent.hook import main

__all__ = ["main", "__version__"]
