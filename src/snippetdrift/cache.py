from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from snippetdrift.models import CacheEntry, CacheIndex


def find_repo_root(start: Path) -> Path:
    """Walk up from start to find the repo root (contains .git or pyproject.toml)."""
    current = start if start.is_dir() else start.parent
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return current


def cache_dir(repo_root: Path) -> Path:
    return repo_root / ".snippetdrift_cache"


def snippets_dir(repo_root: Path) -> Path:
    return cache_dir(repo_root) / "snippets"


def index_path(repo_root: Path) -> Path:
    return cache_dir(repo_root) / "index.json"


def load_index(repo_root: Path) -> CacheIndex:
    path = index_path(repo_root)
    if not path.exists():
        return CacheIndex()
    try:
        return CacheIndex.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Could not parse cache index: {}", e)
        return CacheIndex()


def save_index(repo_root: Path, index: CacheIndex) -> None:
    idx_path = index_path(repo_root)
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(index.model_dump_json(indent=2), encoding="utf-8")
    logger.debug("Saved cache index to {}", idx_path)


def save_snippet_text(repo_root: Path, full_hash: str, lines: list[str]) -> None:
    snip_dir = snippets_dir(repo_root)
    snip_dir.mkdir(parents=True, exist_ok=True)
    (snip_dir / f"{full_hash}.txt").write_text("\n".join(lines), encoding="utf-8")


def load_snippet_text(repo_root: Path, full_hash: str) -> list[str] | None:
    path = snippets_dir(repo_root) / f"{full_hash}.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").splitlines()


def upsert_entry(
    index: CacheIndex,
    markdown_file: str,
    sentinel_line: int,
    source_file: str,
    lines: str,
    full_hash: str,
    short_hash: str,
    reviewed_date: str,
) -> CacheIndex:
    """Replace or insert a cache entry, returning updated index."""
    new_entry = CacheEntry(
        markdown_file=markdown_file,
        sentinel_line=sentinel_line,
        source_file=source_file,
        lines=lines,
        full_hash=full_hash,
        short_hash=short_hash,
        reviewed_date=reviewed_date,
        accepted_at=datetime.now(UTC).isoformat(),
    )
    updated = [
        e
        for e in index.entries
        if not (e.markdown_file == markdown_file and e.sentinel_line == sentinel_line)
    ]
    updated.append(new_entry)
    return CacheIndex(entries=updated)


def find_entry(index: CacheIndex, markdown_file: str, sentinel_line: int) -> CacheEntry | None:
    for e in index.entries:
        if e.markdown_file == markdown_file and e.sentinel_line == sentinel_line:
            return e
    return None


def relative_str(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def write_cache_entry(
    repo_root: Path,
    markdown_file: Path,
    sentinel_line: int,
    source_file: Path,
    start_line: int,
    end_line: int,
    short_hash: str,
    full_hash: str,
    reviewed_date: str,
    source_lines: list[str],
) -> None:
    index = load_index(repo_root)
    md_str = relative_str(markdown_file, repo_root)
    src_str = relative_str(source_file, repo_root)
    lines_str = f"{start_line}-{end_line}"
    index = upsert_entry(
        index, md_str, sentinel_line, src_str, lines_str, full_hash, short_hash, reviewed_date
    )
    save_index(repo_root, index)
    save_snippet_text(repo_root, full_hash, source_lines)


def read_cached_snippet(
    repo_root: Path, markdown_file: Path, sentinel_line: int
) -> tuple[CacheEntry | None, list[str] | None]:
    index = load_index(repo_root)
    md_str = relative_str(markdown_file, repo_root)
    entry = find_entry(index, md_str, sentinel_line)
    if entry is None:
        return None, None
    lines = load_snippet_text(repo_root, entry.full_hash)
    return entry, lines


def get_gitignore_suggestion() -> str:
    return ".snippetdrift_cache/"


def ensure_gitignore(repo_root: Path) -> None:
    gitignore = repo_root / ".gitignore"
    suggestion = get_gitignore_suggestion()
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if suggestion in content:
            return
        gitignore.write_text(content.rstrip() + f"\n{suggestion}\n", encoding="utf-8")
    else:
        gitignore.write_text(f"{suggestion}\n", encoding="utf-8")
    logger.debug("Added {} to .gitignore", suggestion)


def load_all_entries(repo_root: Path) -> list[CacheEntry]:
    return load_index(repo_root).entries


def clear_entries_for_file(repo_root: Path, markdown_file: Path) -> None:
    index = load_index(repo_root)
    md_str = relative_str(markdown_file, repo_root)
    updated = [e for e in index.entries if e.markdown_file != md_str]
    save_index(repo_root, CacheIndex(entries=updated))


def get_cache_entry(repo_root: Path, markdown_file: Path, sentinel_line: int) -> CacheEntry | None:
    index = load_index(repo_root)
    md_str = relative_str(markdown_file, repo_root)
    return find_entry(index, md_str, sentinel_line)


def remove_cache_entry(repo_root: Path, markdown_file: Path, sentinel_line: int) -> None:
    index = load_index(repo_root)
    md_str = relative_str(markdown_file, repo_root)
    updated = [
        e
        for e in index.entries
        if not (e.markdown_file == md_str and e.sentinel_line == sentinel_line)
    ]
    save_index(repo_root, CacheIndex(entries=updated))


def dump_index_json(repo_root: Path) -> str:
    return json.dumps(load_index(repo_root).model_dump(), indent=2)
