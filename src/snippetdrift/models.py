from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SnippetRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    markdown_file: Path
    line_number: int
    source_file: Path
    start_line: int
    end_line: int
    stored_hash: str | None
    reviewed_date: date | None


class SnippetResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    ref: SnippetRef
    current_hash: str
    status: Literal["ok", "drifted", "uninitialized", "source_missing"]
    source_lines: list[str]


class CheckReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    scanned_files: list[Path]
    results: list[SnippetResult]

    @property
    def has_drift(self) -> bool:
        return any(r.status == "drifted" for r in self.results)

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts


class CacheEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    markdown_file: str
    sentinel_line: int
    source_file: str
    lines: str
    full_hash: str
    short_hash: str
    reviewed_date: str
    accepted_at: str


class CacheIndex(BaseModel):
    entries: list[CacheEntry] = []
