#!/usr/bin/env python3
"""
E2E test runner for solid-ai-templates.

Sends prepared interview answers and stack templates to an LLM,
then asserts required strings are present (and forbidden strings absent).

Provider is selected via E2E_PROVIDER env var (default: gemini).
See tests/providers.py for available backends.

Usage:
  py tests/run_e2e.py                    # run canary test only (python-lib)
  py tests/run_e2e.py --all              # run all non-skipped tests
  py tests/run_e2e.py STK-01             # run one test by short ID
  py tests/run_e2e.py STK-01 FMT-01      # run multiple
  py tests/run_e2e.py --area=STK          # run all stack tests
  py tests/run_e2e.py --dry-run          # print prompt, skip LLM call
  py tests/run_e2e.py --fail-fast        # stop on first failure

Default (no args) runs only the canary test (STK-15, python-lib) to keep
live runs fast and token-efficient. Use --all, --area, or explicit IDs
to run more tests.

Structural validation (file existence, field presence, prompt assembly)
is handled by smoke tests — run `py tests/run_smoke.py` instead.
"""

import datetime
import os
import sys
import time

from lib import ROOT, PASS, FAIL, SKIP, ERR, read, parse_args, load_dotenv
from cases import ALL_TESTS, CANARY_TESTS

# Import shared resolver from tools/
sys.path.insert(0, os.path.join(ROOT, "tools"))
from resolve import load_manifest, resolve_chain, read_file  # noqa: E402

# Set the output encoding at the boundary rather than inheriting the
# console default, which mangles any non-ASCII this program prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


load_dotenv()

_manifest_cache = None


def _get_manifest():
    global _manifest_cache
    if _manifest_cache is None:
        core_ids, entries, stacks = load_manifest()
        file_to_id = {e["file"]: e["id"] for e in entries.values()}
        _manifest_cache = (core_ids, entries, file_to_id)
    return _manifest_cache


def resolve_deps(stack_file):
    """Resolve full dependency chain for a stack file path."""
    core_ids, entries, file_to_id = _get_manifest()
    stack_id = file_to_id.get(stack_file)
    if stack_id:
        return resolve_chain(stack_id, core_ids, entries)
    return []


def build_prompt(stack_file, answers, output_file="templates/base/core/agents.md",
                 extra_files=()):
    chain = resolve_deps(stack_file)

    # Step 3: resolve extras via manifest if possible
    _, entries, file_to_id = _get_manifest()
    resolved_ids = {file_to_id.get(f) for f in chain}
    extra_resolved = []
    for ef in extra_files:
        eid = file_to_id.get(ef)
        if eid and eid not in resolved_ids:
            extra_resolved.append(ef)
        elif not eid:
            extra_resolved.append(ef)

    output_fmt = read(output_file)
    answers_text = "\n".join(f"- {k}: {v}" for k, v in answers.items())

    templates_section = ""
    for f in chain:
        templates_section += f"--- {f} ---\n{read(f)}\n\n"

    extra_section = "".join(
        f"--- {f} ---\n{read(f)}\n\n" for f in extra_resolved
    )

    return (
        "You are generating a context file for a software project.\n\n"
        "The interview is complete. The final answers are provided below.\n"
        "Use the templates and output format to compose the file.\n\n"
        "Rules:\n"
        "- Follow the output format structure exactly.\n"
        "- Reproduce conventions from the templates VERBATIM — do not "
        "paraphrase, substitute synonyms, or use your own defaults. "
        "If a template says `feat/`, write `feat/` not `feature/`. "
        "If a template says `feat:`, write `feat:` not `feat,`.\n"
        "- Replace ALL placeholders (e.g. [project], [owner], [platform]) "
        "with concrete values from the interview answers.\n"
        "- Output ONLY the file content — no preamble, no explanation, "
        "no markdown fences around the whole document.\n\n"
        f"--- Templates (full dependency chain) ---\n\n{templates_section}"
        f"{extra_section}"
        f"--- Output format ({output_file}) ---\n{output_fmt}\n\n"
        f"--- Interview answers ---\n{answers_text}\n\n"
        "Generate the output file now.\n\n"
        "IMPORTANT REMINDER: Do NOT summarize. Include the exact language "
        "version (e.g. 'Python 3.11+'), exact branch prefixes (e.g. "
        "'feat/'), and exact commit prefixes (e.g. 'feat:') from the "
        "stack template. Every convention must appear verbatim in your output."
    )


def _get_provider():
    from providers import get_provider
    return get_provider()


def check_assertions(output, required=(), forbidden=()):
    failures = []
    lower = output.lower()
    for s in required:
        if s.lower() not in lower:
            failures.append(f"  MISSING   : {s!r}")
    for s in forbidden:
        if s.lower() in lower:
            failures.append(f"  UNEXPECTED: {s!r}")
    return failures


def run_test(test, dry_run=False):
    tid = test["id"]

    if "skip" in test:
        return SKIP, test["skip"], None, None, None

    prompt = build_prompt(
        test["stack"], test["answers"],
        test.get("output_file", "templates/base/core/agents.md"),
        test.get("extra_files", ()),
    )

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[{tid}] DRY RUN — prompt length: {len(prompt)} chars")
        print(prompt[:400], "...")
        return SKIP, "dry-run", None, None, None

    provider_name, provider_fn = _get_provider()

    t0 = time.time()
    try:
        output = provider_fn(prompt)
    except Exception as e:
        return ERR, f"{provider_name} error: {e}", None, None, None
    elapsed = time.time() - t0

    failures = check_assertions(
        output,
        required=test.get("required", []),
        forbidden=test.get("forbidden", []),
    )

    if failures:
        return FAIL, "\n".join(failures), elapsed, output, prompt
    return PASS, f"{elapsed:.1f}s", elapsed, output, prompt


def _render_prompt(r, lines):
    if r.get("prompt"):
        lines.append("<details><summary>Prompt</summary>")
        lines.append("")
        lines.append("```")
        lines.append(r["prompt"].replace("```", "~~~"))
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")


def render_fail(r):
    lines = []
    elapsed_str = f"  ({r['elapsed']:.1f}s)" if r["elapsed"] else ""
    lines.append(f"### {r['status']}  {r['id']}{elapsed_str}")
    lines.append("")
    lines.append("**Expected**:")
    lines.append("")
    lines.append("```")
    for line in r["detail"].splitlines():
        lines.append(line)
    lines.append("```")
    lines.append("")
    lines.append("**Output**:")
    lines.append("")
    lines.append("```")
    lines.append((r["output"] or "").replace("```", "~~~"))
    lines.append("```")
    lines.append("")
    _render_prompt(r, lines)
    return lines


def render_err(r):
    return [f"### {r['status']}  {r['id']}", "", f"**Error**: {r['detail']}", ""]


def render_skip(r):
    return [f"### {r['status']}  {r['id']}", "", f"**Skipped**: {r['detail']}", ""]


def render_pass(r):
    elapsed_str = f"  ({r['detail']})" if r["detail"] else ""
    lines = [f"### {r['status']}  {r['id']}{elapsed_str}", ""]
    if r.get("output"):
        lines.append("**Output**:")
        lines.append("")
        lines.append("```")
        lines.append(r["output"].replace("```", "~~~"))
        lines.append("```")
        lines.append("")
    _render_prompt(r, lines)
    return lines


def write_report(run_results, started_at, dry_run):
    from lib import write_report as _write_report
    _write_report(run_results, started_at, "e2e", {
        PASS: render_pass,
        FAIL: render_fail,
        SKIP: render_skip,
        ERR: render_err,
    })


def main():
    started_at = datetime.datetime.now()

    filter_ids, flags, area = parse_args(sys.argv[1:])
    dry_run = "dry-run" in flags
    fail_fast = "fail-fast" in flags
    run_all = "all" in flags

    if filter_ids:
        tests = [t for t in ALL_TESTS if t["id"] in filter_ids]
        if not tests:
            print(f"No tests matched: {filter_ids}")
            sys.exit(1)
    elif area:
        tests = [t for t in ALL_TESTS if t["id"].startswith(area)]
        if not tests:
            print(f"No tests matched area: {area}")
            sys.exit(1)
    elif run_all:
        tests = ALL_TESTS
    else:
        tests = CANARY_TESTS

    results = {PASS: 0, FAIL: 0, SKIP: 0, ERR: 0}
    run_results = []

    total = len(tests)
    if not dry_run:
        name, _ = _get_provider()
        print(f"Provider: {name}")
    print(f"Running {total} test(s)...\n")

    for i, test in enumerate(tests, 1):
        tid = test["id"]
        if not dry_run:
            print(f"  [{i}/{total}] {tid} running...", end="\r", flush=True)

        status, detail, elapsed, output, prompt = run_test(test, dry_run=dry_run)
        results[status] += 1
        run_results.append({
            "id": tid, "status": status,
            "detail": detail, "elapsed": elapsed,
            "output": output, "prompt": prompt,
        })

        if status == PASS:
            print(f"  {status}  {tid}  ({detail})")
        elif status == SKIP:
            print(f"  {status}  {tid}  — {detail}")
        else:
            print(f"  {status}  {tid}")
            print(detail)

        if fail_fast and status in (FAIL, ERR):
            print("\n  --fail-fast: stopping after first failure")
            break

    elapsed = (datetime.datetime.now() - started_at).total_seconds()
    total_run = sum(results.values())
    print(
        f"\n{total_run} tests — "
        f"{results[PASS]} passed  "
        f"{results[FAIL]} failed  "
        f"{results[SKIP]} skipped  "
        f"{results[ERR]} errors"
        f"  ({elapsed:.1f}s)"
    )

    write_report(run_results, started_at, dry_run)

    sys.exit(0 if results[FAIL] == 0 and results[ERR] == 0 else 1)


if __name__ == "__main__":
    main()
