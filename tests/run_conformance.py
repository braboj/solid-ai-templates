"""Run the checks the templates embed against this repository.

`run_smoke.py` checks that the templates COMPOSE -- that references
resolve, that IDs are unique, that chains are non-empty. It does not run
the checks the templates prescribe to their consumers, and this repository
is a consumer of its own base tier. Three rules shipped and were violated
here before anything ran them.

Usage:
    py tests/run_conformance.py            # every registered check
    py tests/run_conformance.py --list     # dispositions, run nothing
    py tests/run_conformance.py <find>     # one check, by its find string

A check reaches one of four results. PASS and FAIL are automatic
verdicts; ERR is a check that could not run; REVIEW is a check whose
verdict is a judgement, and its output is the result a person reads.
REVIEW is counted on its own line rather than among the passes, and it
does not fail the run -- the exit status answers whether a verdict was
reached and was negative.
"""

import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conformance import CHECKS, RUN, SKIP, SILENT, MANUAL
from lib import PASS, FAIL, SKIP as SKIPPED, ROOT, write_report

ERR = "ERR"

# A check whose verdict is a judgement gets its own status. Recording it
# as a pass folds a finding into a count that says there is nothing to
# look at: a run that surfaced the output and then contradicted it in
# the summary.
REVIEW = "REVIEW"

TEMPLATES = os.path.join(ROOT, "templates")

FENCE = re.compile(r"^(\s*)```(\w*)\s*$")
RUNNABLE = ("bash", "python", "sh", "py")

# The heredoc wrapper a template uses to introduce a Python check. The body
# is what runs; the wrapper is shell syntax the runner supplies itself.
HEREDOC_OPEN = re.compile(r"^\s*py - <<'EOF'\s*$")


def iter_blocks():
    """Yield (rel_path, line, language, body) for every fenced block.

    Counts blocks in EVERY language, not only the runnable ones. The total
    is what the extraction is reconciled against: a language filter that
    silently stops matching looks identical to a template that lost its
    checks.
    """
    for base, _dirs, files in os.walk(TEMPLATES):
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, TEMPLATES).replace(os.sep, "/")
            lines = io.open(path, encoding="utf-8").read().splitlines()
            index = 0
            while index < len(lines):
                match = FENCE.match(lines[index])
                if match and match.group(2):
                    start = index
                    index += 1
                    while index < len(lines) and lines[index].strip() != "```":
                        index += 1
                    yield rel, start + 1, match.group(2), lines[start + 1:index]
                index += 1


def unwrap(body):
    """Strip a heredoc wrapper and the indent a list item added.

    A fence nested under a bullet is indented, and the indent is part of
    every line inside it. Left in place it makes the first statement of a
    Python check an indentation error.
    """
    inner = [line for line in body
             if not HEREDOC_OPEN.match(line) and line.strip() != "EOF"]
    pad = min((len(l) - len(l.lstrip()) for l in inner if l.strip()),
              default=0)
    return [l[pad:] if l.strip() else l for l in inner]


def is_python(body):
    return any(HEREDOC_OPEN.match(line) for line in body)


def run_block(body, language, workdir):
    """Run one check FROM the repository root, with its source OUTSIDE it.

    A check written into the tree it inspects can match its own source, so
    the extracted file is placed in a scratch directory instead. See the
    self-match rule in `base-quality`.
    """
    lines = unwrap(body)
    if is_python(body) or language in ("python", "py"):
        suffix, argv = ".py", [sys.executable]
    else:
        # Resolve bash to an absolute path. On Windows a bare "bash" can
        # reach the WSL launcher in System32, which cannot see a Windows
        # path and reports the script as missing.
        suffix, argv = ".sh", [shutil.which("bash") or "bash"]
    script = os.path.join(workdir, "check%s" % suffix)
    io.open(script, "w", encoding="utf-8", newline="\n").write(
        "\n".join(lines) + "\n")

    # bash on Windows reads a native path's separators as escapes and
    # loses them, reporting the collapsed name as not found.
    argv.append(script.replace(os.sep, "/"))
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, [l for l in out.splitlines() if l.strip()]


def verdict(entry, code, out):
    """Apply the entry's pass predicate. Returns a list of failures.

    `expect` is either SILENT, MANUAL, or a list naming what each line the
    check declares must hold -- "nonzero", "zero" or "any". Anything after
    the declared lines is a finding. The per-line form is needed because a
    check's own pass condition mixes the two directions: a scanned count
    MUST be non-zero, since zero means it reached nothing, while the
    violation count beside it MUST be zero.
    """
    expect = entry.get("expect")

    # grep exits 1 when it matches nothing, which is the clean result for
    # a check whose second command must print nothing.
    exit_matters = not entry.get("grep")

    if expect == SILENT:
        if exit_matters and code != 0:
            return ["exited %d" % code]
        return ["printed %d line(s), expected none: %s"
                % (len(out), out[0])] if out else []

    if isinstance(expect, list):
        if exit_matters and code != 0:
            return ["exited %d: %s" % (code, out[-1] if out else "")]
        if len(out) < len(expect):
            return ["printed %d line(s), expected at least %d"
                    % (len(out), len(expect))]
        for rule, line in zip(expect, out):
            number = re.search(r"(\d+)\s*$", line)
            if not number:
                return ["'%s' does not end in a count" % line]
            value = int(number.group(1))
            if rule == "nonzero" and value == 0:
                return ["'%s' counted zero -- the check reached nothing"
                        % line]
            if rule == "zero" and value != 0:
                return ["'%s' should be zero" % line]
        extra = out[len(expect):]
        return ["%d finding(s), first: %s" % (len(extra), extra[0])] \
            if extra else []

    # MANUAL: the check runs and is reported; only a crash is a failure.
    if exit_matters and code != 0:
        return ["exited %d: %s" % (code, out[-1] if out else "")]
    return []


def passed(result):
    """Render a passing check, carrying the output a manual one produced."""
    if not result["output"]:
        return ["### %s  %s" % (result["status"], result["id"]), ""]
    return (["### %s  %s — %s" % (result["status"], result["id"],
                                  result["title"]), ""]
            + ["```"] + result["output"] + ["```", ""])


def main():
    started_at = datetime.datetime.now()
    args = sys.argv[1:]
    listing = "--list" in args
    wanted = [a for a in args if not a.startswith("--")]

    blocks = list(iter_blocks())
    runnable = [b for b in blocks if b[2] in RUNNABLE]
    print("fenced blocks in templates/: %d" % len(blocks))
    print("of those, runnable-language:  %d" % len(runnable))
    print("registered dispositions:      %d" % len(CHECKS))

    if not blocks:
        print("\nFAIL: extracted nothing -- the fence pattern reached no "
              "template")
        sys.exit(1)

    # Reconcile the registry against the corpus. An entry matching nothing
    # and a block matching nothing are different defects and both are
    # reported: a registry drifting out of step with the templates is how
    # a check goes unexamined.
    matched, problems = {}, []
    for entry in CHECKS:
        hits = [b for b in runnable
                if b[0] == entry["file"] and any(entry["find"] in l
                                                 for l in b[3])]
        if len(hits) != 1:
            problems.append("%s: 'find' matched %d blocks, expected 1 -- %s"
                            % (entry["file"], len(hits), entry["find"][:40]))
            continue
        key = (hits[0][0], hits[0][1])
        if key in matched:
            problems.append("%s:%d claimed by two entries" % key)
        matched[key] = (entry, hits[0])

    for block in runnable:
        if (block[0], block[1]) not in matched:
            first = next((l.strip() for l in block[3] if l.strip()), "")
            problems.append("%s:%d has no disposition -- %s"
                            % (block[0], block[1], first[:50]))

    if problems:
        print("\nRegistry does not account for the templates:\n")
        for line in problems:
            print("  %s" % line)
        print("\n%d problem(s). Add a disposition in tests/conformance.py."
              % len(problems))
        sys.exit(1)

    print("every runnable block has a disposition\n")

    entries = [matched[k] for k in sorted(matched)]
    if wanted:
        entries = [e for e in entries
                   if any(w in e[0]["find"] or w in e[0]["file"]
                          for w in wanted)]
        if not entries:
            print("nothing matched: %s" % wanted)
            sys.exit(1)

    results = {PASS: 0, FAIL: 0, SKIPPED: 0, ERR: 0, REVIEW: 0}
    run_results = []
    workdir = tempfile.mkdtemp(prefix="sait-conformance-")

    try:
        for entry, block in entries:
            rel, line = block[0], block[1]
            title = entry["title"]
            where = "%s:%d" % (rel, line)

            if entry["do"] == SKIP:
                if not listing:
                    print("  %-6s %s" % (SKIPPED, title))
                    print("        %s -- %s" % (where, entry["reason"]))
                results[SKIPPED] += 1
                run_results.append({"id": where, "title": title,
                                    "status": SKIPPED, "failures": [],
                                    "error": entry["reason"]})
                continue

            if listing:
                print("  %-5s %s (%s)" % (entry["do"], title, where))
                continue

            try:
                code, out = run_block(block[3], block[2], workdir)
            except Exception as exc:
                print("  %-6s %s\n        %s -- %s" % (ERR, title, where, exc))
                results[ERR] += 1
                run_results.append({"id": where, "title": title,
                                    "status": ERR, "failures": [],
                                    "error": str(exc)})
                continue

            failures = verdict(entry, code, out)
            judgement = entry.get("expect") == MANUAL

            # A manual check has no automatic verdict, so its output IS the
            # result. Carry it to the log and the report, or the check runs
            # and tells nobody what it saw.
            reported = out if judgement else []

            # A judgement check that printed nothing reported nothing. That
            # is a defect in the check rather than a reading for the
            # operator, so it fails rather than joining the review pile.
            if judgement and not failures and not reported:
                failures = ["printed nothing -- a judgement check reports "
                            "what it inspected"]

            if failures:
                status = FAIL
            elif judgement:
                status = REVIEW
            else:
                status = PASS

            print("  %-6s %s" % (status, title))
            if status == FAIL:
                print("        %s" % where)
            for line in failures or reported:
                print("        %s" % line)
            results[status] += 1
            run_results.append({"id": where, "title": title,
                                "status": status, "failures": failures,
                                "error": "", "output": reported})
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if listing:
        return

    ran = (results[PASS] + results[FAIL] + results[ERR]
           + results[REVIEW])
    print("\n%d block(s) registered - %d ran, %d skipped as not applicable"
          % (len(CHECKS), ran, results[SKIPPED]))
    print("%d passed  %d failed  %d errors  %d awaiting a reading"
          % (results[PASS], results[FAIL], results[ERR],
             results[REVIEW]))

    # The count alone reads as a tally of things that went fine. Say what
    # the operator still owes, beside it.
    if results[REVIEW]:
        print("%d check(s) produced a reading no rule can judge. Read "
              "them above before calling the run clean."
              % results[REVIEW])

    if ran == 0:
        print("\nFAIL: ran nothing. Every check reported as not applicable "
              "is a check that never verified anything.")
        sys.exit(1)

    write_report(run_results, started_at, "conformance", {
        FAIL: lambda r: ["### %s  %s — %s" % (r["status"], r["id"],
                                              r["title"]), ""]
                        + ["- %s" % f for f in r["failures"]] + [""],
        SKIPPED: lambda r: ["### %s  %s — %s" % (r["status"], r["id"],
                                                 r["title"]), "",
                            r["error"], ""],
        PASS: passed,
        REVIEW: passed,
    })

    sys.exit(1 if results[FAIL] or results[ERR] else 0)


if __name__ == "__main__":
    main()
