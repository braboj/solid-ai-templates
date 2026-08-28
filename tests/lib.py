"""Shared utilities for smoke and e2e test runners."""

import datetime
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv():
    """Load .env from repo root into os.environ (no dependencies)."""
    env_path = os.path.join(ROOT, ".env")
    if not os.path.isfile(env_path):
        return
    with io.open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
ERR  = "ERR "



def read(rel_path):
    """Read a file relative to the repo root."""
    with io.open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def write_report(run_results, started_at, runner_name, columns):
    """Write a timestamped Markdown report to tests/reports/.

    Args:
        run_results: list of dicts with at least 'id', 'status', 'detail'
        started_at: datetime when the run began
        runner_name: 'smoke' or 'e2e'
        columns: dict mapping status to how to render detail (callable or None)
    """
    reports_dir = os.path.join(ROOT, "tests", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    ts = started_at.strftime("%Y-%m-%dT%H-%M-%S")
    report_path = os.path.join(reports_dir, f"{ts}-{runner_name}.md")

    passed  = sum(1 for r in run_results if r["status"] == PASS)
    failed  = sum(1 for r in run_results if r["status"] == FAIL)
    skipped = sum(1 for r in run_results if r["status"] == SKIP)
    errored = sum(1 for r in run_results if r["status"] == ERR)
    total   = len(run_results)

    elapsed = (datetime.datetime.now() - started_at).total_seconds()

    lines = [
        f"# {runner_name.capitalize()} Test Report",
        "",
        f"**Date**: {started_at.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Runner**: run_{runner_name}.py  ",
        f"**Tests run**: {total}  ",
        f"**Elapsed**: {elapsed:.1f}s",
        "",
        "## Summary",
        "",
    ]

    parts = [f"{total} tests — {passed} passed  {failed} failed"]
    if skipped:
        parts.append(f"  {skipped} skipped")
    if errored:
        parts.append(f"  {errored} errors")
    lines.append("".join(parts))
    lines.extend(["", "---", "", "## Results", ""])

    for r in run_results:
        render = columns.get(r["status"])
        if render:
            lines.extend(render(r))
        else:
            lines.append(f"### {r['status']}  {r['id']}")
            lines.append("")

    with io.open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nReport: {os.path.relpath(report_path, ROOT)}")


def parse_args(argv):
    """Parse common CLI args: filter IDs, --fail-fast, --area, --dry-run, --all."""
    flags = set()
    area = None
    filter_ids = []

    for arg in argv:
        if arg == "--fail-fast":
            flags.add("fail-fast")
        elif arg == "--dry-run":
            flags.add("dry-run")
        elif arg == "--all":
            flags.add("all")
        elif arg.startswith("--area="):
            area = arg.split("=", 1)[1].upper()
        elif arg.startswith("--"):
            # ignore unknown flags
            pass
        else:
            filter_ids.append(arg)

    return filter_ids, flags, area
