from __future__ import annotations

from pathlib import Path

from snippetdrift.hasher import compute_hash, hash_lines, read_lines


def test_hash_lines_stable() -> None:
    lines = ["def foo():", "    return 42"]
    short, full = hash_lines(lines)
    assert len(short) == 8
    assert len(full) == 64
    # Should be deterministic
    short2, full2 = hash_lines(lines)
    assert short == short2
    assert full == full2


def test_hash_lines_strips_trailing_whitespace() -> None:
    lines_clean = ["def foo():  ", "    return 42  "]
    lines_dirty = ["def foo():", "    return 42"]
    _, full_clean = hash_lines(lines_clean)
    _, full_dirty = hash_lines(lines_dirty)
    assert full_clean == full_dirty


def test_hash_lines_different_content() -> None:
    short1, _ = hash_lines(["def foo(): return 1"])
    short2, _ = hash_lines(["def foo(): return 2"])
    assert short1 != short2


def test_read_lines(tmp_path: Path) -> None:
    f = tmp_path / "src.py"
    f.write_text("line1\nline2\nline3\nline4\nline5\n")
    lines = read_lines(f, 2, 4)
    assert lines == ["line2", "line3", "line4"]


def test_compute_hash(tmp_path: Path) -> None:
    f = tmp_path / "src.py"
    f.write_text("line1\nline2\nline3\n")
    short, full, lines = compute_hash(f, 1, 3)
    assert len(short) == 8
    assert len(full) == 64
    assert lines == ["line1", "line2", "line3"]
