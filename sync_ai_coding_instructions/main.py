from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_FILES: list[str] = ['AGENTS.md', 'CLAUDE.md', 'GEMINI.md']
DEFAULT_HEADERS: dict[str, str] = {name: f'# {name}' for name in DEFAULT_FILES}


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


def build_headers(file_names: list[str]) -> dict[str, str]:
    """Generate a header mapping for the provided filenames."""
    return {name: f'# {name}' for name in file_names}


def _parse_file_list(value: str) -> list[str]:
    files = [part.strip() for part in value.split(',') if part.strip()]
    if len(files) < 2:  # noqa: PLR2004
        raise ValueError(
            'Provide at least 2 comma-separated filenames for synchronization.'
        )

    return files


def sync_markdown(
        directory: Path, headers: dict[str, str] | None = None
) -> SyncResult:
    """Synchronize target markdown files within ``directory``."""
    active_headers = headers if headers is not None else DEFAULT_HEADERS
    directory = directory.resolve()
    targets = {name: directory / name for name in active_headers}
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
            content = _compose_content(active_headers[name], base_body)
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
        desired = _compose_content(active_headers[name], base_body)
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
    parser.add_argument(
        '--files',
        default=','.join(DEFAULT_FILES),
        help=(
            'Comma-separated list of markdown filenames to synchronize '
            '(minimum two).'
        ),
    )
    args = parser.parse_args(argv)
    try:
        args.files = _parse_file_list(args.files)
    except ValueError as exc:
        parser.error(str(exc))

    return args


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    headers = build_headers(args.files)
    result = sync_markdown(args.path, headers=headers)
    if result.message:
        print(result.message, file=sys.stderr)

    return result.code


if __name__ == '__main__':
    sys.exit(main())
