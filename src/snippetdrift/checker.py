from __future__ import annotations

from pathlib import Path

from loguru import logger

from snippetdrift.cache import find_repo_root, write_cache_entry
from snippetdrift.hasher import compute_hash
from snippetdrift.models import CheckReport, SnippetRef, SnippetResult
from snippetdrift.parser import collect_markdown_files, parse_file


def check_snippet(ref: SnippetRef, repo_root: Path) -> SnippetResult:
    """Check a single snippet ref and return a result."""
    source_abs = repo_root / ref.source_file

    if not source_abs.exists():
        logger.debug("Source file missing: {}", source_abs)
        return SnippetResult(
            ref=ref,
            current_hash="",
            status="source_missing",
            source_lines=[],
        )

    short_hash, _full_hash, source_lines = compute_hash(source_abs, ref.start_line, ref.end_line)
    logger.debug(
        "{}#L{}-{} → current={} stored={}",
        ref.source_file,
        ref.start_line,
        ref.end_line,
        short_hash,
        ref.stored_hash,
    )

    if ref.stored_hash is None:
        status = "uninitialized"
    elif short_hash == ref.stored_hash:
        status = "ok"
    else:
        status = "drifted"

    return SnippetResult(
        ref=ref,
        current_hash=short_hash,
        status=status,
        source_lines=source_lines,
    )


def run_check(path: Path) -> CheckReport:
    """Scan markdown files under path and return a full CheckReport."""
    repo_root = find_repo_root(path)
    md_files = collect_markdown_files(path)
    logger.debug("Scanning {} markdown files under {}", len(md_files), path)

    results: list[SnippetResult] = []
    for md_file in md_files:
        refs = parse_file(md_file)
        for ref in refs:
            result = check_snippet(ref, repo_root)
            results.append(result)

    return CheckReport(scanned_files=md_files, results=results)


def run_init(path: Path) -> list[SnippetResult]:
    """Initialize uninitialized snippets: write hash+reviewed into the markdown."""
    from snippetdrift.writer import write_hash_to_markdown

    repo_root = find_repo_root(path)
    md_files = collect_markdown_files(path)
    initialized: list[SnippetResult] = []

    for md_file in md_files:
        refs = parse_file(md_file)
        for ref in refs:
            if ref.stored_hash is not None:
                logger.debug(
                    "Skipping already-initialized snippet at {}:{}", md_file, ref.line_number
                )
                continue

            source_abs = repo_root / ref.source_file
            if not source_abs.exists():
                logger.warning("Source file missing: {}", source_abs)
                continue

            short_hash, full_hash, source_lines = compute_hash(
                source_abs, ref.start_line, ref.end_line
            )
            today = _today_str()

            write_hash_to_markdown(md_file, ref.line_number, short_hash, today)
            write_cache_entry(
                repo_root,
                md_file,
                ref.line_number,
                ref.source_file,
                ref.start_line,
                ref.end_line,
                short_hash,
                full_hash,
                today,
                source_lines,
            )

            result = SnippetResult(
                ref=ref,
                current_hash=short_hash,
                status="ok",
                source_lines=source_lines,
            )
            initialized.append(result)
            logger.debug("Initialized {}:{} → {}", md_file, ref.line_number, short_hash)

    return initialized


def run_accept(path: Path, snippet_filter: str | None = None) -> list[SnippetResult]:
    """Accept drifted snippets: rewrite hash+reviewed in markdown and update cache."""
    from snippetdrift.writer import write_hash_to_markdown

    repo_root = find_repo_root(path)
    md_files = collect_markdown_files(path)
    accepted: list[SnippetResult] = []

    for md_file in md_files:
        refs = parse_file(md_file)
        for ref in refs:
            if snippet_filter and str(ref.source_file) != snippet_filter:
                continue

            source_abs = repo_root / ref.source_file
            if not source_abs.exists():
                logger.warning("Source file missing: {}", source_abs)
                continue

            short_hash, full_hash, source_lines = compute_hash(
                source_abs, ref.start_line, ref.end_line
            )
            today = _today_str()

            write_hash_to_markdown(md_file, ref.line_number, short_hash, today)
            write_cache_entry(
                repo_root,
                md_file,
                ref.line_number,
                ref.source_file,
                ref.start_line,
                ref.end_line,
                short_hash,
                full_hash,
                today,
                source_lines,
            )

            result = SnippetResult(
                ref=ref,
                current_hash=short_hash,
                status="ok",
                source_lines=source_lines,
            )
            accepted.append(result)

    return accepted


def _today_str() -> str:
    from datetime import date

    return date.today().isoformat()
