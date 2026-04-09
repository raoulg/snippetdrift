from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from loguru import logger

from snippetdrift.models import SnippetRef

# <!-- snippetdrift: src/api/models.py#L45-60 hash:a3f9b2c1 reviewed:2025-04-09 -->
_SENTINEL_RE = re.compile(
    r"<!--\s*snippetdrift:\s*(?P<source>[^\s#]+)#L(?P<start>\d+)-(?P<end>\d+)"
    r"(?:\s+hash:(?P<hash>[0-9a-f]{8}))?"
    r"(?:\s+reviewed:(?P<reviewed>\d{4}-\d{2}-\d{2}))?"
    r"\s*-->"
)


def parse_file(markdown_file: Path) -> list[SnippetRef]:
    """Parse all snippetdrift sentinel comments from a markdown file."""
    refs: list[SnippetRef] = []
    text = markdown_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    for i, line in enumerate(lines, start=1):
        m = _SENTINEL_RE.search(line)
        if not m:
            continue

        source_path = Path(m.group("source"))
        start_line = int(m.group("start"))
        end_line = int(m.group("end"))
        stored_hash = m.group("hash")
        reviewed_str = m.group("reviewed")
        reviewed_date: date | None = date.fromisoformat(reviewed_str) if reviewed_str else None

        logger.debug(
            "Found sentinel at {}:{} → {}#L{}-{}",
            markdown_file,
            i,
            source_path,
            start_line,
            end_line,
        )

        refs.append(
            SnippetRef(
                markdown_file=markdown_file,
                line_number=i,
                source_file=source_path,
                start_line=start_line,
                end_line=end_line,
                stored_hash=stored_hash,
                reviewed_date=reviewed_date,
            )
        )

    return refs


def collect_markdown_files(path: Path) -> list[Path]:
    """Return all .md files under path (recursive if directory)."""
    if path.is_file():
        return [path] if path.suffix == ".md" else []
    return sorted(path.rglob("*.md"))
