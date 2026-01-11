"""End-to-end tests for de-ai-agent using temporary git repos."""

import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.slow
class TestE2E:
    """End-to-end tests with actual git repos."""

    def setup_git_repo(self, tmpdir: Any) -> Path:
        """Create and initialize a git repository.

        Args:
            tmpdir: pytest tmpdir fixture

        Returns:
            Path to the git repository
        """
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Configure git user
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Disable global hooksPath to ensure our local hooks run
        subprocess.run(
            ["git", "config", "--local", "core.hooksPath", ".git/hooks"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit to have a valid HEAD
        test_file = repo_path / "test.txt"
        test_file.write_text("initial content\n")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        return repo_path

    def install_hook(self, repo_path: Path, args: list[str] | None = None) -> None:
        """Install de-ai-agent hook in the repository.

        Args:
            repo_path: Path to git repository
            args: Optional arguments to pass to the hook
        """
        hook_path = repo_path / ".git" / "hooks" / "commit-msg"
        hook_path.parent.mkdir(parents=True, exist_ok=True)

        # Create hook script that calls de-ai-agent
        hook_script = "#!/bin/sh\n"
        if args:
            hook_script += f"de-ai-agent {' '.join(args)} \"$1\"\n"
        else:
            hook_script += 'de-ai-agent "$1"\n'

        hook_path.write_text(hook_script)
        hook_path.chmod(0o755)

    def create_commit(self, repo_path: Path, message: str) -> None:
        """Create a commit with the given message.

        Args:
            repo_path: Path to git repository
            message: Commit message
        """
        # Make a change
        test_file = repo_path / "test.txt"
        current = test_file.read_text()
        test_file.write_text(current + "new line\n")

        # Stage changes
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True, capture_output=True)

        # Write message to file to avoid git's default cleanup stripping content
        msg_file = repo_path / ".git" / "COMMIT_MSG_TEST"
        msg_file.write_text(message)

        # Commit using file input with verbatim cleanup to preserve all content
        subprocess.run(
            ["git", "commit", "-F", str(msg_file), "--cleanup=verbatim"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

    def get_last_commit_message(self, repo_path: Path) -> str:
        """Get the last commit message.

        Args:
            repo_path: Path to git repository

        Returns:
            Commit message
        """
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def test_remove_coauthor_from_commit(self, tmpdir: Any) -> None:
        """Commit with AI co-author has it removed."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path)

        message = """Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Co-Authored-By" not in actual_message
        assert "Fix authentication bug" in actual_message

    def test_remove_branding_from_commit(self, tmpdir: Any) -> None:
        """Commit with branding has it removed."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path)

        message = """Add user registration flow

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Generated with" not in actual_message
        assert "Claude Code" not in actual_message
        assert "Add user registration flow" in actual_message

    def test_remove_both_coauthor_and_branding(self, tmpdir: Any) -> None:
        """Commit with both co-author and branding has both removed."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path)

        message = """Implement feature

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Co-Authored-By" not in actual_message
        assert "Generated with" not in actual_message
        assert "Implement feature" in actual_message

    def test_keep_coauthor_flag(self, tmpdir: Any) -> None:
        """--keep-coauthor flag preserves AI co-author."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path, args=["--keep-coauthor"])

        message = """Fix bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Co-Authored-By: Claude Sonnet 4.5" in actual_message

    def test_keep_branding_flag(self, tmpdir: Any) -> None:
        """--keep-branding flag preserves branding."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path, args=["--keep-branding"])

        message = """Add feature

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Generated with" in actual_message or "Claude Code" in actual_message

    def test_clean_commit_unchanged(self, tmpdir: Any) -> None:
        """Clean commit without AI pollution remains unchanged."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path)

        message = """feat: Add new feature

Detailed description of the feature.

Signed-off-by: Test User <test@example.com>
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "feat: Add new feature" in actual_message
        assert "Detailed description" in actual_message
        assert "Signed-off-by" in actual_message

    def test_preserve_human_coauthor(self, tmpdir: Any) -> None:
        """Human co-authors are preserved, only AI removed."""
        repo_path = self.setup_git_repo(tmpdir)
        self.install_hook(repo_path)

        message = """Implement feature

Co-Authored-By: Alice <alice@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
Co-Authored-By: Bob <bob@example.com>
"""
        self.create_commit(repo_path, message)

        actual_message = self.get_last_commit_message(repo_path)
        assert "Co-Authored-By: Alice" in actual_message
        assert "Co-Authored-By: Bob" in actual_message
        assert "Claude Sonnet" not in actual_message
