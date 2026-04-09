from __future__ import annotations

from pathlib import Path

from snippetdrift.checker import check_snippet
from snippetdrift.hasher import hash_lines
from snippetdrift.models import SnippetRef


def _make_source(tmp_path: Path, lines: list[str]) -> Path:
    f = tmp_path / "src.py"
    f.write_text("\n".join(lines) + "\n")
    return f


def _make_ref(
    md_file: Path,
    source_file: Path,
    stored_hash: str | None,
) -> SnippetRef:
    return SnippetRef(
        markdown_file=md_file,
        line_number=2,
        source_file=source_file,
        start_line=1,
        end_line=3,
        stored_hash=stored_hash,
        reviewed_date=None,
    )


def test_check_ok(tmp_path: Path) -> None:
    source_lines = ["def foo():", "    pass", "    return None"]
    src = _make_source(tmp_path, source_lines)
    short_hash, _ = hash_lines(source_lines)

    md = tmp_path / "doc.md"
    md.write_text("")
    ref = _make_ref(md, src, short_hash)

    result = check_snippet(ref, tmp_path)
    assert result.status == "ok"
    assert result.current_hash == short_hash


def test_check_drifted(tmp_path: Path) -> None:
    source_lines = ["def foo():", "    pass", "    return None"]
    src = _make_source(tmp_path, source_lines)

    md = tmp_path / "doc.md"
    md.write_text("")
    ref = _make_ref(md, src, "00000000")

    result = check_snippet(ref, tmp_path)
    assert result.status == "drifted"


def test_check_uninitialized(tmp_path: Path) -> None:
    source_lines = ["x = 1", "y = 2", "z = 3"]
    src = _make_source(tmp_path, source_lines)

    md = tmp_path / "doc.md"
    md.write_text("")
    ref = _make_ref(md, src, None)

    result = check_snippet(ref, tmp_path)
    assert result.status == "uninitialized"


def test_check_source_missing(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("")
    ref = _make_ref(md, Path("nonexistent.py"), "abcd1234")

    result = check_snippet(ref, tmp_path)
    assert result.status == "source_missing"
