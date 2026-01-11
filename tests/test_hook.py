"""Unit tests for de-ai-agent hook."""

from de_ai_agent.hook import remove_branding, remove_coauthor, sanitize_commit_message


class TestRemoveCoauthor:
    """Tests for remove_coauthor function."""

    def test_remove_claude_coauthor(self) -> None:
        """Remove Claude co-author attribution."""
        text = """Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        expected = "Fix authentication bug\n"
        assert remove_coauthor(text) == expected

    def test_remove_gpt_coauthor(self) -> None:
        """Remove GPT co-author attribution."""
        text = """Add new feature

Co-Authored-By: GPT-4 <ai@openai.com>
"""
        expected = "Add new feature\n"
        assert remove_coauthor(text) == expected

    def test_remove_copilot_coauthor(self) -> None:
        """Remove GitHub Copilot co-author attribution."""
        text = """Refactor code

Co-Authored-By: GitHub Copilot <copilot@github.com>
"""
        expected = "Refactor code\n"
        assert remove_coauthor(text) == expected

    def test_remove_aider_coauthor(self) -> None:
        """Remove Aider co-author attribution."""
        text = """Update config

Co-Authored-By: aider <aider@example.com>
"""
        expected = "Update config\n"
        assert remove_coauthor(text) == expected

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
        assert remove_coauthor(text) == expected

    def test_no_coauthor(self) -> None:
        """Message without co-author remains unchanged."""
        text = """Simple commit message

This is a detailed description.
"""
        assert remove_coauthor(text) == text

    def test_empty_message(self) -> None:
        """Empty message returns empty string."""
        assert remove_coauthor("") == ""

    def test_case_insensitive(self) -> None:
        """Pattern matching is case insensitive."""
        text = """Fix bug

Co-Authored-By: claude assistant <ai@example.com>
"""
        expected = "Fix bug\n"
        assert remove_coauthor(text) == expected


class TestRemoveBranding:
    """Tests for remove_branding function."""

    def test_remove_claude_code_link(self) -> None:
        """Remove 'Generated with Claude Code' markdown link."""
        text = """Add user registration

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        expected = "Add user registration\n"
        assert remove_branding(text) == expected

    def test_remove_plain_generated_text(self) -> None:
        """Remove plain 'Generated with' text."""
        text = """Update docs

Generated with Claude AI
"""
        expected = "Update docs\n"
        assert remove_branding(text) == expected

    def test_remove_emoji_branding(self) -> None:
        """Remove emoji + generated branding."""
        text = """Fix typo

✨ Generated with Cursor AI
"""
        expected = "Fix typo\n"
        assert remove_branding(text) == expected

    def test_remove_multiple_branding_lines(self) -> None:
        """Remove multiple branding lines."""
        text = """Commit message

Generated with Claude
🤖 Generated with [AI Assistant](https://example.com)
"""
        expected = "Commit message\n"
        assert remove_branding(text) == expected

    def test_no_branding(self) -> None:
        """Message without branding remains unchanged."""
        text = """Normal commit message

With detailed description.
"""
        assert remove_branding(text) == text

    def test_preserve_non_ai_links(self) -> None:
        """Keep non-AI markdown links."""
        text = """Update README

See [documentation](https://example.com) for details.
"""
        assert remove_branding(text) == text


class TestSanitizeCommitMessage:
    """Tests for sanitize_commit_message function."""

    def test_both_rules_enabled_default(self) -> None:
        """Both removal rules enabled by default."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        expected = "Fix bug\n"
        result = sanitize_commit_message(text)
        assert result == expected

    def test_only_coauthor_removal(self) -> None:
        """Only remove co-author, keep branding."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result = sanitize_commit_message(text, keep_branding=True)
        assert "Co-Authored-By" not in result
        assert "Generated with" in result

    def test_only_branding_removal(self) -> None:
        """Only remove branding, keep co-author."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result = sanitize_commit_message(text, keep_coauthor=True)
        assert "Co-Authored-By" in result
        assert "Generated with" not in result

    def test_both_disabled(self) -> None:
        """Both rules disabled, message unchanged."""
        text = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result = sanitize_commit_message(text, keep_coauthor=True, keep_branding=True)
        assert result == text

    def test_message_with_only_pollution(self) -> None:
        """Message containing only pollution returns empty."""
        text = """Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        result = sanitize_commit_message(text)
        assert result == ""

    def test_conventional_commit_preserved(self) -> None:
        """Conventional commit format is preserved."""
        text = """feat: Add new authentication flow

Implement OAuth2 login with Google and GitHub providers.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        expected = """feat: Add new authentication flow

Implement OAuth2 login with Google and GitHub providers.
"""
        result = sanitize_commit_message(text)
        assert result == expected

    def test_preserve_other_trailers(self) -> None:
        """Preserve non-AI trailers like Signed-off-by."""
        text = """Fix security issue

Signed-off-by: Alice <alice@example.com>
Fixes: #123
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        result = sanitize_commit_message(text)
        assert "Signed-off-by" in result
        assert "Fixes:" in result
        assert "Co-Authored-By" not in result

    def test_multiline_commit_body(self) -> None:
        """Handle multiline commit body correctly."""
        text = """feat: Implement new feature

This is a detailed description
that spans multiple lines.

It includes several paragraphs
to explain the changes.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        result = sanitize_commit_message(text)
        assert "This is a detailed description" in result
        assert "spans multiple lines" in result
        assert "Co-Authored-By" not in result
