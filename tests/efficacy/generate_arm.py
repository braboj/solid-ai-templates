"""Generate one arm's context file, once, without anybody answering anything.

The design's section 3.3 fixes what the interview is told, requires the
generation to be one non-interactive invocation, and sets the 40-line
budget arm `short` is generated under and the hybrid model arm `hybrid`
asks for. This module is that invocation. It resolves the chain at
the recorded release, builds the prompt from `INTERVIEW.md`, that chain,
the pinned brief and the arm's model and budget, calls the generator,
writes `arms/<arm>/CLAUDE.md`, and refuses to keep a result the
specification leaked into or one over the arm's budget.

Run it once per arm. Re-running it produces a different file and therefore
a different arm, so it refuses to overwrite an existing one without
`--replace`, and the record it writes is what the report cites.
"""

import argparse
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# This module sits a level below the other runners, so the shared library
# is reached by path rather than as a sibling.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
from harness import (RELEASE, VENDORED, TrialError,  # noqa: E402
                     agent_environment, agent_executable,
                     assert_authenticated, assert_outside_repository,
                     prepare_home, read_input)

HERE = os.path.dirname(os.path.abspath(__file__))

# The generated arms' project brief lives in a file of its own, the one copy
# the design links to, for the reason `harness.CHANGE_PROMPT` gives.
BRIEF = os.path.join(HERE, "brief.txt")

# The arms the interview generates, each with the directory under `arms/`
# its file and record live in, the interview's output model it is asked for,
# and its budget as (lines, width) where the design's section 3.3 sets one.
# Each directory is named after its arm. A record written before the rename
# still gives the path the file was generated to, as a record should.
GENERATED = {
    "full": {"dir": "full", "model": "inline", "budget": None},
    "short": {"dir": "short", "model": "inline", "budget": (40, 88)},
    "hybrid": {"dir": "hybrid", "model": "hybrid", "budget": None},
}


def output_path(arm):
    """Where an arm's generated file is committed."""
    return os.path.join(HERE, "arms", GENERATED[arm]["dir"], "CLAUDE.md")


def record_path(arm):
    """The record of the generation behind an arm's file, committed beside
    it. The report cites it, and a scratch directory would not outlive the
    run."""
    return os.path.join(HERE, "arms", GENERATED[arm]["dir"],
                        "generation.json")


# The roots the design's brief resolves to. Each resolves as its own root
# per ADR-035, and their chains overlap heavily, so the union is
# deduplicated before it reaches the prompt.
ROOTS = ["stack-flask", "stack-htmx", "frontend-ux", "frontend-quality"]

# Two lists, because the prompt and the output are different questions.
#
# The PROMPT scan is a wiring check: a generation is never handed
# `SPEC.md`, so any of these appearing in the prompt means the plumbing is
# wrong. It can afford to be broad, since a false positive costs a look
# rather than a generation.
PROMPT_TOKENS = [
    "half-even", "ROUND_HALF_EVEN", "n-for-m",
    "WID-1", "GAD-2", "BOK-3", "SRV-4", "SEE-5",
    "r-tier-wid", "r-bulk-see", "r-pct-bok", "r-pct-all",
    "c-welcome", "c-tenoff", "WELCOME", "TENOFF",
    "PricedInvoice", "TariffError",
    "/invoices/preview", "/invoices/new", "export.csv", "export.json",
    "228.35", "227.07", "195.24", "0.135",
    "TARIFF_ADMIN_PASSWORD", "/sign-in", "/sign-out",
    "Ada Example", "ada@example.com",
]

# The OUTPUT scan asks something narrower, and the prompt scan is what
# earns it: once the prompt is clean, the model demonstrably never read the
# specification, so anything specification-shaped in the output was
# *inferred*. Only arbitrary data can survive that argument — a seed sku, a
# rule id, a figure from the worked example. Nothing derives those.
NON_INVENTABLE = [
    "WID-1", "GAD-2", "BOK-3", "SRV-4", "SEE-5",
    "r-tier-wid", "r-bulk-see", "r-pct-bok", "r-pct-all",
    "c-welcome", "c-tenoff",
    "228.35", "227.07", "195.24",
    "Ada Example", "ada@example.com",
]

# Two tokens taught this the hard way.
#
# `HX-Request` came off the prompt list: the templates document the header
# themselves, as any HTMX guidance would, so the scan fired on a clean
# prompt. `/customers/` came off it the same way, from the templates' REST
# rule, whose example nests `/customers/{id}/orders`. Every other token was then checked the same way against the chain
# at the release and appears nowhere in it.
#
# `TariffError` came off the *output* list on the first real generation. The
# prompt had already scanned clean, so the model could not have read it —
# it named the error base after the package, which is exactly what the
# templates' one-hierarchy rule asks of a package called `tariff`. The
# specification chose the same name for the same reason. `PricedInvoice`,
# the routes, the coupon codes and `half-even` are all derivable the same
# way and stay out of the output list for the same reason.

INSTRUCTION = """\
You are running the interview in `INTERVIEW.md` for one project, without a
person to answer questions.

The project brief below is the whole of what the client has told you. Treat
it as their answers to the interview's exploring and clarifying phases, and
carry out the generating phase: produce the project's `CLAUDE.md`.

Do not ask questions; there is nobody to answer them. Where the brief does
not settle something the interview would have asked, take the default the
interview itself states, and where it states none, choose what the rules
below already imply and move on.

Output the finished `CLAUDE.md` and nothing else: no preamble, no
explanation, no code fence around the whole document.

%s
## Project brief

%s

## The interview

%s

## The rules this project's chain resolves

%s
"""

# What each output model's clause tells the generation, in place of the
# interview's own question about the model. The hybrid clause names where
# the templates sit in the workspace, because the harness vendors them
# there rather than adding a submodule, and a file telling its reader to
# add one would be wrong from its first line.
MODELS = {
    "inline": "Use the interview's inline model.",
    "hybrid": ("Use the interview's hybrid model. The templates are present "
               "in the project at `%s/%s/`, the repository's `%s/` directory "
               "at the same revision as the rules below, as a vendored copy "
               "rather than a submodule: point there, list the template "
               "files to read by their paths under it, and do not tell "
               "anyone to add a submodule."
               % (VENDORED["into"], VENDORED["path"], VENDORED["path"])),
}

# The budget clause, stated in the instruction as the design's section 3.3
# requires. The width keeps a line from carrying a paragraph. The closing
# check adds no content; it asks the model to hold a bound it is already
# given, since a file over it is refused whole.
BUDGET = """\
The finished `CLAUDE.md` MUST be at most {lines} lines, blank lines counted,
and no line may be longer than {width} characters. Keep the rules that matter
most for this project and leave the rest out; a rule that does not fit is left
out, not squeezed onto another rule's line.

Before you answer, measure every line against {width} characters and shorten
or split each one over it, then count the lines again. A file over either
bound is refused whole, never trimmed."""


def arm_clause(arm):
    """The model and budget paragraph for one arm's instruction."""
    entry = GENERATED[arm]
    lines = ["## The output model", "", MODELS[entry["model"]]]
    if entry["budget"]:
        count, width = entry["budget"]
        lines.extend(["", "## The budget", "",
                      BUDGET.format(lines=count, width=width)])
    return "\n".join(lines) + "\n"


def over_budget(document, budget):
    """Every way a generated file exceeds its (lines, width) budget, as
    sentences; empty where it fits or has no budget."""
    if not budget:
        return []
    lines, width = budget
    text = document.rstrip("\n").split("\n")
    findings = []
    if len(text) > lines:
        findings.append("%d lines, over the budget of %d" % (len(text), lines))
    widest = max((len(line) for line in text), default=0)
    if widest > width:
        findings.append("a line of %d characters, over the width of %d"
                        % (widest, width))
    return findings


def read_brief(path=BRIEF):
    """The pinned brief, read from its only copy.

    Reading it here rather than restating it keeps one source of truth: a
    brief duplicated in code drifts from the one the design fixed, and the
    arm would then be generated from something nobody agreed.
    """
    brief = read_input(path)
    if len(brief) < 100:
        raise TrialError("the brief read from %s is implausibly short: %r"
                         % (path, brief))
    return brief


def worktree_at(ref):
    """A throwaway worktree pinned to `ref`, so the chain is that release's.

    Resolution reads a tree. Running the resolver against the checkout would
    read whatever is checked out now, which is the defect this avoids: a
    parallel session moves HEAD and the arm is silently generated from a
    different revision.
    """
    path = tempfile.mkdtemp(prefix="efficacy-%s-" % ref.replace(".", "_"))
    shutil.rmtree(path)
    proc = subprocess.run(["git", "-C", lib.ROOT, "worktree", "add", "-q",
                           "--detach", path, ref],
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise TrialError("could not create a worktree at %s: %s"
                         % (ref, proc.stderr.strip()))
    return path


def remove_worktree(path):
    subprocess.run(["git", "-C", lib.ROOT, "worktree", "remove", "--force",
                    path], capture_output=True, text=True, encoding="utf-8")


def resolve_union(tree, roots):
    """The deduplicated file list for every root, in resolution order."""
    union = []
    for root in roots:
        proc = subprocess.run([sys.executable, "tools/resolve.py", root],
                              cwd=tree, capture_output=True, text=True,
                              encoding="utf-8")
        if proc.returncode != 0:
            raise TrialError("resolving %s failed: %s"
                             % (root, proc.stderr.strip()))
        files = [line.strip() for line in proc.stdout.splitlines()
                 if line.strip().endswith(".md")]
        if not files:
            raise TrialError("root %s resolved to no files" % root)
        for name in files:
            if name not in union:
                union.append(name)
    return union


def read_chain(tree, files):
    """Concatenate the resolved templates, each under its own path."""
    parts = []
    for name in files:
        path = name if os.path.isabs(name) else os.path.join(tree, name)
        if not os.path.exists(path):
            path = os.path.join(tree, "templates", name)
        if not os.path.exists(path):
            raise TrialError("resolved file %s is not in the tree" % name)
        with io.open(path, encoding="utf-8") as handle:
            parts.append("<!-- %s -->\n%s" % (name, handle.read()))
    return "\n\n".join(parts)


def scan(text, label, tokens):
    """Every listed token this text carries, or None if it carries none."""
    hits = {token: text.count(token) for token in tokens if token in text}
    if not hits:
        return None
    return {"where": label, "hits": hits}


def build_prompt(tree, arm):
    interview_path = os.path.join(tree, "templates", "INTERVIEW.md")
    with io.open(interview_path, encoding="utf-8") as handle:
        interview = handle.read()
    files = resolve_union(tree, ROOTS)
    chain = read_chain(tree, files)
    prompt = INSTRUCTION % (arm_clause(arm), read_brief(), interview, chain)
    return prompt, files


def agent_command(home, model, effort, budget):
    """The generator invocation: isolated, offline, non-interactive."""
    argv = [
        agent_executable(), "-p",
        "--output-format", "json",
        "--model", model,
        "--effort", effort,
        "--permission-mode", "bypassPermissions",
        "--setting-sources", "",
        "--settings", os.path.join(home, "settings.json"),
        "--strict-mcp-config",
        "--disallowed-tools", "WebSearch", "WebFetch",
    ]
    if budget is not None:
        argv.extend(["--max-budget-usd", str(budget)])
    return argv


def extract_document(payload, raw):
    """The generated file, from the CLI's JSON envelope or its raw output."""
    if isinstance(payload, dict):
        for key in ("result", "text", "content"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return raw.strip()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate one arm's context file, non-interactively.")
    parser.add_argument("--arm", choices=sorted(GENERATED),
                        help="the arm to generate; required for everything "
                             "but --self-test")
    parser.add_argument("--root",
                        help="scratch directory for the isolated home and the "
                             "record; MUST be outside this repository. "
                             "Required for everything but --self-test")
    parser.add_argument("--ref", default=RELEASE,
                        help="the release to resolve the chain at "
                             "(default %s)" % RELEASE)
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--replace", action="store_true",
                        help="overwrite the arm's existing file; the arm "
                             "changes when you do")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and scan the prompt, call no model")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the leak scan and the budget can fail, "
                             "then exit")
    return parser.parse_args(argv)


def self_test():
    """A scan that cannot fail is not a control, and neither is a budget.

    Plants one specification-only token in a clean text and requires the
    scan to report it, then requires a clean text to scan clean. Plants a
    file one line over the budget and one a character too wide, and
    requires each refused and a file at both bounds kept.
    """
    clean = "A pricing and invoicing web application with discount rules."
    if scan(clean, "clean", PROMPT_TOKENS) is not None:
        print("FAIL: the scan fired on text carrying no specification token")
        return 1
    planted = clean + " Rounding is half-even to two places."
    found = scan(planted, "planted", PROMPT_TOKENS)
    if found is None or "half-even" not in found["hits"]:
        print("FAIL: the scan missed a planted specification token")
        return 1
    print("the leak scan reports a planted token and passes clean text")
    print("  planted hit: %r" % found["hits"])

    budget = GENERATED["short"]["budget"]
    lines, width = budget
    at_bounds = "\n".join(["x" * width] * lines) + "\n"
    if over_budget(at_bounds, budget):
        print("FAIL: a file at both bounds was refused")
        return 1
    long = "\n".join(["x"] * (lines + 1)) + "\n"
    wide = "\n".join(["x" * (width + 1)] + ["x"] * (lines - 1)) + "\n"
    if not over_budget(long, budget) or not over_budget(wide, budget):
        print("FAIL: a file over the budget was kept")
        return 1
    if over_budget(long, None):
        print("FAIL: an arm with no budget refused a file")
        return 1
    print("the budget keeps a file at %d lines of %d characters and refuses "
          "one over either" % (lines, width))
    if "MUST be at most %d lines" % lines not in arm_clause("short") \
            or "measure every line against %d" % width \
            not in arm_clause("short") \
            or "budget" in arm_clause("full").lower():
        print("FAIL: the budget clause is not in short's instruction alone")
        return 1
    print("the budget is stated in short's instruction and no other")
    return 0


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root or not options.arm:
        print("refused: --root and --arm are required")
        return 2

    try:
        assert_outside_repository(options.root)
    except TrialError as error:
        print("refused: %s" % error)
        return 1

    output = output_path(options.arm)
    if os.path.exists(output) and not options.replace:
        print("refused: %s already exists. An arm is generated once; "
              "regenerating changes the arm. Pass --replace if that is what "
              "you mean." % output)
        return 1

    os.makedirs(options.root, exist_ok=True)
    started_at = datetime.datetime.now()
    tree = worktree_at(options.ref)
    try:
        prompt, files = build_prompt(tree, options.arm)
        head = subprocess.run(["git", "-C", tree, "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              encoding="utf-8").stdout.strip()
    finally:
        remove_worktree(tree)

    record = {
        "arm": options.arm,
        "output_model": GENERATED[options.arm]["model"],
        "budget": GENERATED[options.arm]["budget"],
        "ref": options.ref,
        "commit": head,
        "roots": ROOTS,
        "resolved_files": files,
        "prompt_chars": len(prompt),
        "model": options.model,
        "effort": options.effort,
        "started_at": started_at.isoformat(timespec="seconds"),
    }
    print("chain at %s (%s): %d unique files, %d prompt chars"
          % (options.ref, head[:8], len(files), len(prompt)))

    leak = scan(prompt, "prompt", PROMPT_TOKENS)
    record["prompt_leak"] = leak
    if leak is not None:
        print("refused: the prompt carries specification-only tokens, so the "
              "wiring is wrong: %r" % leak["hits"])
        return 1
    print("prompt carries no specification-only token")

    prompt_path = os.path.join(options.root, "arm-%s-prompt.txt" % options.arm)
    with io.open(prompt_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(prompt)
    record["prompt_file"] = prompt_path

    if options.dry_run:
        record["outcome"] = "dry-run"
        print("dry run: prompt written to %s, no model called" % prompt_path)
        return write_record(options.root, record, started_at)

    home = prepare_home(options.root)
    try:
        ready = assert_authenticated(home, agent_environment,
                                     agent_executable())
    except TrialError as error:
        print("refused: %s" % error)
        record["outcome"] = "refused: not authenticated"
        return write_record(options.root, record, started_at) or 1
    record["auth_probe"] = ready
    print("the isolated home reaches the model: %r" % ready)

    argv_ = agent_command(home, options.model, options.effort, options.budget)
    record["command"] = argv_
    env = agent_environment(home)

    started = time.monotonic()
    try:
        proc = subprocess.run(argv_, input=prompt, cwd=options.root, env=env,
                              capture_output=True, text=True,
                              encoding="utf-8", timeout=options.timeout)
    except subprocess.TimeoutExpired:
        record["outcome"] = "timeout"
        print("the generator did not finish within %ds" % options.timeout)
        return write_record(options.root, record, started_at) or 1
    record["elapsed_s"] = round(time.monotonic() - started, 1)
    record["exit_status"] = proc.returncode

    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        payload = None
    record["result"] = payload if isinstance(payload, dict) else None
    document = extract_document(payload, proc.stdout)

    if proc.returncode != 0 or not document:
        record["outcome"] = "failed"
        record["stderr"] = proc.stderr[-4000:]
        print("the generator failed (status %s)" % proc.returncode)
        return write_record(options.root, record, started_at) or 1

    leak = scan(document, "generated file", NON_INVENTABLE)
    record["output_leak"] = leak
    excess = over_budget(document, GENERATED[options.arm]["budget"])
    record["over_budget"] = excess
    if leak is not None or excess:
        rejected = os.path.join(options.root, "arm-%s-REJECTED.md"
                                % options.arm)
        with io.open(rejected, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(document)
        if leak is not None:
            record["outcome"] = "refused: specification leaked"
            print("refused: the generated file carries data only the "
                  "specification supplies: %r" % leak["hits"])
        else:
            record["outcome"] = "refused: over the budget"
            print("refused: the generated file is %s" % "; ".join(excess))
        print("the rejected file is at %s" % rejected)
        return write_record(options.root, record, started_at) or 1

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with io.open(output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(document.rstrip() + "\n")
    record["outcome"] = "generated"
    record["output"] = output
    record["output_chars"] = len(document)
    record["output_lines"] = document.rstrip("\n").count("\n") + 1
    record["output_width"] = max(len(line) for line in document.splitlines())
    print("wrote %s: %d lines, %d chars, widest line %d"
          % (output, record["output_lines"], record["output_chars"],
             record["output_width"]))
    print("no specification-only token in the generated file")
    keep_record(record, record_path(options.arm))
    print("Record kept beside it: %s" % record_path(options.arm))
    return write_record(options.root, record, started_at)


def keep_record(record, path):
    """Write the record of the generation behind the committed file."""
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)


def write_record(root, record, started_at):
    path = os.path.join(root, "arm-%s-generation-%s.json"
                        % (record["arm"],
                           started_at.strftime("%Y-%m-%dT%H-%M-%S")))
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    print("Record: %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
