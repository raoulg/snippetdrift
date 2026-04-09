from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from snippetdrift.parser import parse_file


@pytest.fixture
def md_with_initialized(tmp_path: Path) -> Path:
    f = tmp_path / "doc.md"
    f.write_text(
        "# Doc\n"
        "<!-- snippetdrift: src/api/models.py#L10-20 hash:a1b2c3d4 reviewed:2025-04-01 -->\n"
        "```python\npass\n```\n"
    )
    return f


@pytest.fixture
def md_uninitialized(tmp_path: Path) -> Path:
    f = tmp_path / "doc.md"
    f.write_text("# Doc\n<!-- snippetdrift: src/api/models.py#L10-20 -->\n```python\npass\n```\n")
    return f


def test_parse_initialized(md_with_initialized: Path) -> None:
    refs = parse_file(md_with_initialized)
    assert len(refs) == 1
    ref = refs[0]
    assert ref.source_file == Path("src/api/models.py")
    assert ref.start_line == 10
    assert ref.end_line == 20
    assert ref.stored_hash == "a1b2c3d4"
    assert ref.reviewed_date == datetime(2025, 4, 1)
    assert ref.line_number == 2


def test_parse_uninitialized(md_uninitialized: Path) -> None:
    refs = parse_file(md_uninitialized)
    assert len(refs) == 1
    ref = refs[0]
    assert ref.stored_hash is None
    assert ref.reviewed_date is None


def test_parse_multiple(tmp_path: Path) -> None:
    f = tmp_path / "multi.md"
    f.write_text(
        "<!-- snippetdrift: src/a.py#L1-5 hash:aaaabbbb reviewed:2025-01-01 -->\n"
        "```python\npass\n```\n"
        "<!-- snippetdrift: src/b.py#L6-10 -->\n"
        "```python\npass\n```\n"
    )
    refs = parse_file(f)
    assert len(refs) == 2
    assert refs[0].source_file == Path("src/a.py")
    assert refs[1].source_file == Path("src/b.py")
    assert refs[0].stored_hash == "aaaabbbb"
    assert refs[1].stored_hash is None


def test_parse_no_sentinels(tmp_path: Path) -> None:
    f = tmp_path / "plain.md"
    f.write_text("# Just a plain markdown file\n\nNo snippets here.\n")
    refs = parse_file(f)
    assert refs == []
