from __future__ import annotations

import sys
from pathlib import Path

import typer
from loguru import logger

app = typer.Typer(
    name="snippetdrift",
    help="Detect when source code referenced from markdown has drifted from a stored hash.",
    add_completion=False,
)

_DEFAULT_PATH = typer.Argument(None, help="Path to markdown file or directory (default: cwd)")


def _setup_logging(verbose: bool) -> None:
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="WARNING")


@app.command("check")
def check(
    path: Path | None = _DEFAULT_PATH,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Scan markdown files for snippet drift."""
    from snippetdrift.checker import run_check
    from snippetdrift.display import print_check_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    report = run_check(target)
    print_check_results(report)

    if report.has_drift:
        raise typer.Exit(code=1)

    uninitialized = report.summary.get("uninitialized", 0)
    if uninitialized > 0:
        raise typer.Exit(code=0)


@app.command("init")
def init(
    path: Path | None = _DEFAULT_PATH,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Initialize uninitialized snippet hashes in-place."""
    from snippetdrift.checker import run_init
    from snippetdrift.display import print_init_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    results = run_init(target)
    print_init_results(results)


@app.command("accept")
def accept(
    path: Path | None = _DEFAULT_PATH,
    snippet: str | None = typer.Option(
        None, "--snippet", help="Only accept snippets from this source file path"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Accept drifted snippets and reset their hashes."""
    from snippetdrift.checker import run_accept
    from snippetdrift.display import print_accept_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    results = run_accept(target, snippet_filter=snippet)
    print_accept_results(results)


@app.command("status")
def status(
    path: Path | None = _DEFAULT_PATH,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Show a summary table of all tracked snippets and their status."""
    from snippetdrift.checker import run_check
    from snippetdrift.display import print_status_table

    _setup_logging(verbose)
    target = path or Path.cwd()

    report = run_check(target)
    print_status_table(report)
