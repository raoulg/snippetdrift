# Ingestion API Guide

This guide covers the request and response models used by the document ingestion pipeline.
All models are defined using [Pydantic v2](https://docs.pydantic.dev/) and are fully typed.

---

## Submitting a document

To submit a document for ingestion, POST to `/v1/ingest` with an `IngestRequest` body.

<!-- snippetdrift: examples/src/api/models.py#L27-34 hash:daaed440 reviewed:2026-04-09 -->
```python
class IngestRequest(BaseModel):
    """Payload for submitting a document to the ingestion pipeline."""

    document_id: str = Field(..., description="Unique identifier for the document")
    content: str = Field(..., description="Raw text content to ingest")
    language: Literal["nl", "en"] = Field("nl", description="Language of the document")
    source_url: str | None = Field(None, description="Optional origin URL of the document")
```

The `language` field defaults to `"nl"` (Dutch). Set it to `"en"` for English documents.
The `source_url` is optional and can be used to record where the document originated.

---

## Handling the response

After submission the API returns an `IngestResponse`:

<!-- snippetdrift: examples/src/api/models.py#L36-43 hash:04134a06 reviewed:2026-04-09 -->
```python
class IngestResponse(BaseModel):
    """Response returned after submitting a document."""

    document_id: str = Field(..., description="The document ID echoed back")
    status: Literal["queued", "processed", "failed"] = Field(
        ..., description="Processing status"
    )
    message: str | None = Field(None, description="Optional human-readable status message")
```

Poll `GET /v1/ingest/{document_id}` until `status` is `"processed"` or `"failed"`.
A non-null `message` field will contain additional detail when `status` is `"failed"`.
