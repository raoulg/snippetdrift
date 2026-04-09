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


@app.command("init")
def init(
    path: Path | None = _DEFAULT_PATH,
    no_sync: bool = typer.Option(
        False, "--no-sync", help="Skip syncing source lines into code blocks"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Initialize uninitialized snippets: sync content + write hashes.

    By default also syncs source lines into the code blocks. Use --no-sync to
    write hashes only without touching code block content.
    """
    from snippetdrift.checker import run_init
    from snippetdrift.display import print_init_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    results = run_init(target, sync=not no_sync)
    print_init_results(results)


@app.command("sync")
def sync(
    path: Path | None = _DEFAULT_PATH,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Copy current source lines into code blocks. Does not change hashes.

    Use this to update code block content after a drift without yet accepting.
    After syncing, review any surrounding prose, then run `snippetdrift accept`.
    """
    from snippetdrift.checker import run_sync
    from snippetdrift.display import print_sync_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    results = run_sync(target)
    print_sync_results(results)


@app.command("accept")
def accept(
    path: Path | None = _DEFAULT_PATH,
    snippet: str | None = typer.Option(
        None, "--snippet", help="Only accept snippets from this source file path"
    ),
    do_sync: bool = typer.Option(
        False, "--sync", help="Also sync source lines into code blocks before accepting"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Accept drifted snippets and reset their hashes.

    Marks all snippets as reviewed at today's date. Pass --sync to also update
    the code block content from source in the same step.
    """
    from snippetdrift.checker import run_accept
    from snippetdrift.display import print_accept_results

    _setup_logging(verbose)
    target = path or Path.cwd()

    results = run_accept(target, snippet_filter=snippet, sync=do_sync)
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
