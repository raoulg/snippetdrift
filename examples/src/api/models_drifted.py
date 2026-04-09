"""API models for the document ingestion service (drifted version for testing)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Internal helpers (not part of public API)
# ---------------------------------------------------------------------------


def _validate_language(lang: str) -> str:
    supported = {"nl", "en"}
    if lang not in supported:
        raise ValueError(f"Unsupported language: {lang!r}. Must be one of {supported}")
    return lang


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Payload for submitting a document to the ingestion pipeline."""

    document_id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Raw text content to ingest")
    language: Literal["nl", "en"] = Field("nl", description="Language of the document")
    source_url: str | None = Field(None, description="Optional origin URL of the document")


# New field added — this shifts IngestResponse down and changes its content
class IngestMetadata(BaseModel):
    """Metadata attached to an ingested document."""

    ingested_at: str
    pipeline_version: str


class IngestResponse(BaseModel):
    """Response returned after submitting a document."""

    document_id: str = Field(..., description="The document ID echoed back")
    status: Literal["queued", "processed", "failed"] = Field(
        ..., description="Processing status"
    )
    message: str | None = Field(None, description="Optional human-readable status message")
    metadata: IngestMetadata | None = Field(None, description="Optional ingestion metadata")
