from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def examples_src(repo_root: Path) -> Path:
    return repo_root / "examples" / "src" / "api"


@pytest.fixture
def examples_docs(repo_root: Path) -> Path:
    return repo_root / "examples" / "docs"
