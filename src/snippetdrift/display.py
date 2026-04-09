from __future__ import annotations

import difflib
from pathlib import Path

from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from snippetdrift.models import CheckReport, SnippetResult

console = Console()


def _status_icon(status: str) -> Text:
    icons = {
        "ok": Text("✓", style="bold green"),
        "drifted": Text("✗", style="bold red"),
        "uninitialized": Text("?", style="bold yellow"),
        "source_missing": Text("!", style="bold magenta"),
    }
    return icons.get(status, Text("?"))


def _status_label(status: str) -> Text:
    labels = {
        "ok": Text("ok", style="green"),
        "drifted": Text("DRIFTED", style="bold red"),
        "uninitialized": Text("uninitialized", style="yellow"),
        "source_missing": Text("source missing", style="magenta"),
    }
    return labels.get(status, Text(status))


def print_check_results(report: CheckReport, repo_root: Path | None = None) -> None:
    file_count = len(report.scanned_files)
    console.print(f"\n  Scanning {file_count} markdown file{'s' if file_count != 1 else ''}...\n")

    for result in report.results:
        ref = result.ref
        icon = _status_icon(result.status)
        md_loc = f"{ref.markdown_file}:{ref.line_number}"
        src_loc = f"{ref.source_file}#L{ref.start_line}-{ref.end_line}"
        reviewed = f"reviewed {ref.reviewed_date}" if ref.reviewed_date else "not reviewed"
        label_str = result.status.upper() if result.status != "ok" else "ok"
        label = _status_label(result.status)

        console.print(
            f"  {icon}  {md_loc:<40} {src_loc:<35} ",
            end="",
        )
        console.print(f"{label_str:<14}", style=label.style, end=" ")
        console.print(reviewed)

    console.print()

    drifted = [r for r in report.results if r.status == "drifted"]
    for result in drifted:
        _print_drift_detail(result, repo_root)

    summary = report.summary
    if not report.has_drift and summary.get("uninitialized", 0) == 0:
        ok = summary.get("ok", 0)
        console.print(f"  All {ok} snippet{'s' if ok != 1 else ''} up to date.\n", style="green")
    elif report.has_drift:
        d = summary.get("drifted", 0)
        console.print(
            f"  {d} snippet{'s' if d != 1 else ''} drifted."
            "  Run `snippetdrift status` for full overview.\n",
            style="red",
        )


def _print_drift_detail(result: SnippetResult, repo_root: Path | None) -> None:
    from snippetdrift.cache import find_repo_root, read_cached_snippet

    ref = result.ref
    console.print(Rule(style="dim"))
    console.print(f"  [bold red]DRIFT DETECTED[/]  {ref.markdown_file}  line {ref.line_number}")
    console.print(Rule(style="dim"))
    console.print(f"\n  Source:       {ref.source_file}  lines {ref.start_line}–{ref.end_line}")
    console.print(
        f"  Stored hash:  [yellow]{ref.stored_hash}[/]"
        + (f"   (reviewed {ref.reviewed_date})" if ref.reviewed_date else "")
    )
    console.print(f"  Current hash: [red]{result.current_hash}[/]\n")
    console.print("  The source region has changed since this snippet was last reviewed.")

    root = repo_root or find_repo_root(ref.markdown_file)
    _entry, cached_lines = read_cached_snippet(root, ref.markdown_file, ref.line_number)
    if cached_lines is not None:
        diff = list(
            difflib.unified_diff(
                cached_lines,
                result.source_lines,
                fromfile=f"{ref.source_file} (accepted)",
                tofile=f"{ref.source_file} (current)",
                lineterm="",
            )
        )
        if diff:
            console.print()
            for line in diff:
                if line.startswith("+") and not line.startswith("+++"):
                    console.print(f"  [green]{line}[/]")
                elif line.startswith("-") and not line.startswith("---"):
                    console.print(f"  [red]{line}[/]")
                else:
                    console.print(f"  {line}")

    console.print(f"\n  Check whether [bold]{ref.markdown_file}[/] needs updating, then run:\n")
    console.print(f"    snippetdrift sync {ref.markdown_file}")
    console.print(f"    snippetdrift accept {ref.markdown_file}\n")
    console.print("  Or in one step if no prose changes are needed:")
    console.print(f"    snippetdrift accept --sync {ref.markdown_file}\n")
    console.print(Rule(style="dim"))
    console.print()


def print_init_results(results: list[SnippetResult]) -> None:
    n = len(results)
    console.print(f"\n  Found {n} uninitialized snippet{'s' if n != 1 else ''}.\n")
    for result in results:
        ref = result.ref
        console.print(
            f"  [blue]✎[/]  {ref.markdown_file}:{ref.line_number:<6}"
            f"  {ref.source_file}#L{ref.start_line}-{ref.end_line:<6}"
            f"  → hash written  ([yellow]{result.current_hash}[/])"
        )
    console.print(
        f"\n  Initialized {len(results)} snippet{'s' if len(results) != 1 else ''}."
        "  Commit the updated markdown files.\n",
        style="green",
    )


def print_accept_results(results: list[SnippetResult]) -> None:
    if not results:
        console.print("\n  No snippets to accept.\n", style="yellow")
        return
    for result in results:
        ref = result.ref
        console.print(
            f"  [green]✓[/]  {ref.markdown_file}:{ref.line_number}"
            f"  → accepted  ([yellow]{result.current_hash}[/])"
        )
    console.print(
        f"\n  Accepted {len(results)} snippet{'s' if len(results) != 1 else ''}.\n",
        style="green",
    )


def print_sync_results(results: list[SnippetResult]) -> None:
    if not results:
        console.print("\n  All code blocks already up to date.\n", style="green")
        return
    for result in results:
        ref = result.ref
        console.print(
            f"  [blue]↻[/]  {ref.markdown_file}:{ref.line_number}"
            f"  {ref.source_file}#L{ref.start_line}-{ref.end_line}"
            f"  → synced"
        )
    console.print(
        f"\n  Synced {len(results)} code block{'s' if len(results) != 1 else ''}."
        "  Commit the updated markdown files.\n",
        style="green",
    )


def print_status_table(report: CheckReport) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", width=4)
    table.add_column("Markdown file")
    table.add_column("Source")
    table.add_column("Last reviewed")

    for result in report.results:
        ref = result.ref
        icon = _status_icon(result.status)
        src = f"{ref.source_file}#L{ref.start_line}-{ref.end_line}"
        reviewed = str(ref.reviewed_date) if ref.reviewed_date else "-"
        table.add_row(icon, f"{ref.markdown_file}:{ref.line_number}", src, reviewed)

    console.print()
    console.print(table)
    console.print()

    summary = report.summary
    parts = [f"{v} {k}" for k, v in summary.items()]
    console.print("  " + "  |  ".join(parts) + "\n")
