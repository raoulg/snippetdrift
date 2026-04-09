from __future__ import annotations

import re
from pathlib import Path

from loguru import logger

_SENTINEL_RE = re.compile(
    r"(<!--\s*snippetdrift:\s*[^\s#]+#L\d+-\d+)"
    r"(?:\s+hash:[0-9a-f]{8})?"
    r"(?:\s+reviewed:\d{4}-\d{2}-\d{2})?"
    r"(\s*-->)"
)


def write_hash_to_markdown(
    markdown_file: Path,
    line_number: int,
    short_hash: str,
    reviewed_date: str,
) -> None:
    """Rewrite the sentinel comment at line_number in-place with hash and reviewed date."""
    text = markdown_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    idx = line_number - 1
    original = lines[idx]

    new_line = _SENTINEL_RE.sub(
        rf"\g<1> hash:{short_hash} reviewed:{reviewed_date}\g<2>",
        original,
    )

    if new_line == original:
        logger.debug("No change needed at {}:{}", markdown_file, line_number)
        return

    lines[idx] = new_line
    markdown_file.write_text("".join(lines), encoding="utf-8")
    logger.debug("Updated sentinel at {}:{} → hash:{}", markdown_file, line_number, short_hash)
