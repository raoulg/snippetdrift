from __future__ import annotations

from pathlib import Path

from snippetdrift.writer import sync_code_block, write_hash_to_markdown


def _make_md(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "doc.md"
    f.write_text(content)
    return f


# ---------------------------------------------------------------------------
# write_hash_to_markdown
# ---------------------------------------------------------------------------


def test_write_hash_adds_fields(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-5 -->\n```python\npass\n```\n",
    )
    write_hash_to_markdown(md, 2, "abcd1234", "2025-04-09")
    text = md.read_text()
    assert "hash:abcd1234" in text
    assert "reviewed:2025-04-09" in text


def test_write_hash_overwrites_existing(tmp_path: Path) -> None:
    sentinel = "<!-- snippetdrift: src/a.py#L1-5 hash:00000000 reviewed:2020-01-01 -->"
    md = _make_md(tmp_path, f"# Doc\n{sentinel}\n```python\npass\n```\n")
    write_hash_to_markdown(md, 2, "abcd1234", "2025-04-09")
    text = md.read_text()
    assert "hash:abcd1234" in text
    assert "reviewed:2025-04-09" in text
    assert "00000000" not in text
    assert "2020-01-01" not in text


# ---------------------------------------------------------------------------
# sync_code_block
# ---------------------------------------------------------------------------


def test_sync_fills_empty_block(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-3 -->\n```python\n```\n",
    )
    changed = sync_code_block(md, 2, ["def foo():", "    pass"])
    assert changed
    text = md.read_text()
    assert "def foo():" in text
    assert "    pass" in text


def test_sync_replaces_existing_content(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-2 -->\n```python\nold_line\n```\n",
    )
    changed = sync_code_block(md, 2, ["new_line"])
    assert changed
    text = md.read_text()
    assert "new_line" in text
    assert "old_line" not in text


def test_sync_preserves_language_tag(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-1 -->\n```typescript\nold\n```\n",
    )
    sync_code_block(md, 2, ["const x = 1"])
    text = md.read_text()
    assert "```typescript" in text


def test_sync_no_change_when_already_current(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-1 -->\n```python\nx = 1\n```\n",
    )
    changed = sync_code_block(md, 2, ["x = 1"])
    assert not changed


def test_sync_no_fence_returns_false(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n<!-- snippetdrift: src/a.py#L1-1 -->\nNo code block here.\n",
    )
    changed = sync_code_block(md, 2, ["x = 1"])
    assert not changed


def test_sync_preserves_surrounding_content(tmp_path: Path) -> None:
    md = _make_md(
        tmp_path,
        "# Doc\n\nIntro text.\n\n"
        "<!-- snippetdrift: src/a.py#L1-1 -->\n```python\nold\n```\n\n"
        "Outro text.\n",
    )
    sync_code_block(md, 5, ["new"])
    text = md.read_text()
    assert "Intro text." in text
    assert "Outro text." in text
    assert "new" in text
    assert "old" not in text
