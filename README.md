# sync-ai-coding-instructions

_Sometimes the brute-force solution is the most elegant._

<!--TOC-->

______________________________________________________________________

**Table of Contents**

- [1. What is this tool?](#1-what-is-this-tool)
- [2. Why should you use this tool?](#2-why-should-you-use-this-tool)
- [3. How to use this tool?](#3-how-to-use-this-tool)
  - [3.1. 3.1 Use as a pre-commit hook](#31-31-use-as-a-pre-commit-hook)
  - [3.2. 3.2 Use from the command line](#32-32-use-from-the-command-line)

______________________________________________________________________

<!--TOC-->

## 1. What is this tool?

This is a simple pre-commit hook or Python CLI tool to syncrhonize different AI
coding assistant instruction files (AGENTS.md, CLAUDE.md, GEMINI.md, ...).

For example, if you only have CLAUDE.md in your repo, this tool would create an
AGENTS.md file and keep them in sync. (Whichever file gets modified last, its
contents will be copied over to the other file(s).)

## 2. Why should you use this tool?

It's best to allow different code contributors to the same project to use their
preferred AI coding tools, so keeping multiple instruction files becomes
necessary. (As of November 2025,
[Claude Code still hasn't adopted AGENTS.md](https://github.com/anthropics/claude-code/issues/6235).)

Unlike other solutions online that uses `@` or symbolic link (non-trivial to
learn and may not always work), this tool uses a brute-force solution
(copy/paste). It's guaranteed to work and has no learning curve. (The
prerequisite is to learn to use
[pre-commit](https://github.com/pre-commit/pre-commit), of course.)

## 3. How to use this tool?

### 3.1. 3.1 Use as a pre-commit hook

1. Install the dependencies for this project (typically within a virtual
   environment).
2. Add this repository to your `.pre-commit-config.yaml`, for example:

```yaml
repos:
    - repo: https://github.com/jsh9/sync-ai-coding-instructions
    rev: <LATEST_VERSION>
    hooks:
        - id: sync-ai-coding-instructions
          # Optional: override the default AGENTS/CLAUDE/GEMINI list.
          # args: [--files, AGENTS.md,CLAUDE.md,GEMINI.md]
```

3. Run `pre-commit install` inside your project to enable the hook.

With this configuration, every commit automatically syncs `AGENTS.md`,
`CLAUDE.md`, and `GEMINI.md` using the newest file as the source.

### 3.2. 3.2 Use from the command line

Install the project (editable install recommended during development):

```bash
pip install sync-ai-coding-instructions
```

Then run the CLI directly in the directory that contains the markdown files:

```bash
sync-ai-coding-instructions
```

You can also point at another directory:

```bash
sync-ai-coding-instructions --path /path/to/project
```

Alternatively, execute via Python without installing:

```bash
python -m sync_ai_coding_instructions.main --path /path/to/project
```

Provide a custom comma-separated file list with `--files`. At least two file
names are required:

```bash
sync-ai-coding-instructions --files AGENTS.md,CLARITY.md,GEMINI.md
```

The command exits with status codes indicating whether files were created,
synced, or untouched (non-zero when files are created or updated).
