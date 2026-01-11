# de-ai-agent

[![CI](https://github.com/kwesolowski/de-ai-agent/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/kwesolowski/de-ai-agent/actions/workflows/ci.yml)

Pre-commit hook that removes AI pollution from commit messages.

## Problem

Analysis of 40 million pull requests shows 1-in-7 contain AI artifacts. Forced attribution (`Co-Authored-By: Claude...`) and branding footers (`Generated with...`) clutter git history and conflict with organizational commit standards. See [ai-git-pollution-review.md](ai-git-pollution-review.md) for detailed analysis.

## What It Does

- Removes `Co-Authored-By` AI attribution (Claude, GPT, Copilot, Aider, etc.)
- Removes "Generated with..." branding footers and links
- Configurable per-rule via command-line args

## Installation

### Via pre-commit Framework (Recommended)

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/kwesolowski/de-ai-agent
  rev: master  # Use specific commit SHA in production
  hooks:
    - id: de-ai-agent
```

Then install the hook:

```bash
pre-commit install --hook-type commit-msg
```

### Standalone

Install the package:

```bash
pip install git+https://github.com/kwesolowski/de-ai-agent.git
```

Create `.git/hooks/commit-msg`:

```bash
#!/bin/sh
de-ai-agent "$1"
```

Make it executable:

```bash
chmod +x .git/hooks/commit-msg
```

## Configuration

Both removal rules are enabled by default. Keep specific elements using args:

```yaml
- repo: https://github.com/kwesolowski/de-ai-agent
  rev: master
  hooks:
    - id: de-ai-agent
      args: ['--keep-coauthor']  # Keep co-author lines, remove branding
```

## Examples

### Co-Author Removal

**Before:**

```
Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**After:**

```
Fix authentication bug
```

### Branding Removal

**Before:**

```
Add user registration flow

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**After:**

```
Add user registration flow
```

## Configuration Reference

| Argument          | Default Behavior | Description                                     |
| ----------------- | ---------------- | ----------------------------------------------- |
| `--keep-coauthor` | Remove           | Keep `Co-Authored-By` lines with AI agent names |
| `--keep-branding` | Remove           | Keep "Generated with..." footers and tool links |

## License

MIT
