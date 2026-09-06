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

A check reaches one of five results. PASS and FAIL are automatic
verdicts; ERR is a check that could not run; N/A is a check that
determined this run that it does not apply; REVIEW is a check whose
verdict is a judgement, and its output is the result a person reads.
REVIEW is counted on its own line rather than among the passes, and it
does not fail the run -- the exit status answers whether a verdict was
reached and was negative.

Every check's output reaches the report, whatever its result. Carrying it
only for REVIEW made visibility a reason to leave a verdict unreached.
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

from conformance import CHECKS, RUN, SKIP, SILENT, MANUAL, READ
from lib import (PASS, FAIL, SKIP as SKIPPED, ROOT, write_report,
                 template_documents)

ERR = "ERR"

# A check whose verdict is a judgement gets its own status. Recording it
# as a pass folds a finding into a count that says there is nothing to
# look at: a run that surfaced the output and then contradicted it in
# the summary.
REVIEW = "REVIEW"

# A check whose question is tied to a moment reports that the moment is
# not in progress by exiting with this status. It is not SKIP: SKIP is
# decided in advance, by a person, about this repository, and this is the
# check answering, this run, about this moment. Counting it as awaiting a
# reading asks for a reader the check has already spared.
NOT_APPLICABLE = 3
NA = "N/A"

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

    # Ask git what belongs to the repository. A walk of the directory reads
    # whatever happens to sit there, so a gitignored scratch file becomes a
    # block with no disposition and fails the gate.
    for tracked in template_documents():
        rel = tracked[len("templates/"):]
        path = os.path.join(ROOT, tracked.replace("/", os.sep))
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
    check declares must hold -- "nonzero", "zero", "any", or "line" for a
    declared line that carries no count. Anything after the declared lines
    is a finding. The per-line form is needed because a check's own pass
    condition mixes the two directions: a scanned count MUST be non-zero,
    since zero means it reached nothing, while the violation count beside
    it MUST be zero.

    READ ends the scored run. The lines from there on are a reading
    addressed to whoever the verdict's failure summons, so they are carried
    into the report and never scored -- which is what lets a check reach a
    verdict on the counts that are decided without failing on the lines
    that are not.
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

        # Everything from READ on is the reading, so only the lines
        # before it are declared, and only they set the length the
        # check must reach.
        scored = expect[:expect.index(READ)] if READ in expect else expect
        if len(out) < len(scored):
            return ["printed %d line(s), expected at least %d"
                    % (len(out), len(scored))]
        for rule, line in zip(scored, out):
            if rule == "line":
                continue
            number = re.search(r"(\d+)\s*$", line)
            if not number:
                return ["'%s' does not end in a count" % line]
            value = int(number.group(1))
            if rule == "nonzero" and value == 0:
                return ["'%s' counted zero -- the check reached nothing"
                        % line]
            if rule == "zero" and value != 0:
                return ["'%s' should be zero" % line]
        if READ in expect:
            return []
        extra = out[len(scored):]
        return ["%d finding(s), first: %s" % (len(extra), extra[0])] \
            if extra else []

    # MANUAL: the check runs and is reported; only a crash is a failure.
    if exit_matters and code != 0:
        return ["exited %d: %s" % (code, out[-1] if out else "")]
    return []


def reading(result):
    """Render a check, carrying what it printed.

    Every result carries its output, a failure included. A failure names
    the line that broke the predicate and not the counts around it, and
    those counts are what say whether the check reached its inputs -- so
    a control run that proves a narrowed check still reads them has
    nothing to read without this.
    """
    body = result.get("output") or []
    failures = ["- %s" % f for f in result.get("failures") or []]
    if not body and not failures:
        return ["### %s  %s" % (result["status"], result["id"]), ""]
    head = ["### %s  %s — %s" % (result["status"], result["id"],
                                 result["title"]), ""]
    if failures:
        head += failures + [""]
    return head + (["```"] + body + ["```", ""] if body else [])


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
        # A judgement with no stated reason is indistinguishable from a
        # verdict nobody got round to writing, and the pile is where the
        # difference stops being visible.
        if entry.get("expect") == MANUAL and not entry.get("reason"):
            problems.append("%s: manual with no reason -- %s"
                            % (entry["file"], entry["title"][:40]))

        # A check mixing a verdict with a reading MUST say which lines
        # are which. Left unstated, the unscored tail cannot be told
        # from a predicate that stopped short.
        declared = entry.get("expect")
        if isinstance(declared, list) and READ in declared \
                and not entry.get("reading"):
            problems.append("%s: a reading with nothing said about it -- %s"
                            % (entry["file"], entry["title"][:40]))

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

    results = {PASS: 0, FAIL: 0, SKIPPED: 0, ERR: 0, REVIEW: 0, NA: 0}
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

            # Asked before the predicate, because a check that does not
            # apply prints the sentence explaining it and none of the
            # lines the predicate expects.
            not_applicable = code == NOT_APPLICABLE

            failures = [] if not_applicable else verdict(entry, code, out)
            judgement = entry.get("expect") == MANUAL and not not_applicable

            # A judgement check's output IS its result, so it goes to the
            # terminal where the operator is. Every check's output goes to
            # the report: what a check saw MUST NOT depend on how its
            # verdict was reached, or keeping a reading visible costs a
            # verdict that was available.
            reported = out if judgement else []

            # A judgement check that printed nothing reported nothing. That
            # is a defect in the check rather than a reading for the
            # operator, so it fails rather than joining the review pile.
            if judgement and not failures and not out:
                failures = ["printed nothing -- a judgement check reports "
                            "what it inspected"]

            if failures:
                status = FAIL
            elif not_applicable:
                status = NA
            elif judgement:
                status = REVIEW
            else:
                status = PASS

            print("  %-6s %s" % (status, title))
            if status == FAIL:
                print("        %s" % where)
            for line in failures or reported or (out if not_applicable else []):
                print("        %s" % line)
            results[status] += 1
            run_results.append({"id": where, "title": title,
                                "status": status, "failures": failures,
                                "error": "", "output": out})
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if listing:
        return

    ran = (results[PASS] + results[FAIL] + results[ERR]
           + results[REVIEW] + results[NA])
    print("\n%d block(s) registered - %d ran, %d skipped as not applicable"
          % (len(CHECKS), ran, results[SKIPPED]))
    print("%d passed  %d failed  %d errors  %d not applicable  "
          "%d awaiting a reading"
          % (results[PASS], results[FAIL], results[ERR], results[NA],
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
        FAIL: reading,
        SKIPPED: lambda r: ["### %s  %s — %s" % (r["status"], r["id"],
                                                 r["title"]), "",
                            r["error"], ""],
        PASS: reading,
        REVIEW: reading,
        NA: reading,
    })

    sys.exit(1 if results[FAIL] or results[ERR] else 0)


if __name__ == "__main__":
    main()
