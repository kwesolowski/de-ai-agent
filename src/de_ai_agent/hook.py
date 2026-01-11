"""Main hook implementation for de-ai-agent."""

import argparse
import re
import sys
from pathlib import Path


def remove_coauthor(text: str) -> tuple[str, list[str]]:
    """Remove Co-Authored-By lines containing AI agent names.

    Args:
        text: Commit message text

    Returns:
        Tuple of (cleaned text, list of removed lines)
    """
    # Pattern matches Co-Authored-By lines with common AI agent names
    ai_coauthor_pattern = re.compile(
        r"^Co-Authored-By:.*(?:Claude|GPT|Copilot|Aider|Gemini|Cline|Cody|Windsurf).*$",
        re.MULTILINE | re.IGNORECASE,
    )

    # Find matching lines before removal
    removed_lines = ai_coauthor_pattern.findall(text)

    # Remove matching lines
    cleaned = ai_coauthor_pattern.sub("", text)

    # Clean up excessive blank lines (more than 2 consecutive)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return (
        cleaned.rstrip() + "\n" if cleaned.rstrip() else "",
        removed_lines,
    )


def remove_branding(text: str) -> tuple[str, list[str]]:
    """Remove branding footers and links from commit messages.

    Args:
        text: Commit message text

    Returns:
        Tuple of (cleaned text, list of removed content)
    """
    removed_items: list[str] = []

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

    # Remove emoji-style branding and track what was removed
    matches = emoji_generated_pattern.findall(cleaned)
    removed_items.extend(matches)
    cleaned = emoji_generated_pattern.sub("", cleaned)

    # Remove plain branding and track what was removed
    matches = plain_generated_pattern.findall(cleaned)
    removed_items.extend(matches)
    cleaned = plain_generated_pattern.sub("", cleaned)

    # Remove markdown links and track what was removed
    matches = markdown_link_pattern.findall(cleaned)
    removed_items.extend(matches)
    cleaned = markdown_link_pattern.sub("", cleaned)

    # Clean up excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return (
        cleaned.rstrip() + "\n" if cleaned.rstrip() else "",
        removed_items,
    )


def sanitize_commit_message(
    text: str,
    *,
    keep_coauthor: bool = False,
    keep_branding: bool = False,
) -> tuple[str, dict[str, list[str]]]:
    """Sanitize commit message by removing AI pollution.

    Args:
        text: Original commit message
        keep_coauthor: If True, preserve Co-Authored-By AI lines
        keep_branding: If True, preserve branding footers

    Returns:
        Tuple of (sanitized message, dict of removed items by category)
    """
    result = text
    removed: dict[str, list[str]] = {"coauthor": [], "branding": []}

    if not keep_coauthor:
        result, coauthor_removed = remove_coauthor(result)
        removed["coauthor"] = coauthor_removed

    if not keep_branding:
        result, branding_removed = remove_branding(result)
        removed["branding"] = branding_removed

    return result, removed


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
        "--verbose",
        action="store_true",
        help="Show detailed output of what was removed",
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
        cleaned, removed = sanitize_commit_message(
            text,
            keep_coauthor=args.keep_coauthor,
            keep_branding=args.keep_branding,
        )
        sys.stdout.write(cleaned)
        _print_feedback(removed, args.verbose)
        return 0

    # Read commit message
    commit_msg_file = args.commit_msg_file
    try:
        original_message = commit_msg_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Commit message file not found: {commit_msg_file}", file=sys.stderr)
        return 1

    # Sanitize the message
    cleaned_message, removed = sanitize_commit_message(
        original_message,
        keep_coauthor=args.keep_coauthor,
        keep_branding=args.keep_branding,
    )

    # Write back the cleaned message
    commit_msg_file.write_text(cleaned_message, encoding="utf-8")

    # Print feedback about what was removed
    _print_feedback(removed, args.verbose)

    return 0


def _print_feedback(removed: dict[str, list[str]], verbose: bool) -> None:
    """Print feedback about removed items to stderr.

    Args:
        removed: Dictionary of removed items by category
        verbose: Whether to show detailed output
    """
    coauthor_count = len(removed["coauthor"])
    branding_count = len(removed["branding"])

    # Silent if nothing was removed
    if coauthor_count == 0 and branding_count == 0:
        return

    if verbose:
        # Detailed output showing what was removed
        print("de-ai-agent: Removed:", file=sys.stderr)
        for line in removed["coauthor"]:
            print(f"  - {line}", file=sys.stderr)
        for item in removed["branding"]:
            print(f"  - {item}", file=sys.stderr)
    else:
        # Minimal one-line summary
        removed_parts = []
        if coauthor_count > 0:
            removed_parts.append("AI co-author")
        if branding_count > 0:
            removed_parts.append("branding")

        if removed_parts:
            print(f"de-ai-agent: Removed {', '.join(removed_parts)}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
