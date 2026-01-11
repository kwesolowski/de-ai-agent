"""Main hook implementation for de-ai-agent."""

import argparse
import re
import sys
from pathlib import Path


def remove_coauthor(text: str) -> str:
    """Remove Co-Authored-By lines containing AI agent names.

    Args:
        text: Commit message text

    Returns:
        Text with AI co-author lines removed
    """
    # Pattern matches Co-Authored-By lines with common AI agent names
    ai_coauthor_pattern = re.compile(
        r"^Co-Authored-By:.*(?:Claude|GPT|Copilot|Aider|Gemini|Cline|Cody|Windsurf).*$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Remove matching lines
    cleaned = ai_coauthor_pattern.sub("", text)

    # Clean up excessive blank lines (more than 2 consecutive)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.rstrip() + "\n" if cleaned.rstrip() else ""


def remove_branding(text: str) -> str:
    """Remove branding footers and links from commit messages.

    Args:
        text: Commit message text

    Returns:
        Text with branding removed
    """
    # Pattern for emoji + "Generated with..." style branding
    emoji_generated_pattern = re.compile(
        r"(?:🤖|✨|🚀)\s*Generated with.*(?:Claude|AI|Copilot|Cline|Cursor|Aider).*",
        re.IGNORECASE,
    )

    # Pattern for plain "Generated with..." text
    plain_generated_pattern = re.compile(
        r"Generated with.*(?:Claude|AI|Copilot|Cline|Cursor|Aider).*",
        re.IGNORECASE,
    )

    # Pattern for markdown links to AI tools
    markdown_link_pattern = re.compile(
        r"\[(?:Claude Code|Claude|Copilot|AI|Cline|Cursor|Aider)\]\([^)]*\)",
        re.IGNORECASE,
    )

    cleaned = text
    cleaned = emoji_generated_pattern.sub("", cleaned)
    cleaned = plain_generated_pattern.sub("", cleaned)
    cleaned = markdown_link_pattern.sub("", cleaned)

    # Clean up excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.rstrip() + "\n" if cleaned.rstrip() else ""


def sanitize_commit_message(
    text: str,
    *,
    keep_coauthor: bool = False,
    keep_branding: bool = False,
) -> str:
    """Sanitize commit message by removing AI pollution.

    Args:
        text: Original commit message
        keep_coauthor: If True, preserve Co-Authored-By AI lines
        keep_branding: If True, preserve branding footers

    Returns:
        Sanitized commit message
    """
    result = text

    if not keep_coauthor:
        result = remove_coauthor(result)

    if not keep_branding:
        result = remove_branding(result)

    return result


def main() -> int:
    """Main entry point for the commit-msg hook.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Remove AI pollution from commit messages",
    )
    parser.add_argument(
        "--keep-coauthor",
        action="store_true",
        help="Keep Co-Authored-By lines with AI agent names",
    )
    parser.add_argument(
        "--keep-branding",
        action="store_true",
        help='Keep "Generated with..." branding footers',
    )
    parser.add_argument(
        "commit_msg_file",
        nargs="?",
        type=Path,
        help="Path to commit message file (provided by git)",
    )

    args = parser.parse_args()

    # If no file provided, read from stdin (for testing)
    if args.commit_msg_file is None:
        text = sys.stdin.read()
        cleaned = sanitize_commit_message(
            text,
            keep_coauthor=args.keep_coauthor,
            keep_branding=args.keep_branding,
        )
        sys.stdout.write(cleaned)
        return 0

    # Read commit message
    commit_msg_file = args.commit_msg_file
    try:
        original_message = commit_msg_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Commit message file not found: {commit_msg_file}", file=sys.stderr)
        return 1

    # Sanitize the message
    cleaned_message = sanitize_commit_message(
        original_message,
        keep_coauthor=args.keep_coauthor,
        keep_branding=args.keep_branding,
    )

    # Write back the cleaned message
    commit_msg_file.write_text(cleaned_message, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
