# snippetdrift examples

This directory demonstrates `snippetdrift` in action.

## Structure

- `src/api/models.py` — the "current" source file with two Pydantic models
- `src/api/models_drifted.py` — a modified version used in tests to simulate drift
- `docs/api_guide.md` — markdown with two snippet sentinels (one stable, one drifted)

## Try it yourself

```bash
# Initialize hashes into the markdown
snippetdrift init examples/docs/

# Check — all ok
snippetdrift check examples/docs/

# Simulate drift: replace the source with the drifted version
cp examples/src/api/models_drifted.py examples/src/api/models.py

# Check again — drift detected on the second snippet
snippetdrift check examples/docs/

# Accept the drift after reviewing
snippetdrift accept examples/docs/api_guide.md
```
