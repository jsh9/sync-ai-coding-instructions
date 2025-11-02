import os
import time
from pathlib import Path

import pytest

from sync_ai_coding_instructions.main import (
    DEFAULT_FILES,
    DEFAULT_HEADERS,
    SyncResult,
    build_headers,
    main,
    parse_args,
    sync_markdown,
)


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def _build_content(name: str, body: str, headers: dict[str, str]) -> str:
    header = headers[name]
    header_line = header if header.endswith('\n') else f'{header}\n'
    return f'{header_line}{body}'


@pytest.mark.parametrize(
    ('files', 'expected'),
    [
        (
            ['ONE.md', 'TWO.md'],
            {'ONE.md': '# ONE.md', 'TWO.md': '# TWO.md'},
        ),
        (
            ['FILE_ONE.md', 'FILE_TWO.md', 'FILE_THREE.md'],
            {
                'FILE_ONE.md': '# FILE_ONE.md',
                'FILE_TWO.md': '# FILE_TWO.md',
                'FILE_THREE.md': '# FILE_THREE.md',
            },
        ),
    ],
)
def test_build_headers_generates_expected_mapping(
        files: list[str], expected: dict[str, str]
) -> None:
    headers = build_headers(files)
    assert headers == expected


def test_sync_returns_three_when_files_missing(tmp_path: Path) -> None:
    result = sync_markdown(tmp_path, headers=DEFAULT_HEADERS)
    assert result == SyncResult(
        code=3, message='No markdown files found; nothing to synchronize.'
    )
    for name in DEFAULT_HEADERS:
        assert not (tmp_path / name).exists()


def test_sync_creates_missing_files(tmp_path: Path) -> None:
    base_path = tmp_path / 'AGENTS.md'
    _write_file(
        base_path, _build_content('AGENTS.md', 'Body line.\n', DEFAULT_HEADERS)
    )
    result = sync_markdown(tmp_path, headers=DEFAULT_HEADERS)
    assert result.code == 2
    for name, header in DEFAULT_HEADERS.items():
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
        _write_file(path, _build_content(name, body, DEFAULT_HEADERS))
        offset = 5 if name == newest_file else 0
        os.utime(path, (now + offset, now + offset))

    timestamps = {name: (tmp_path / name).stat().st_mtime for name in bodies}
    assert timestamps[newest_file] == max(timestamps.values())
    for name in oldest_files:
        assert timestamps[name] < timestamps[newest_file]

    result = sync_markdown(tmp_path, headers=DEFAULT_HEADERS)
    assert result.code == 1
    expected_body = 'Latest notes.\n'
    expected_content = {
        name: f'{DEFAULT_HEADERS[name]}\n{expected_body}'
        for name in DEFAULT_HEADERS
    }
    for name, expected in expected_content.items():
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == expected


@pytest.mark.parametrize('newest_name', list(DEFAULT_HEADERS))
def test_sync_no_changes_when_already_consistent(
        tmp_path: Path, newest_name: str
) -> None:
    body = 'Shared content.\n'
    now = time.time()
    for offset, name in enumerate(DEFAULT_HEADERS):
        path = tmp_path / name
        _write_file(path, _build_content(name, body, DEFAULT_HEADERS))
        stamp = now + (offset if name == newest_name else 0)
        os.utime(path, (stamp, stamp))

    result = sync_markdown(tmp_path, headers=DEFAULT_HEADERS)
    assert result.code == 0
    for name in DEFAULT_HEADERS:
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == _build_content(name, body, DEFAULT_HEADERS)


def test_cli_argument_parsing_defaults_to_cwd(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    args = parse_args([])
    assert args.path == tmp_path
    assert args.files == DEFAULT_FILES


def test_cli_main_returns_exit_code(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = main([])
    assert isinstance(result, int)


@pytest.mark.parametrize(
    'bad_files',
    [
        'ONLY.md',
        '',
        'SINGLE.md,',
        ',',
    ],
)
def test_parse_args_rejects_invalid_file_lists(bad_files: str) -> None:
    with pytest.raises(SystemExit):
        parse_args(['--files', bad_files])


def test_sync_with_two_files(tmp_path: Path) -> None:
    files = ['ONE.md', 'TWO.md']
    headers = build_headers(files)
    latest = 'TWO.md'
    stale = 'ONE.md'
    _write_file(
        tmp_path / stale, _build_content(stale, 'Old body.\n', headers)
    )
    _write_file(
        tmp_path / latest, _build_content(latest, 'Fresh body.\n', headers)
    )
    os.utime(tmp_path / latest, None)
    os.utime(tmp_path / stale, (0, 0))

    result = sync_markdown(tmp_path, headers=headers)
    assert result.code == 1
    for name in files:
        expected = _build_content(name, 'Fresh body.\n', headers)
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == expected


def test_sync_with_many_files(tmp_path: Path) -> None:
    files = [f'FILE_{index}.md' for index in range(8)]
    headers = build_headers(files)
    freshest = files[-1]
    for index, name in enumerate(files):
        body = f'Body {index}\n'
        _write_file(tmp_path / name, _build_content(name, body, headers))
        os.utime(tmp_path / name, (index, index))

    # make the last file the freshest
    os.utime(tmp_path / freshest, (1000, 1000))
    result = sync_markdown(tmp_path, headers=headers)
    assert result.code == 1
    for name in files:
        expected = _build_content(name, 'Body 7\n', headers)
        content = (tmp_path / name).read_text(encoding='utf-8')
        assert content == expected
