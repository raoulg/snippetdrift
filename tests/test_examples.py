from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from snippetdrift.checker import run_accept, run_check, run_init, run_sync
from snippetdrift.models import CheckReport


@pytest.fixture
def example_tree(tmp_path: Path) -> tuple[Path, Path]:
    """Copy the examples directory into a tmp dir, returning (docs_dir, src_dir).

    Places a pyproject.toml marker at tmp_path so find_repo_root correctly
    identifies tmp_path as the repo root.
    """
    repo_root = Path(__file__).parent.parent
    examples = repo_root / "examples"

    src_dst = tmp_path / "examples" / "src" / "api"
    docs_dst = tmp_path / "examples" / "docs"
    src_dst.mkdir(parents=True)
    docs_dst.mkdir(parents=True)

    # Marker so find_repo_root stops here
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    shutil.copy(examples / "src" / "api" / "models.py", src_dst / "models.py")

    # Write the markdown from scratch so tests are never affected by the
    # state of the real examples/docs/api_guide.md (which the linter may modify).
    (docs_dst / "api_guide.md").write_text(
        "# Ingestion API Guide\n"
        "\n"
        "<!-- snippetdrift: examples/src/api/models.py#L27-34 -->\n"
        "```python\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "<!-- snippetdrift: examples/src/api/models.py#L36-43 -->\n"
        "```python\n"
        "```\n"
    )

    # Also copy the drifted file for later use
    shutil.copy(
        examples / "src" / "api" / "models_drifted.py",
        src_dst / "models_drifted.py",
    )

    return docs_dst, src_dst


def test_init_writes_hashes(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree

    results = run_init(docs_dir)
    assert len(results) == 2, "Should initialize exactly 2 snippets"
    for r in results:
        assert r.status == "ok"
        assert len(r.current_hash) == 8

    md = docs_dir / "api_guide.md"
    text = md.read_text()
    for r in results:
        assert r.current_hash in text, f"Hash {r.current_hash!r} not written to markdown"


def test_init_syncs_code_blocks_by_default(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree

    run_init(docs_dir)

    text = (docs_dir / "api_guide.md").read_text()
    assert "class IngestRequest" in text
    assert "class IngestResponse" in text


def test_init_no_sync_leaves_blocks_empty(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree

    # Blocks should contain nothing between ``` markers after fixture setup
    run_init(docs_dir, sync=False)

    text = (docs_dir / "api_guide.md").read_text()
    # Hashes should be written
    assert "hash:" in text
    # But original code block content should not have been injected
    assert "class IngestRequest" not in text


def test_check_all_ok_after_init(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree
    run_init(docs_dir)

    report = run_check(docs_dir)
    assert not report.has_drift
    assert report.summary.get("ok", 0) == 2


def test_sync_fills_code_blocks(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree

    results = run_sync(docs_dir)
    assert len(results) == 2

    text = (docs_dir / "api_guide.md").read_text()
    assert "class IngestRequest" in text
    assert "class IngestResponse" in text


def test_sync_is_idempotent(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, _src_dir = example_tree

    run_sync(docs_dir)
    second = run_sync(docs_dir)
    # Second run reports no changes
    assert second == []


def test_drift_detected_after_source_change(
    example_tree: tuple[Path, Path], tmp_path: Path
) -> None:
    docs_dir, src_dir = example_tree
    run_init(docs_dir)

    # Simulate drift by replacing models.py with the drifted version
    shutil.copy(src_dir / "models_drifted.py", src_dir / "models.py")

    report = run_check(docs_dir)
    assert report.has_drift, "Drift should be detected after source change"

    drifted = [r for r in report.results if r.status == "drifted"]
    assert len(drifted) >= 1

    drifted_sources = [str(r.ref.source_file) for r in drifted]
    assert any("models.py" in s for s in drifted_sources)


def test_accept_sync_resolves_drift(example_tree: tuple[Path, Path], tmp_path: Path) -> None:
    docs_dir, src_dir = example_tree
    run_init(docs_dir)

    shutil.copy(src_dir / "models_drifted.py", src_dir / "models.py")

    accepted = run_accept(docs_dir, sync=True)
    assert len(accepted) == 2

    # Code blocks should now contain content from the drifted version
    text = (docs_dir / "api_guide.md").read_text()
    assert "IngestMetadata" in text  # new class only in drifted version

    # Check should now pass
    report = run_check(docs_dir)
    assert not report.has_drift


def test_check_returns_exit_code_via_has_drift(
    example_tree: tuple[Path, Path], tmp_path: Path
) -> None:
    docs_dir, src_dir = example_tree
    run_init(docs_dir)
    shutil.copy(src_dir / "models_drifted.py", src_dir / "models.py")

    report = run_check(docs_dir)
    assert isinstance(report, CheckReport)
    assert report.has_drift
