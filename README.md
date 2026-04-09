# snippetdrift

**snippetdrift** detects when source code referenced from markdown documentation has changed since it was last reviewed. Think of it as [lychee](https://github.com/lycheeverse/lychee), but for code snippets instead of URLs.

---

## What it does

Authors embed a small sentinel comment directly above a fenced code block in their markdown. The comment points to a source file and line range. On first run, `snippetdrift init` computes a SHA-256 hash of those lines and writes it into the comment. On subsequent runs, `snippetdrift check` recomputes the hash and fails if the source region has changed — signalling that the documentation may be stale.

It is designed to work alongside [embedme](https://github.com/zakhenry/embedme), which keeps the snippet *text* current. `snippetdrift` handles the semantic question: *has this region changed since we last reviewed it?*

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

### 1. Add a sentinel comment above your code block

```markdown
<!-- snippetdrift: src/api/models.py#L27-34 -->
```python
class IngestRequest(BaseModel):
    ...
```
```

### 2. Initialize hashes

```bash
snippetdrift init docs/
```

This writes the hash and today's date into the comment in-place:

```markdown
<!-- snippetdrift: src/api/models.py#L27-34 hash:a3f9b2c1 reviewed:2025-04-09 -->
```

Commit the updated markdown files.

### 3. Check for drift

```bash
snippetdrift check docs/
```

Returns exit code `0` when all snippets match, `1` when drift is detected.

### 4. After reviewing and updating docs

```bash
snippetdrift accept docs/api_guide.md
```

Resets the hash and `reviewed:` date for all snippets in that file.

---

## Comment syntax reference

| Field | Description |
|---|---|
| `src/api/models.py#L27-34` | Path relative to repo root, with line range |
| `hash:a3f9b2c1` | First 8 hex chars of SHA-256 of the source lines |
| `reviewed:2025-04-09` | ISO date when the hash was last confirmed correct |

---

## CLI commands

| Command | Description |
|---|---|
| `snippetdrift check [PATH]` | Scan for drift. Exit `0` = ok, `1` = drift, `2` = error |
| `snippetdrift init [PATH]` | Write hashes for uninitialized snippets |
| `snippetdrift accept [PATH]` | Reset hashes after reviewing drifted snippets |
| `snippetdrift status [PATH]` | Show a summary table of all tracked snippets |

All commands accept a path to a markdown file or directory (default: current directory, recursive).

`snippetdrift accept` also accepts `--snippet <source-path>` to accept only snippets from a specific source file.

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

This is a suggestion — `snippetdrift check` on staged files will only check the files being committed, not all docs. You may prefer to always run `snippetdrift check docs/` instead.

---

## Cache

`snippetdrift` writes a `.snippetdrift_cache/` directory at the repo root. It contains:

- `index.json` — maps each sentinel to its full hash and metadata
- `snippets/<hash>.txt` — the accepted source lines at the time of last accept

The markdown file itself is the source of truth for the short hash. The cache stores the full hash and the last-accepted snippet text, used to display rich unified diffs when drift is detected.

**To commit or not to commit:** Adding `.snippetdrift_cache/` to version control lets teammates see the accepted snippet text and diffs in CI. Excluding it means each developer rebuilds it locally on `accept`. Either workflow is valid.

Add to `.gitignore` if you prefer not to commit it:

```
.snippetdrift_cache/
```

---

## Works great with embedme

[embedme](https://github.com/zakhenry/embedme) reads a path comment in your code block and rewrites the block content with the actual file contents. `snippetdrift` is complementary:

- **embedme** keeps the *text* of the snippet current
- **snippetdrift** detects when the *semantics* of the referenced region have changed since the docs were last reviewed

Run them together in CI for complete documentation freshness coverage:

```bash
embedme --check docs/
snippetdrift check docs/
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
