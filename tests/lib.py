"""Shared utilities for smoke and e2e test runners."""

import datetime
import io
import os
import subprocess

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



# Directories git may list in full -- an unignored virtual environment, a
# dependency tree, a nested worktree -- that no check has ever read as
# repository content. Applied to git's answer so a corpus does not depend
# on whether a given toolchain happens to write its own .gitignore.
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".idea",
             ".claude"}

# templates/INTERVIEW.md is written by tools/sync.py from the manifest. It
# is a document the templates directory holds, not a template: it declares
# no [ID:] section and takes no manifest entry. Naming it here keeps the
# exception in one place, so a second generated document dropped beside it
# is a finding rather than a silent member of the corpus.
GENERATED_TEMPLATE_DOCS = frozenset(["templates/INTERVIEW.md"])


def repository_files():
    """Every repo-relative path git tracks or would track, ignored ones out.

    A filesystem walk cannot read .gitignore, so it descends into build
    output, virtual environments and nested worktrees, and reports their
    copies of a file as repository content. Git decides what belongs to the
    repository, so ask git: --cached covers tracked files and --others
    --exclude-standard the untracked ones a commit could still add, leaving
    out everything .gitignore excludes.
    """
    out = subprocess.check_output(
        ["git", "-C", ROOT, "ls-files", "-z", "--cached", "--others",
         "--exclude-standard"],
        stderr=subprocess.STDOUT,
    )
    paths = [p for p in out.decode("utf-8").split("\0") if p]
    return [
        p for p in paths
        if not any(part in SKIP_DIRS for part in p.split("/"))
    ]


def template_documents(prefix="templates/"):
    """Every Markdown file the repository holds under templates/.

    A hardcoded directory list defines what the checks reading it can see,
    so a template outside the list is invisible to all of them and the
    corpus count cannot move to say so. Asking git makes the count evidence:
    it differs when the tree differs.
    """
    return sorted(
        p for p in repository_files()
        if p.startswith(prefix) and p.endswith(".md")
    )


def template_files(prefix="templates/"):
    """The template corpus the manifest governs, repo-relative.

    Every Markdown file under templates/ except the documents sync.py
    generates there, which carry no manifest entry and declare no sections.
    """
    return [p for p in template_documents(prefix)
            if p not in GENERATED_TEMPLATE_DOCS]


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

    # A runner may carry a status of its own -- a check whose verdict is a
    # judgement rather than a pass. Count it by name rather than dropping
    # it, so the summary's parts add up to the total it states.
    named = {PASS, FAIL, SKIP, ERR}
    other = {}
    for r in run_results:
        if r["status"] not in named:
            other[r["status"]] = other.get(r["status"], 0) + 1

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
    for status in sorted(other):
        parts.append(f"  {other[status]} {status.strip().lower()}")
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


def print_verdict(ok, detail):
    """Print the run outcome as the very last line the runner emits.

    Args:
        ok: True when the run is clean, False otherwise
        detail: the counts to state beside the verdict, already formatted
    """

    # Every other summary line -- the counts, the advisory, the report
    # path -- can be the last one a truncated read keeps, and each of
    # them reads as a complete summary with no failure in it. The
    # verdict goes after all of them, so a reader who keeps one line
    # keeps this one.
    print("VERDICT: %s - %s" % ("PASS" if ok else "FAIL", detail))


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
