# Claude Code Instructions: `snippetdrift`

Build a Python CLI package called **`snippetdrift`** that detects when source code referenced from markdown documentation has drifted from a stored hash. Think of it as lychee, but for code snippets instead of URLs.

---

## Concept

Authors embed special comments in markdown that point to a source file + line range. On first run, `snippetdrift` computes and writes the hash into the markdown. On subsequent runs, it recomputes the hash and fails if the source region has changed — signalling that the documentation may be stale.

It is designed to work alongside **embedme**, which handles keeping the snippet text itself current. `snippetdrift` handles the semantic question: *has this region changed since we last reviewed it?*

---

## Comment syntax in markdown

Each tracked snippet needs a sentinel comment directly above the fenced code block:

```markdown
<!-- snippetdrift: src/api/models.py#L45-60 hash:a3f9b2c1 reviewed:2025-04-09 -->
```python
class IngestRequest(BaseModel):
    ...
```
```

Fields:
- `src/api/models.py#L45-60` — path relative to repo root, with line range
- `hash:` — SHA-256 (first 8 chars) of the referenced source lines, written by `snippetdrift init`
- `reviewed:` — ISO date when the hash was last confirmed correct, written by `snippetdrift init` or `snippetdrift accept`

On **first run** (no hash present), the comment looks like:
```markdown
<!-- snippetdrift: src/api/models.py#L45-60 -->
```

`snippetdrift init` fills in `hash:` and `reviewed:` in-place.

---

## Project layout

```
snippetdrift/
├── pyproject.toml
├── README.md
├── lefthook.yml                         # suggested pre-commit config
├── .github/
│   └── workflows/
│       └── snippetdrift.yml             # GitHub Actions workflow
├── src/
│   └── snippetdrift/
│       ├── __init__.py
│       ├── cli.py                       # Typer CLI entrypoint
│       ├── parser.py                    # markdown sentinel comment parser
│       ├── hasher.py                    # hashing logic
│       ├── checker.py                   # drift detection logic
│       ├── writer.py                    # in-place markdown updater
│       ├── cache.py                     # .snippetdrift_cache management
│       ├── models.py                    # Pydantic models
│       └── display.py                   # rich terminal output formatting
├── examples/
│   ├── README.md                        # demo instructions
│   ├── docs/
│   │   └── api_guide.md                 # markdown with two snippets (one ok, one drifted)
│   └── src/
│       └── api/
│           ├── models.py                # source file — one region stable, one moved
│           └── models_drifted.py        # simulated drifted version
└── tests/
    ├── conftest.py
    ├── test_parser.py
    ├── test_hasher.py
    ├── test_checker.py
    └── test_examples.py                 # integration test that runs against examples/
```

---

## `pyproject.toml` requirements

- Use **uv** conventions: `[build-system]` with `hatchling`
- Package name: `snippetdrift`
- Entry point: `snippetdrift` → `snippetdrift.cli:app`
- Python `>=3.11`
- run code with `uv run python` to avoid issues with the environment not being activated

**Runtime dependencies:**
- `typer` (with extras `[all]` for rich support)
- `pydantic>=2`
- `loguru`
- `rich` (for colored output)

**Dev dependencies (`[dependency-groups]` in uv style):**
- `ruff`
- `ty`
- `pytest`
- `pytest-cov`

---

## CLI commands

### `snippetdrift check [PATH]`

The main command. Scans markdown files (default: current directory, recursive) for sentinel comments, recomputes hashes, and reports drift.

```
snippetdrift check docs/
snippetdrift check docs/api_guide.md
snippetdrift check          # scans cwd recursively
```

Exit codes:
- `0` — all snippets match
- `1` — one or more snippets have drifted
- `2` — configuration or parse error

### `snippetdrift init [PATH]`

First-run command. Finds sentinel comments that have no `hash:` yet, computes and writes them in-place. Also writes `reviewed:` timestamp.

```
snippetdrift init docs/
```

Does **not** overwrite existing hashes. Safe to re-run.

### `snippetdrift accept [PATH]`

After a developer has reviewed a drift and updated the docs, they run this to reset the hash and update `reviewed:`.

```
snippetdrift accept docs/api_guide.md
```

Accepts **all** drifted snippets in the file, or can be scoped with `--snippet` flag by source path.

### `snippetdrift status [PATH]`

Summary table view: shows all tracked snippets, their status (✓ ok / ✗ drifted / ? uninitialized), last reviewed date, source location. Good for a quick overview.

---

## Pydantic models (`models.py`)

```python
class SnippetRef(BaseModel):
    """A parsed sentinel comment from a markdown file."""
    markdown_file: Path
    line_number: int              # line of the sentinel comment in the markdown
    source_file: Path             # path to the source file
    start_line: int
    end_line: int
    stored_hash: str | None       # None if not yet initialized
    reviewed_date: date | None

class SnippetResult(BaseModel):
    """Result of checking a single snippet."""
    ref: SnippetRef
    current_hash: str
    status: Literal["ok", "drifted", "uninitialized", "source_missing"]
    source_lines: list[str]

class CheckReport(BaseModel):
    """Full report for a check run."""
    scanned_files: list[Path]
    results: list[SnippetResult]

    @property
    def has_drift(self) -> bool: ...

    @property
    def summary(self) -> dict[str, int]: ...  # counts per status
```

---

## Hashing (`hasher.py`)

- Read the specified line range from the source file
- Strip trailing whitespace from each line before hashing (avoids noise from editor formatting)
- Hash with `hashlib.sha256`
- Return first **8 hex characters** (stored in the comment)
- Also store the full hash in the cache

---

## Cache (`.snippetdrift_cache/`)

Location: `.snippetdrift_cache/` in the repo root (walk up from cwd to find it, like git does).

Structure:
```
.snippetdrift_cache/
├── index.json          # maps (markdown_file, line_number) → full hash + metadata
└── snippets/
    └── <hash>.txt      # the source lines at the time the hash was accepted
```

`index.json` schema (use Pydantic for serialization):
```json
{
  "entries": [
    {
      "markdown_file": "docs/api_guide.md",
      "sentinel_line": 14,
      "source_file": "src/api/models.py",
      "lines": "45-60",
      "full_hash": "a3f9b2c1d4e5f6a7...",
      "short_hash": "a3f9b2c1",
      "reviewed_date": "2025-04-09",
      "accepted_at": "2025-04-09T14:32:00Z"
    }
  ]
}
```

The cache is **supplementary** — the markdown file itself is the source of truth for the short hash. The cache stores the full hash and the accepted snippet text for richer diffing.

Add `.snippetdrift_cache/` to the project's `.gitignore` suggestion in the README, but note that teams may choose to commit it.

---

## Terminal output (`display.py`)

Use `rich` for all terminal output. This is a linting tool and output clarity is a first-class concern.

### On `check` — clean run:
```
  snippetdrift check docs/

  Scanning 3 markdown files...

  ✓  docs/api_guide.md:14    src/api/models.py#L45-60     ok          reviewed 2025-04-09
  ✓  docs/api_guide.md:38    src/api/client.py#L10-25     ok          reviewed 2025-04-01

  All 2 snippets up to date.
```

### On `check` — drift detected:
```
  snippetdrift check docs/

  Scanning 3 markdown files...

  ✓  docs/api_guide.md:14    src/api/models.py#L45-60     ok          reviewed 2025-04-09
  ✗  docs/api_guide.md:38    src/api/client.py#L10-25     DRIFTED     reviewed 2025-04-01

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DRIFT DETECTED  docs/api_guide.md  line 38
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Source:       src/api/client.py  lines 10–25
  Stored hash:  b1c2d3e4   (reviewed 2025-04-01)
  Current hash: f9a8b7c6

  The source region has changed since this snippet was last reviewed.
  Check whether docs/api_guide.md needs updating, then run:

    snippetdrift accept docs/api_guide.md

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1 snippet drifted. Run `snippetdrift status` for full overview.
```

If the cache has the old snippet stored, show a **unified diff** between the cached version and the current source lines, using rich markup for red/green coloring.

### On `init`:
```
  snippetdrift init docs/

  Found 2 uninitialized snippets.

  ✎  docs/api_guide.md:14    src/api/models.py#L45-60     → hash written  (a3f9b2c1)
  ✎  docs/api_guide.md:38    src/api/client.py#L10-25     → hash written  (b1c2d3e4)

  Initialized 2 snippets. Commit the updated markdown files.
```

Use **loguru** for internal logging (debug-level tracing of file parsing, hash computation etc). Use `rich` for user-facing output. Keep them separate — loguru goes to stderr at DEBUG level, only visible with `--verbose` flag.

---

## Example setup (`examples/`)

### `examples/src/api/models.py`

A real-looking Python file with two classes. The line numbers should be realistic (not just line 1).

```python
# examples/src/api/models.py

from pydantic import BaseModel
from typing import Literal

# ... some code above to push classes down ...

class IngestRequest(BaseModel):
    document_id: str
    content: str
    language: Literal["nl", "en"] = "nl"
    source_url: str | None = None


class IngestResponse(BaseModel):
    document_id: str
    status: Literal["queued", "processed", "failed"]
    message: str | None = None
```

### `examples/docs/api_guide.md`

Two snippets:
1. One pointing to `IngestRequest` — will be **stable** (hash matches)
2. One pointing to `IngestResponse` — will be **drifted** (line numbers have shifted because we'll swap in a modified source file in the test)

The markdown should look like real docs — intro text, explanation, snippet, outro. Not just a bare code block.

### Simulating drift in tests

In `test_examples.py`:
1. Copy the example source files to a tmp directory
2. Run `snippetdrift init` against the copied markdown
3. Modify one source region (move the class down by inserting lines)
4. Run `snippetdrift check`
5. Assert exit code 1 and that the drifted snippet is correctly identified

Use `pytest` fixtures and `tmp_path` for isolation. Do **not** mutate the actual `examples/` directory in tests.

---

## `lefthook.yml` (suggested, not enforced)

```yaml
pre-commit:
  commands:
    snippetdrift:
      run: snippetdrift check {staged_files}
      glob: "*.md"
```

Include this file in the repo root and document it in the README.

---

## GitHub Actions workflow (`.github/workflows/snippetdrift.yml`)

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

## README sections to include

1. **What it does** — one paragraph
2. **Installation** — `uv tool install snippetdrift` and `pip install snippetdrift`
3. **Quickstart** — sentinel comment syntax, `init`, `check`, `accept` workflow
4. **Comment syntax reference** — table of fields
5. **CI integration** — paste the GitHub Actions workflow
6. **Pre-commit with lefthook** — paste the lefthook config, note this is a suggestion
7. **Cache** — explain `.snippetdrift_cache/`, whether to commit it
8. **Works great with embedme** — one paragraph explaining the complementary workflow
9. **Contributing** — `uv sync --dev`, `ruff check`, `ty check`, `pytest`

---

## Code quality

- Run `ruff check` and `ruff format` — zero warnings
- Run `ty check` — zero errors
- `ruff` config in `pyproject.toml`: target Python 3.11, enable `E`, `F`, `I`, `UP` rule sets
- All functions and methods must have type annotations
- Pydantic models must use `model_config = ConfigDict(frozen=True)` where appropriate
- No `Any` unless genuinely unavoidable

---

## What to build, in order

1. `pyproject.toml` + project scaffolding with uv
2. `models.py`
3. `hasher.py`
4. `parser.py`
5. `cache.py`
6. `checker.py`
7. `writer.py`
8. `display.py`
9. `cli.py`
10. `examples/` directory
11. `tests/`
12. `README.md`
13. `lefthook.yml`
14. `.github/workflows/snippetdrift.yml`

Run `uv run pytest` at the end and confirm tests pass before declaring done.
