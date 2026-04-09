from __future__ import annotations

import hashlib
from pathlib import Path


def hash_lines(lines: list[str]) -> tuple[str, str]:
    """Return (short_hash, full_hash) for a list of source lines.

    Trailing whitespace is stripped from each line before hashing.
    """
    normalized = "\n".join(line.rstrip() for line in lines)
    full = hashlib.sha256(normalized.encode()).hexdigest()
    return full[:8], full


def read_lines(source_file: Path, start_line: int, end_line: int) -> list[str]:
    """Read lines [start_line, end_line] (1-indexed, inclusive) from source_file."""
    text = source_file.read_text(encoding="utf-8")
    all_lines = text.splitlines()
    return all_lines[start_line - 1 : end_line]


def compute_hash(source_file: Path, start_line: int, end_line: int) -> tuple[str, str, list[str]]:
    """Return (short_hash, full_hash, source_lines) for the given line range."""
    lines = read_lines(source_file, start_line, end_line)
    short, full = hash_lines(lines)
    return short, full, lines
