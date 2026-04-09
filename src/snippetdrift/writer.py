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

# Matches the opening fence: optional whitespace, 3+ backticks, optional language tag
_FENCE_OPEN_RE = re.compile(r"^(\s*`{3,})(\w*)\s*$")


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


def sync_code_block(
    markdown_file: Path,
    sentinel_line: int,
    source_lines: list[str],
) -> bool:
    """Replace the content of the fenced code block immediately following the sentinel.

    Returns True if the file was modified, False if content was already up to date
    or no code block was found.
    """
    text = markdown_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Find the opening fence on the line(s) after the sentinel
    fence_open_idx: int | None = None
    fence_marker: str = "```"
    for i in range(sentinel_line, min(sentinel_line + 3, len(lines))):
        m = _FENCE_OPEN_RE.match(lines[i].rstrip("\n\r"))
        if m:
            fence_open_idx = i
            fence_marker = m.group(1)  # the backtick string, e.g. "```"
            lang = m.group(2)
            break

    if fence_open_idx is None:
        logger.warning(
            "No fenced code block found after sentinel at {}:{}", markdown_file, sentinel_line
        )
        return False

    # Find the matching closing fence
    fence_close_idx: int | None = None
    for i in range(fence_open_idx + 1, len(lines)):
        stripped = lines[i].rstrip("\n\r")
        if stripped.startswith(fence_marker) and stripped.strip("`") == "":
            fence_close_idx = i
            break

    if fence_close_idx is None:
        logger.warning(
            "No closing fence found for code block after sentinel at {}:{}",
            markdown_file,
            sentinel_line,
        )
        return False

    # Build the replacement block
    eol = _detect_eol(lines[fence_open_idx])
    open_fence = f"{fence_marker}{lang}{eol}"
    close_fence = f"{fence_marker}{eol}"
    new_content_lines = [line + eol for line in source_lines]

    new_block = [open_fence] + new_content_lines + [close_fence]
    old_block = lines[fence_open_idx : fence_close_idx + 1]

    if new_block == old_block:
        logger.debug("Code block at {}:{} already up to date", markdown_file, sentinel_line)
        return False

    lines[fence_open_idx : fence_close_idx + 1] = new_block
    markdown_file.write_text("".join(lines), encoding="utf-8")
    logger.debug("Synced code block at {}:{}", markdown_file, sentinel_line)
    return True


def _detect_eol(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\r"):
        return "\r"
    return "\n"
