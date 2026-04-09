# snippetdrift examples

This directory demonstrates `snippetdrift` in action.

## Structure

- `src/api/models.py` — the "current" source file with two Pydantic models
- `src/api/models_drifted.py` — a modified version used in tests to simulate drift
- `docs/api_guide.md` — markdown with two snippet sentinels (empty code blocks to start)

## Try it yourself

From the repo root:

```bash
# Step 1: sync source lines into the empty code blocks + write hashes
snippetdrift init examples/docs/

# Step 2: check — all ok
snippetdrift check examples/docs/

# Step 3: simulate drift by replacing the source with a modified version
cp examples/src/api/models_drifted.py examples/src/api/models.py

# Step 4: check again — drift is detected on the second snippet
snippetdrift check examples/docs/

# Step 5: sync the updated source into the code block, then accept
snippetdrift sync examples/docs/
snippetdrift accept examples/docs/api_guide.md

# Or collapse steps 5 into one:
snippetdrift accept --sync examples/docs/api_guide.md
```
