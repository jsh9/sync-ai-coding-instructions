import os
import time
from pathlib import Path

import pytest

from sync_ai_coding_instructions.main import (
    HEADERS,
    SyncResult,
    main,
    parse_args,
    sync_markdown,
)


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def _build_content(name: str, body: str) -> str:
    header = HEADERS[name]
    header_line = header if header.endswith('\n') else f'{header}\n'
    return f'{header_line}{body}'


def test_sync_returns_three_when_files_missing(tmp_path: Path) -> None:
    result = sync_markdown(tmp_path)
    assert result == SyncResult(
        code=3, message='No markdown files found; nothing to synchronize.'
    )
    for name in HEADERS:
        assert not (tmp_path / name).exists()


def test_sync_creates_missing_files(tmp_path: Path) -> None:
    base_path = tmp_path / 'AGENTS.md'
    _write_file(base_path, _build_content('AGENTS.md', 'Body line.\n'))
    result = sync_markdown(tmp_path)
    assert result.code == 2
    for name, header in HEADERS.items():
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content.startswith(f'{header}\n')
        assert content.endswith('Body line.\n')


def test_sync_updates_outdated_files(tmp_path: Path) -> None:
    now = time.time()
    newest_file = 'GEMINI.md'
    oldest_files = ['AGENTS.md', 'CLAUDE.md']
    bodies = {
        'AGENTS.md': 'Old body.\n',
        'CLAUDE.md': 'Out of date.\n',
        newest_file: 'Latest notes.\n',
    }
    for name, body in bodies.items():
        path = tmp_path / name
        _write_file(path, _build_content(name, body))
        offset = 5 if name == newest_file else 0
        os.utime(path, (now + offset, now + offset))

    timestamps = {name: (tmp_path / name).stat().st_mtime for name in bodies}
    assert timestamps[newest_file] == max(timestamps.values())
    for name in oldest_files:
        assert timestamps[name] < timestamps[newest_file]

    result = sync_markdown(tmp_path)
    assert result.code == 1
    expected_body = 'Latest notes.\n'
    expected_content = {
        name: f'{HEADERS[name]}\n{expected_body}' for name in HEADERS
    }
    for name, expected in expected_content.items():
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == expected


@pytest.mark.parametrize('newest_name', list(HEADERS))
def test_sync_no_changes_when_already_consistent(
        tmp_path: Path, newest_name: str
) -> None:
    body = 'Shared content.\n'
    now = time.time()
    for offset, name in enumerate(HEADERS):
        path = tmp_path / name
        _write_file(path, _build_content(name, body))
        stamp = now + (offset if name == newest_name else 0)
        os.utime(path, (stamp, stamp))

    result = sync_markdown(tmp_path)
    assert result.code == 0
    for name in HEADERS:
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == _build_content(name, body)


def test_cli_argument_parsing_defaults_to_cwd(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    args = parse_args([])
    assert args.path == tmp_path


def test_cli_main_returns_exit_code(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = main([])
    assert isinstance(result, int)
