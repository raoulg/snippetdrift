# Ingestion API Guide

This guide covers the request and response models used by the document ingestion pipeline.
All models are defined using [Pydantic v2](https://docs.pydantic.dev/) and are fully typed.

---

## Submitting a document

To submit a document for ingestion, POST to `/v1/ingest` with an `IngestRequest` body.

<!-- snippetdrift: examples/src/api/models.py#L27-34 -->
```python
```

The `language` field defaults to `"nl"` (Dutch). Set it to `"en"` for English documents.
The `source_url` is optional and can be used to record where the document originated.

---

## Handling the response

After submission the API returns an `IngestResponse`:

<!-- snippetdrift: examples/src/api/models.py#L36-43 -->
```python
```

Poll `GET /v1/ingest/{document_id}` until `status` is `"processed"` or `"failed"`.
A non-null `message` field will contain additional detail when `status` is `"failed"`.
