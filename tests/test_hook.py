"""Unit tests for de-ai-agent hook."""

import io
import sys

from de_ai_agent.hook import (
    _print_feedback,
    remove_branding,
    remove_coauthor,
    sanitize_commit_message,
)


class TestRemoveCoauthor:
    """Tests for remove_coauthor function."""

    def test_remove_claude_coauthor(self) -> None:
        """Remove Claude co-author attribution."""
        text = """Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        expected = "Fix authentication bug\n"
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1
        assert "Claude Sonnet 4.5" in removed[0]

    def test_remove_gpt_coauthor(self) -> None:
        """Remove GPT co-author attribution."""
        text = """Add new feature

Co-Authored-By: GPT-4 <ai@openai.com>
"""
        expected = "Add new feature\n"
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1

    def test_remove_copilot_coauthor(self) -> None:
        """Remove GitHub Copilot co-author attribution."""
        text = """Refactor code

Co-Authored-By: GitHub Copilot <copilot@github.com>
"""
        expected = "Refactor code\n"
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1

    def test_remove_aider_coauthor(self) -> None:
        """Remove Aider co-author attribution."""
        text = """Update config

Co-Authored-By: aider <aider@example.com>
"""
        expected = "Update config\n"
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1

    def test_keep_human_coauthor(self) -> None:
        """Keep human co-author, remove only AI."""
        text = """Implement feature

Co-Authored-By: Alice <alice@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
Co-Authored-By: Bob <bob@example.com>
"""
        expected = """Implement feature

Co-Authored-By: Alice <alice@example.com>

Co-Authored-By: Bob <bob@example.com>
"""
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1

    def test_no_coauthor(self) -> None:
        """Message without co-author remains unchanged."""
        text = """Simple commit message

This is a detailed description.
"""
        result, removed = remove_coauthor(text)
        assert result == text
        assert len(removed) == 0

    def test_empty_message(self) -> None:
        """Empty message returns empty string."""
        result, removed = remove_coauthor("")
        assert result == ""
        assert len(removed) == 0

    def test_case_insensitive(self) -> None:
        """Pattern matching is case insensitive."""
        text = """Fix bug

Co-Authored-By: claude assistant <ai@example.com>
"""
        expected = "Fix bug\n"
        result, removed = remove_coauthor(text)
        assert result == expected
        assert len(removed) == 1


class TestRemoveBranding:
    """Tests for remove_branding function."""

    def test_remove_claude_code_link(self) -> None:
        """Remove 'Generated with Claude Code' markdown link."""
        text = """Add user registration

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        expected = "Add user registration\n"
        result, removed = remove_branding(text)
        assert result == expected
        assert len(removed) >= 1

    def test_remove_plain_generated_text(self) -> None:
        """Remove plain 'Generated with' text."""
        text = """Update docs

Generated with Claude AI
"""
        expected = "Update docs\n"
        result, removed = remove_branding(text)
        assert result == expected
        assert len(removed) == 1

    def test_remove_emoji_branding(self) -> None:
        """Remove emoji + generated branding."""
        text = """Fix typo

✨ Generated with Cursor AI
"""
        expected = "Fix typo\n"
        result, removed = remove_branding(text)
        assert result == expected
        assert len(removed) == 1

    def test_remove_multiple_branding_lines(self) -> None:
        """Remove multiple branding lines."""
        text = """Commit message

Generated with Claude
🤖 Generated with [AI Assistant](https://example.com)
"""
        expected = "Commit message\n"
        result, removed = remove_branding(text)
        assert result == expected
        assert len(removed) >= 2

    def test_no_branding(self) -> None:
        """Message without branding remains unchanged."""
        text = """Normal commit message

With detailed description.
"""
        result, removed = remove_branding(text)
        assert result == text
        assert len(removed) == 0

    def test_preserve_non_ai_links(self) -> None:
        """Keep non-AI markdown links."""
        text = """Update README

See [documentation](https://example.com) for details.
"""
        result, removed = remove_branding(text)
        assert result == text
        assert len(removed) == 0


class TestSanitizeCommitMessage:
    """Tests for sanitize_commit_message function."""

    def test_both_rules_enabled_default(self) -> None:
        """Both removal rules enabled by default."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        expected = "Fix bug\n"
        result, removed = sanitize_commit_message(text)
        assert result == expected
        assert len(removed["coauthor"]) == 1
        assert len(removed["branding"]) >= 1

    def test_only_coauthor_removal(self) -> None:
        """Only remove co-author, keep branding."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result, removed = sanitize_commit_message(text, keep_branding=True)
        assert "Co-Authored-By" not in result
        assert "Generated with" in result
        assert len(removed["coauthor"]) == 1
        assert len(removed["branding"]) == 0

    def test_only_branding_removal(self) -> None:
        """Only remove branding, keep co-author."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result, removed = sanitize_commit_message(text, keep_coauthor=True)
        assert "Co-Authored-By" in result
        assert "Generated with" not in result
        assert len(removed["coauthor"]) == 0
        assert len(removed["branding"]) >= 1

    def test_both_disabled(self) -> None:
        """Both rules disabled, message unchanged."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result, removed = sanitize_commit_message(text, keep_coauthor=True, keep_branding=True)
        assert result == text
        assert len(removed["coauthor"]) == 0
        assert len(removed["branding"]) == 0

    def test_message_with_only_pollution(self) -> None:
        """Message containing only pollution returns empty."""
        text = """Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result, removed = sanitize_commit_message(text)
        assert result == ""
        assert len(removed["coauthor"]) == 1
        assert len(removed["branding"]) >= 1

    def test_conventional_commit_preserved(self) -> None:
        """Conventional commit format is preserved."""
        text = """feat: Add new authentication flow

Implement OAuth2 login with Google and GitHub providers.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        expected = """feat: Add new authentication flow

Implement OAuth2 login with Google and GitHub providers.
"""
        result, removed = sanitize_commit_message(text)
        assert result == expected
        assert len(removed["coauthor"]) == 1

    def test_preserve_other_trailers(self) -> None:
        """Preserve non-AI trailers like Signed-off-by."""
        text = """Fix security issue

Signed-off-by: Alice <alice@example.com>
Fixes: #123
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        result, removed = sanitize_commit_message(text)
        assert "Signed-off-by" in result
        assert "Fixes:" in result
        assert "Co-Authored-By" not in result
        assert len(removed["coauthor"]) == 1

    def test_multiline_commit_body(self) -> None:
        """Handle multiline commit body correctly."""
        text = """feat: Implement new feature

This is a detailed description
that spans multiple lines.

It includes several paragraphs
to explain the changes.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        result, removed = sanitize_commit_message(text)
        assert "This is a detailed description" in result
        assert "spans multiple lines" in result
        assert "Co-Authored-By" not in result
        assert len(removed["coauthor"]) == 1


class TestPrintFeedback:
    """Tests for _print_feedback function."""

    def test_silent_when_nothing_removed(self) -> None:
        """No output when nothing was removed."""
        removed = {"coauthor": [], "branding": []}
        stderr = io.StringIO()
        sys.stderr = stderr
        try:
            _print_feedback(removed, verbose=False)
            assert stderr.getvalue() == ""
        finally:
            sys.stderr = sys.__stderr__

    def test_minimal_feedback_coauthor_only(self) -> None:
        """Minimal feedback when only co-author removed."""
        removed = {
            "coauthor": ["Co-Authored-By: Claude <ai@example.com>"],
            "branding": [],
        }
        stderr = io.StringIO()
        sys.stderr = stderr
        try:
            _print_feedback(removed, verbose=False)
            output = stderr.getvalue()
            assert "de-ai-agent: Removed AI co-author" in output
            assert "branding" not in output
        finally:
            sys.stderr = sys.__stderr__

    def test_minimal_feedback_both(self) -> None:
        """Minimal feedback when both removed."""
        removed = {
            "coauthor": ["Co-Authored-By: Claude <ai@example.com>"],
            "branding": ["Generated with Claude"],
        }
        stderr = io.StringIO()
        sys.stderr = stderr
        try:
            _print_feedback(removed, verbose=False)
            output = stderr.getvalue()
            assert "de-ai-agent: Removed AI co-author, branding" in output
        finally:
            sys.stderr = sys.__stderr__

    def test_verbose_feedback(self) -> None:
        """Verbose feedback shows details."""
        removed = {
            "coauthor": ["Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"],
            "branding": ["🤖 Generated with [Claude Code](https://claude.com/claude-code)"],
        }
        stderr = io.StringIO()
        sys.stderr = stderr
        try:
            _print_feedback(removed, verbose=True)
            output = stderr.getvalue()
            assert "de-ai-agent: Removed:" in output
            assert "Co-Authored-By: Claude Sonnet 4.5" in output
            assert "Generated with" in output
        finally:
            sys.stderr = sys.__stderr__
