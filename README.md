# snippetdrift

[![PyPI](https://img.shields.io/pypi/v/snippetdrift?color=blue)](https://pypi.org/project/snippetdrift/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![ty](https://img.shields.io/badge/type--checked-ty-blue)](https://github.com/astral-sh/ty) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

**snippetdrift** keeps code snippets in your markdown documentation honest. It syncs source code directly into your docs and detects when those regions change — so you always know when documentation may have gone stale.

---

## What it does

Add a sentinel comment above any fenced code block pointing to a source file and line range. `snippetdrift` will:

1. **Sync** — copy those exact lines from the source file into the code block
2. **Hash** — record a SHA-256 fingerprint of the region
3. **Check** — on every subsequent run, recompute the hash and fail if the source has changed

The result: your docs always show real, current code, and CI tells you the moment a referenced region drifts.

---

## Installation

```bash
# Recommended
uv tool install snippetdrift

# Or with pip
pip install snippetdrift
```

---

## Quickstart

### 1. Add a sentinel comment above an empty code block

```markdown
<!-- snippetdrift: src/api/models.py#L27-34 -->
```python
```
```

The path is relative to the repo root. The code block can be empty — `init` will fill it in.

### 2. Initialize: sync content + write hashes

```bash
snippetdrift init docs/
```

This copies the referenced source lines into the code block and writes the hash and today's date into the sentinel comment, in-place:

```markdown
<!-- snippetdrift: src/api/models.py#L27-34 hash:a3f9b2c1 reviewed:2025-04-09 -->
```python
class IngestRequest(BaseModel):
    document_id: str
    content: str
    ...
```
```

Commit the updated markdown files.

### 3. Check for drift in CI

```bash
snippetdrift check docs/
```

Exit code `0` = all snippets match. Exit code `1` = drift detected.

### 4. When drift is detected

Review the diff that `snippetdrift check` prints, update any surrounding prose, then sync the new content and accept:

```bash
snippetdrift sync docs/          # pull current source lines into code blocks
snippetdrift accept docs/        # reset hashes, mark as reviewed today
```

Or, if you're happy to accept the source as-is without manual editing:

```bash
snippetdrift accept --sync docs/
```

---

## Comment syntax reference

| Field | Description |
|---|---|
| `src/api/models.py#L27-34` | Path relative to repo root, with line range |
| `hash:a3f9b2c1` | First 8 hex chars of SHA-256 of the source lines (written by `init`/`accept`) |
| `reviewed:2025-04-09T14:32:00` | Datetime when the hash was last confirmed correct (written by `init`/`accept`) |

---

## CLI commands

| Command | Description |
|---|---|
| `snippetdrift init [PATH]` | Sync source into code blocks + write hashes for uninitialized snippets. Use `--no-sync` to skip content sync. |
| `snippetdrift sync [PATH]` | Copy current source lines into code blocks. Does not change hashes. |
| `snippetdrift check [PATH]` | Detect drift. Exit `0` = ok, `1` = drift. |
| `snippetdrift accept [PATH]` | Reset hashes after reviewing drift. Add `--sync` to also update code block content. |
| `snippetdrift status [PATH]` | Show a summary table of all tracked snippets and their status. |

All commands accept a path to a markdown file or directory (default: current directory, recursive).

`snippetdrift accept` also accepts `--snippet <source-path>` to scope acceptance to a single source file.

### What each command touches

| | Code block content | `hash:` in sentinel | `reviewed:` in sentinel | Cache |
|---|:---:|:---:|:---:|:---:|
| `init` | ✅ (default, skip with `--no-sync`) | ✅ written | ✅ set to now | ✅ written |
| `sync` | ✅ updated | ❌ | ❌ | ❌ |
| `check` | ❌ read-only | ❌ read-only | ❌ read-only | ❌ |
| `accept` | ❌ (opt-in with `--sync`) | ✅ recomputed | ✅ set to now | ✅ updated |
| `status` | ❌ read-only | ❌ read-only | ❌ read-only | ❌ |

The `reviewed:` timestamp is the human sign-off marker — only `init` and `accept` update it, because those are the points where someone confirms the documentation is correct.

---

## Typical workflows

**First time setup:**
```bash
snippetdrift init docs/          # sync source into code blocks + write hashes
git add docs/
git commit -m "docs: initialize snippet hashes"
```

**Day to day — source code changes:**
```bash
# change source code
snippetdrift check docs/         # drift detected → exit 1
snippetdrift sync docs/          # pull new source lines into code blocks
# review the diff, edit surrounding prose if needed
snippetdrift accept docs/        # reset hashes, mark as reviewed
git add docs/
git commit -m "docs: accept drift in api_guide"
```

---

## CI integration

```yaml
name: Snippet Drift Check

on:
  push:
    branches: [main]
  pull_request:

jobs:
  snippetdrift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv tool install snippetdrift
      - run: snippetdrift check docs/
```

---

## Pre-commit with lefthook

A suggested `lefthook.yml` is included in this repo:

```yaml
pre-commit:
  commands:
    snippetdrift:
      run: snippetdrift check {staged_files}
      glob: "*.md"
```

This is a suggestion — `snippetdrift check` on staged files only checks committed files. You may prefer to always run `snippetdrift check docs/` unconditionally.

---

## Cache

`snippetdrift` writes a `.snippetdrift_cache/` directory at the repo root containing:

- `index.json` — maps each sentinel to its full hash and metadata
- `snippets/<hash>.txt` — the accepted source lines at the time of last accept, used to render diffs

The markdown file itself is the source of truth for the short hash. The cache is supplementary.

**To commit or not:** Committing the cache lets CI show rich diffs even on the first run after a drift. Excluding it means the cache is rebuilt locally on the next `accept`. Either works — add to `.gitignore` if you prefer not to commit it:

```
.snippetdrift_cache/
```

---

## Contributing

```bash
uv sync --dev
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run ty check src/
uv run pytest
```
