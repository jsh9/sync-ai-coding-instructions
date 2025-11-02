from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

HEADERS: dict[str, str] = {
    'AGENTS.md': '# AGENTS.md',
    'CLAUDE.md': '# CLAUDE.md',
    'GEMINI.md': '# GEMINI.md',
}


@dataclass(frozen=True)
class SyncResult:
    """Status code and optional message produced by a sync run."""

    code: int
    message: str | None = None


def _read_body(path: Path) -> str:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    if not lines:
        return ''

    return ''.join(lines[1:])


def _compose_content(header: str, body: str) -> str:
    header_line = header if header.endswith('\n') else f'{header}\n'
    return f'{header_line}{body}'


def sync_markdown(directory: Path) -> SyncResult:
    """Synchronize target markdown files within ``directory``."""
    directory = directory.resolve()
    targets = {name: directory / name for name in HEADERS}
    existing = {name: path for name, path in targets.items() if path.exists()}

    if not existing:
        return SyncResult(
            code=3,
            message='No markdown files found; nothing to synchronize.',
        )

    if len(existing) < len(targets):
        newest_name = max(
            existing, key=lambda name: existing[name].stat().st_mtime
        )
        base_body = _read_body(existing[newest_name])

        for name, path in targets.items():
            content = _compose_content(HEADERS[name], base_body)
            if not path.exists():
                path.write_text(content, encoding='utf-8')
            else:
                current = path.read_text(encoding='utf-8')
                if current != content:
                    path.write_text(content, encoding='utf-8')

        missing = sorted(set(targets) - set(existing))
        return SyncResult(
            code=2,
            message=f'Created missing file(s): {", ".join(missing)}.',
        )

    newest_name = max(
        existing, key=lambda name: existing[name].stat().st_mtime
    )
    base_body = _read_body(existing[newest_name])
    changes_made = False

    for name, path in targets.items():
        desired = _compose_content(HEADERS[name], base_body)
        current = path.read_text(encoding='utf-8')
        if current != desired:
            path.write_text(desired, encoding='utf-8')
            changes_made = True

    if changes_made:
        return SyncResult(
            code=1,
            message='Synchronized markdown files to match the latest changes.',
        )

    return SyncResult(code=0, message=None)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            'Synchronize AGENTS.md, CLAUDE.md, and GEMINI.md based on the '
            'newest file.'
        ),
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=Path.cwd(),
        help=(
            'Directory containing the markdown files '
            '(defaults to current working directory).'
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    result = sync_markdown(args.path)
    if result.message:
        print(result.message, file=sys.stderr)

    return result.code


if __name__ == '__main__':
    sys.exit(main())
