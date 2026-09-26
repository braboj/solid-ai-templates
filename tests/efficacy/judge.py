"""Judge one frozen efficacy trial, blind.

The design's section 5 fixes what this asks for: a 1-5 rubric with a quoted
evidence line per score, a pattern census that says what each pattern removes
or opens, and the three primary dimensions the report leads with. Section 7
fixes the controls: blind to arm, order shuffled, condition markers
stripped, model id and reasoning effort recorded, and a judge from another
vendor reading a sample as a cross-check.

Two properties make the result readable as evidence rather than as an
opinion. The rubric is a JSON Schema the CLI enforces on the final message,
so a score is machine-read by construction. And every evidence line is
checked against the bundle it was supposedly quoted from: a judge that never
opened the code can still return plausible numbers, and the share of evidence
that is actually present in the tree is what separates the two.
"""

import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
import score  # noqa: E402
from harness import (LiveRunError, TrialError, canonical,  # noqa: E402
                     claim_area, claim_refusal_check, release_area)

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.basename(__file__)
SPEC = os.path.join(HERE, "SPEC.md")

# Every specification a round has built against, by the sha256 of its text
# with line endings normalised. A tree is judged against the one it carries,
# which is the copy the harness gave its agent, and never against a later one:
# that would score it on features it was never asked for. The current file is
# accepted as well, so a round's specification is listed here once a later one
# replaces it.
SPECS = {
    "ebecfff1951ce0f4f2d5a0d95564be7e6eda15283905116e83805020e7cb85f5":
        "rounds 1 and 2",
    "c9e24a3850d1b7033ad8f2261f6e7a2b18c62d490020d1d2d8e5ad5b144da7b2":
        "the calibration trial",
}

# The model each CLI judges with. The rounds' judge is Claude: it shares a
# vendor with the generator, which a judge from another vendor would not, but
# that one's plan allows about thirty judgings a week and a round needs three
# times as many. The other vendor's model reads a sample of each round as a
# cross-check, and its readings are never meaned with the rounds' judge's.
JUDGE_MODELS = {"claude": "claude-opus-5-5", "codex": "gpt-6-astra"}

# The CLI that drives the rounds' judge.
DEFAULT_CLI = "claude"

# The local default is low, and the rubric is a reasoning task over long
# code, so the effort is set on the command and recorded rather than
# inherited from this machine's configuration.
JUDGE_EFFORT = "high"

# The five SOLID dimensions plus the rest of the rubric. `design` is asked for
# directly because the report leads with it: an aggregate this module invented
# from the five would be a score the judge never gave.
DIMENSIONS = (
    "design", "srp", "ocp", "lsp", "isp", "dip", "naming_and_abstraction",
    "error_design", "readability", "maintainability", "test_quality",
    "security", "data_protection",
)

# What the report leads with, owner-declared in the design.
PRIMARY = ("design", "readability", "maintainability", "security",
           "data_protection")

# Never shown to the judge. A context file names the condition, and so does a
# README that thanks one: both are stripped from the bundle, and what was
# stripped is recorded.
EXCLUDED_NAMES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules",
                  ".windsurfrules", "copilot-instructions.md")
EXCLUDED_DIRS = (".git", ".cursor", ".github", "venv", ".venv", "__pycache__",
                 ".score-pages", "node_modules", ".pytest_cache", ".ruff_cache",
                 "build", "dist", ".mypy_cache",

                 # The hybrid arm's vendored templates, which name the arm on
                 # every page: stripped with the context file, under the
                 # repository's own name.
                 "solid-ai-templates")

# What scoring leaves in the tree it measured: tool caches, reports and the
# install's metadata. None of it is the trial's code, and the caches hold
# absolute paths through the scoring area, which name the trial and so its arm.
SCORING_OUTPUT_DIRS = (".complexipy_cache", ".grimp_cache")
SCORING_OUTPUT_NAMES = (".coverage", "complexipy.json")

# Tokens that would tell the judge which arm it is reading. Masked in place,
# with the count recorded: a bundle that needed many of them is itself a
# finding about the arm.
#
# Every token here has to be one no implementation would use as an
# identifier. The harness's own arm labels are not on the list for that
# reason: masking `candidate` would rewrite a plausible variable name and
# damage the code of whichever arm happened to use the word, so blinding
# would have changed what is being judged.
MARKERS = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "solid-ai-templates",
           "Claude Code", "claude.ai", "CLAUDE", "context file",
           "arm A", "arm B", "arm C", "arm none", "arm full", "arm short",
           "arm hybrid", "arm hand")

MASK = "[redacted]"

TEXT_SUFFIXES = (".py", ".md", ".txt", ".toml", ".cfg", ".ini", ".html",
                 ".jinja", ".j2", ".css", ".js", ".json", ".yaml", ".yml",
                 ".rst", ".adoc", ".env", ".in")

PROMPT = """\
You are reviewing one submission that implements the application described in
SPEC.md, which is in the directory you have been given. Read the code before
scoring it; every score must quote a line from the tree.

Score each dimension from 1 to 5, where 1 is poor and 5 is excellent:

- design: SOLID overall and pattern use, taken together
- srp: one reason to change per module
- ocp: rule kinds, jurisdictions and export formats are extension points
- lsp: every rule kind honours the rule contract, every export the renderer's
- isp: the public API is no larger than the specification requires
- dip: the domain is independent of Flask, SQLite and the request cycle
- naming_and_abstraction: names carry intent at a consistent level
- error_design: one error hierarchy, refusals where the specification says
- readability: function length, nesting, names a reader can follow
- maintainability: how quickly a reader finds where a change goes
- test_quality: what the tests assert, not how many there are
- security: how sign-in, sessions, secrets and queries are defended
- data_protection: how the customers' personal data is held, logged,
  exported and erased

Five of those carry the report and are anchored, so that 3 is a described
place on the scale rather than wherever ordinary work lands. Score against
the description nearest what you read, and use 2 and 4 for the gaps between.

design
  1  the layers are not kept apart: the domain's modules are merged into
     one, or the domain imports the web framework, and adding a discount
     kind means editing the algorithm, the form and the template
  3  the domain is a set of modules of its own that imports nothing from
     the web layer, and the algorithm dispatches on concrete rule classes,
     so a new kind reopens more than one function; that dispatch alone, with
     the layers kept apart, is a 3 and not lower
  5  a discount kind is added by writing one class: the algorithm, the
     persistence mapping, the form and the template read a contract or a
     registry and name no kind of their own

readability
  1  functions run past a screen with nested conditionals, names abbreviate,
     and the algorithm has to be held in the head to be followed
  3  followable, with dense expressions or accumulators whose shape has to be
     reconstructed before the surrounding code reads
  5  each function does one thing at one level, names carry the intent, and
     no expression needs a second reading

maintainability
  1  the modules do not divide the work: one of them holds the domain and
     the layers around it together, so a reader has no boundary to start
     from and the pricing rules sit beside the web framework they import
  3  the modules divide along lines a reader can name and the domain is
     quick to find, but one discount kind's behaviour is still spread
     across the algorithm, the persistence layer and the templates
  5  each module's responsibility is evident from where it sits, the
     domain depends on nothing layered above it, and every fact about a
     discount kind sits in one place

security
  1  a secret sits in plain sight or input reaches a query or a redirect
     unchecked: the password stored or compared as typed, the secret key a
     literal in the source, SQL built from strings, `next` followed wherever
     it points
  3  the common defences are all present - a hashed password, parameterised
     queries, one sign-in guard, a CSRF token on every form, `next` checked
     for a local path - and the application stops there: the secret key
     comes from a default or a file the deployment cannot set, and the
     session cookie and the responses carry only the framework's defaults
  5  everything in 3, and the deployment is configured on purpose: the
     secret key is read from the environment, the session cookie's flags
     are set, every response carries security headers, and each check a
     reviewer audits, such as the redirect target, is one named function

data_protection
  1  personal data escapes: customer fields are written to the logs, erasure
     leaves the data behind, or an export reaches past one customer
  3  erasure and export do what the specification asks, but nothing names
     what is personal: each query, view and template lists the fields or
     checks the erased flag for itself, so the next field or page added is
     one to forget
  5  one declaration names the personal fields, and erasure, export and
     every read of a single customer go through it; an erased customer
     cannot be read by accident, and erased data does not linger in the
     database file

A submission that removes what a lower anchor describes scores above it, even
where the result is ordinary: these are descriptions of the code, not of how
impressive it is.

For each score, `evidence` must be a short verbatim line copied from a file in
the tree, and `file` the path it came from. Do not paraphrase the line.

Then census the design patterns you find. For each: where it is, what it
removes (a duplication, a conditional ladder) or opens (an extension point),
how many implementors it has, and a verdict - `warranted` when it removes or
opens something real, `over_engineered` when it has one implementor and
removes nothing, `missed` for a place where a pattern was warranted and a
conditional ladder stands instead.

Answer with JSON only, in the shape the schema requires.
"""


def schema():
    """The rubric as a JSON Schema, so the CLI enforces the shape.

    One definition produces both the schema and the validation below, which is
    what keeps a dimension from being added to the prompt and silently not
    read.
    """
    score_shape = {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 1, "maximum": 5},
            "evidence": {"type": "string", "minLength": 3},
            "file": {"type": "string"},
        },
        "required": ["score", "evidence", "file"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "rubric": {
                "type": "object",
                "properties": {name: score_shape for name in DIMENSIONS},
                "required": list(DIMENSIONS),
                "additionalProperties": False,
            },
            "patterns": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "where": {"type": "string"},
                        "removes_or_opens": {"type": "string"},
                        "implementors": {"type": "integer", "minimum": 0},
                        "verdict": {"type": "string",
                                    "enum": ["warranted", "over_engineered",
                                             "missed"]},
                    },
                    "required": ["pattern", "where", "removes_or_opens",
                                 "implementors", "verdict"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["rubric", "patterns"],
        "additionalProperties": False,
    }


def is_text(path):
    return path.lower().endswith(TEXT_SUFFIXES)


def mask_markers(text):
    """Replace every condition marker, and say how many were replaced."""
    count = 0
    for marker in MARKERS:
        pattern = re.compile(re.escape(marker), re.IGNORECASE)
        text, hits = pattern.subn(MASK, text)
        count += hits
    return text, count


def copied_dir(name):
    """Whether a directory of the trial's tree belongs in its bundle."""
    return not (name in EXCLUDED_DIRS or name in SCORING_OUTPUT_DIRS
                or name.endswith(".egg-info"))


def build_bundle(tree, target):
    """Copy one trial's tree into a blind bundle and return what was stripped.

    The context file is the loudest marker but not the only one: a README that
    credits its conventions names the arm just as clearly, so the text files
    are masked as they are copied and the totals are recorded.
    """
    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(target)
    removed, masked = [], 0
    for base, directories, names in os.walk(tree):
        directories[:] = [d for d in directories if copied_dir(d)]
        for name in names:
            source = os.path.join(base, name)
            relative = os.path.relpath(source, tree)
            if name in EXCLUDED_NAMES:
                removed.append(relative)
                continue
            if (name.startswith(".score-") or name.endswith(".sqlite")
                    or name in SCORING_OUTPUT_NAMES):
                continue
            destination = os.path.join(target, relative)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            if not is_text(source):
                shutil.copyfile(source, destination)
                continue
            with io.open(source, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            text, hits = mask_markers(text)
            masked += hits
            with io.open(destination, "w", encoding="utf-8",
                         newline="") as handle:
                handle.write(text)

    # The judge needs the task to score against it, and the tree carries the
    # one its agent was given. Written unmasked: a specification a round ran
    # is identical for every arm, so it carries no condition.
    spec = tree_spec(tree)
    if spec:
        with io.open(os.path.join(target, "SPEC.md"), "wb") as handle:
            handle.write(spec.pop("text"))
    return {"removed": removed, "markers_masked": masked, "spec": spec,
            "leaks": surviving_markers(target, os.path.basename(tree)),
            "digest": digest(target)}


def spec_text(path):
    """A specification's bytes with line endings normalised, or None."""
    if not os.path.isfile(path):
        return None
    with io.open(path, "rb") as handle:
        return handle.read().replace(b"\r\n", b"\n")


def tree_spec(tree):
    """The specification a tree carries, if it is one a round ran.

    Returns its text, sha256 and round, or None. An agent can edit its copy,
    so the copy is checked against the specifications rounds ran, not trusted.
    """
    text = spec_text(os.path.join(tree, "SPEC.md"))
    if text is None:
        return None
    known = dict(SPECS)
    current = hashlib.sha256(spec_text(SPEC)).hexdigest()
    known.setdefault(current, "the current specification")
    found = hashlib.sha256(text).hexdigest()
    if found not in known:
        return None
    return {"text": text, "sha256": found, "round": known[found]}


def surviving_markers(bundle, trial):
    """Markers, and paths naming the trial, still readable in the bundle.

    The masking pass is checked rather than trusted: a marker in a file
    extension the copy treated as binary, or in a name rather than in text,
    would leave the arm legible and every later control would read as blind.
    """

    # The trial's name matched only between path separators, where a path
    # through the run root or the scoring area puts it and no implementation
    # would. The escaped separator of a JSON string matches too.
    segment = re.compile(r"[\\/]%s[\\/]" % re.escape(trial))

    # Every directory, including the ones the copy leaves out: the judge reads
    # the whole bundle, so a scan that skipped what the copy skipped would
    # pass a bundle the copy had got wrong.
    found = []
    for base, _, names in os.walk(bundle):
        for name in names:
            path = os.path.join(base, name)
            relative = os.path.relpath(path, bundle)
            for marker in MARKERS:
                if marker.lower() in name.lower():
                    found.append([relative, marker, "in the file name"])
            if trial in relative.split(os.sep):
                found.append([relative, trial, "in the path"])

            # Every file, decoded loosely, not only the suffixes the masker
            # recognises. A scan that skipped what the masker skipped would
            # share its blind spot exactly, and a marker in an extension
            # neither of them knows would read as a blind bundle.
            with io.open(path, "rb") as handle:
                raw = handle.read().decode("utf-8", "replace")
            text = raw.lower()
            for marker in MARKERS:
                if marker.lower() in text:
                    found.append([relative, marker, "in the bytes"])
            if segment.search(raw):
                found.append([relative, trial, "as a path segment"])
    return found


def digest(tree):
    """A digest over the bundle, so a score names the bytes it graded."""
    accumulator = hashlib.sha256()
    for base, directories, names in os.walk(tree):
        directories.sort()
        for name in sorted(names):
            path = os.path.join(base, name)
            accumulator.update(os.path.relpath(path, tree).encode("utf-8"))
            with io.open(path, "rb") as handle:
                accumulator.update(handle.read())
    return accumulator.hexdigest()[:16]


def bundle_text(bundle):
    """Every text line in the bundle, for checking quoted evidence."""
    lines = set()
    for base, directories, names in os.walk(bundle):
        directories[:] = [d for d in directories if d not in EXCLUDED_DIRS]
        for name in names:
            path = os.path.join(base, name)
            if not is_text(path):
                continue
            with io.open(path, encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        lines.add(stripped)
    return lines


def verify_evidence(payload, lines):
    """The share of evidence lines that are actually in the tree.

    A judge that never opened the code returns plausible scores and invented
    quotes, which no schema can catch. Matching each quote against the bundle
    is what tells one from the other, and the share is reported beside every
    score it supports.
    """
    present, absent_lines = 0, []
    rubric = payload.get("rubric", {})
    for name in DIMENSIONS:
        entry = rubric.get(name) or {}
        quote = (entry.get("evidence") or "").strip()
        if quote and any(quote in line or line in quote for line in lines):
            present += 1
        else:
            absent_lines.append([name, quote[:80]])
    return {"share": round(present / len(DIMENSIONS), 3),
            "not_found": absent_lines}


class JudgeError(Exception):
    """The judge cannot be launched as the design requires."""


def judge_executable(cli=DEFAULT_CLI):
    """The judge CLI's absolute path.

    A bare name in an argv list is not launchable on Windows, where the
    command is a `.CMD` shim and `CreateProcess` resolves no extension.
    """
    found = shutil.which(cli)
    if found is None:
        raise JudgeError("the `%s` CLI is not on PATH, so no trial can be "
                         "judged" % cli)
    return found


def codex_version(executable):
    """The judge CLI's version, which goes in the report.

    Launched before any bundle is built, the dry run included, so a CLI that
    cannot start refuses the run rather than failing every trial after it.
    """
    outcome = score.run([executable, "--version"], timeout=120)
    version = (outcome["stdout"] or "").strip()
    if outcome["failed"] or outcome["status"] != 0 or not version:
        raise JudgeError("`%s --version` did not report a version: %s"
                         % (executable, (outcome["failed"] or outcome["stderr"]
                                         or "no output")[:300]))
    return version


def judge_bundle(bundle, options, schema_path):
    """Run the judge over one bundle and return its answer.

    Read-only and ephemeral: the judge inspects a tree and writes nothing, and
    no session file carries one trial's reading into the next.
    """
    last = os.path.join(os.path.dirname(bundle),
                        os.path.basename(bundle) + "-message.json")

    if options.cli == "claude":
        return judge_through_claude(bundle, options, schema_path)

    # The prompt goes on standard input, named by `-`, never as an argument:
    # the Windows shim runs through `cmd.exe`, which ends a command at a
    # newline and expands a `%NAME%` pair inside an argument.
    argv = [options.executable, "exec",
            "--model", options.model,
            "-c", 'model_reasoning_effort="%s"' % options.effort,
            "--sandbox", "read-only",
            "--ephemeral",
            "--skip-git-repo-check",
            "-C", bundle,
            "--output-schema", schema_path,
            "--output-last-message", last,
            "-"]
    if options.dry_run:
        return {"argv": argv, "dry_run": True}
    outcome = score.run(argv, cwd=bundle, timeout=options.timeout,
                        stdin=PROMPT)
    if not os.path.exists(last):
        return {"argv": argv, "error": "the judge wrote no final message: %s"
                % cli_said(outcome)}
    with io.open(last, encoding="utf-8") as handle:
        text = handle.read().strip()
    try:
        payload = json.loads(text)
    except ValueError:

        # The CLI creates the file before it calls the model, so a refusal
        # leaves it empty and states its cause only in what the CLI printed.
        return {"argv": argv, "error": "the final message was %s; the CLI "
                "said: %s" % ("not JSON: %s" % text[:400] if text else "empty",
                              cli_said(outcome))}
    return {"argv": argv, "payload": payload}


def cli_said(outcome):
    """The last of what the judge CLI printed, where a failure names its
    cause."""
    return (outcome["stderr"] or outcome["stdout"] or "").strip()[-400:]


def judge_through_claude(bundle, options, schema_path):
    """Run the judge through the `claude` CLI, the rounds' judge.

    A reading is recorded under its own CLI and model and is never meaned
    with another judge's -- a different judge is a different instrument, not
    another sample of the same one.

    There is no schema flag here as there is on `codex`, so the shape is asked
    for in the prompt and enforced afterwards by `validate`, which every answer
    passes through whichever backend produced it.
    """

    # Read-only by tool list rather than by plan mode: plan mode answers with
    # a written plan and a summary, so the rubric never reaches standard
    # output. These three tools read and nothing writes.
    argv = [options.executable, "--print",
            "--model", options.model,
            "--effort", options.effort,
            "--allowed-tools", "Read", "Glob", "Grep",
            "--add-dir", bundle]
    if options.dry_run:
        return {"argv": argv, "dry_run": True}

    # The contract leads and closes. This backend has no schema flag, and a
    # CLI built for conversation answers a review prompt with a review unless
    # the shape is the first thing it reads and the last.
    with io.open(schema_path, encoding="utf-8") as handle:
        shape = handle.read()
    prompt = ("Your entire reply must be one JSON object and nothing else: no "
              "prose before or after it, no code fence, no summary. It must "
              "match this schema exactly:\n\n%s\n\n%s\n\nThe submission is the "
              "tree at %s. Read it, then reply with the JSON object alone."
              % (shape, PROMPT, bundle))

    # On standard input, as the other backend does: the schema carries the
    # prompt past the command-line length this platform allows.
    outcome = score.run(argv, cwd=bundle, timeout=options.timeout,
                        stdin=prompt)
    text = (outcome["stdout"] or "").strip()
    if not text:
        return {"argv": argv, "error": "the judge wrote nothing: %s"
                % (outcome["stderr"] or "")[-400:]}

    # A fenced block is the one shape the prompt asks against that still
    # arrives, so it is unwrapped rather than failed.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    opened, closed = text.find("{"), text.rfind("}")
    if opened < 0 or closed < opened:
        return {"argv": argv, "error": "the answer carried no JSON object: %s"
                % text[:400]}
    try:
        payload = json.loads(text[opened:closed + 1])
    except ValueError:
        return {"argv": argv, "error": "the answer was not JSON: %s"
                % text[opened:opened + 400]}
    return {"argv": argv, "payload": payload}


def validate(payload):
    """Every dimension present, in range, with a non-empty quote."""
    problems = []
    rubric = payload.get("rubric")
    if not isinstance(rubric, dict):
        return ["the answer carries no rubric object"]
    for name in DIMENSIONS:
        entry = rubric.get(name)
        if not isinstance(entry, dict):
            problems.append("%s is missing" % name)
            continue
        value = entry.get("score")
        if not isinstance(value, int) or not 1 <= value <= 5:
            problems.append("%s scored %r, which is not 1-5" % (name, value))
        if not (entry.get("evidence") or "").strip():
            problems.append("%s quotes nothing" % name)
    if not isinstance(payload.get("patterns"), list):
        problems.append("the answer carries no pattern census")
    return problems


def refusal(stripped):
    """Why a built bundle may not be judged, or None where it may."""

    # A bundle that still names its condition is not judged at all. A score
    # taken from a tree that says which arm it is cannot be un-taken, and the
    # design's blinding would read as held.
    if stripped["leaks"]:
        return "the bundle still names its condition: %s" % stripped["leaks"][:5]

    # Nor is one with no specification a round ran: judged against another,
    # the tree would be scored on work it was never asked for.
    if not stripped["spec"]:
        return ("the tree carries no specification a round ran, so there is "
                "nothing to judge it against")
    return None


def trees(root):
    """Every scored trial's extracted tree, by canonical trial name.

    A tree round 1 scored sits under its letter name, `B1`, and is judged
    under its word, `full-1`.
    """
    found = {}
    scoring = os.path.join(score.scoring_area(root), "scoring")
    for path in sorted(glob.glob(os.path.join(scoring, "*", "tree", "*"))):
        if os.path.isdir(path):
            found[canonical(os.path.basename(path))] = path
    return found


def judged(judging):
    """Every trial's completed judgings under `judging`, by canonical name.

    A trial may hold several: the rubric's readability row is not reproducible
    between calls on one unchanged tree, so a round judges each trial more than
    once and the report reads the mean. The labels come back in file order.
    """
    found = {}
    for file in sorted(glob.glob(os.path.join(judging, "T*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            record = json.load(handle)
        if record.get("outcome") != "judged":
            continue
        try:
            found.setdefault(canonical(record.get("trial") or ""), []).append(
                record.get("blind_id"))
        except TrialError:
            continue
    return found


def highest_label(judging):
    """The highest blind label number in use under `judging`: every judging
    file's, whatever its outcome, and every one the map names."""
    numbers = [0]
    for file in glob.glob(os.path.join(judging, "T*.json")):
        match = re.match(r"T(\d+)\.json$", os.path.basename(file))
        if match:
            numbers.append(int(match.group(1)))
    path = os.path.join(judging, "map.json")
    if os.path.isfile(path):
        with io.open(path, encoding="utf-8") as handle:
            for label in json.load(handle).get("blind", {}).values():
                match = re.match(r"T(\d+)$", str(label))
                if match:
                    numbers.append(int(match.group(1)))
    return max(numbers)


def blind_labels(order, after):
    """A blind label per trial in `order`, numbered from `after` + 1, so a
    root holding an earlier round's judgings never reuses one of theirs."""
    return {name: "T%d" % (after + index + 1)
            for index, name in enumerate(order)}


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    available = trees(options.root)
    if not available:
        print("no extracted trial trees under %s; score.py writes them"
              % score.scoring_area(options.root))
        return 2

    try:
        wanted = (sorted(canonical(name) for name in options.trial)
                  if options.trial else sorted(available))
    except TrialError as error:
        print("refused: %s" % error)
        return 2
    missing = [name for name in wanted if name not in available]
    if missing:
        print("no tree for %s" % ", ".join(missing))
        return 2

    # A second run against the area takes the same next label as a live one,
    # and clears the bundle that run's judge is reading.
    try:
        claim = claim_area(score.scoring_area(options.root), SCRIPT)
    except LiveRunError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "no trial judged")
        return 2
    try:
        return judge_trials(options, available, wanted)
    finally:
        release_area(claim)


def judge_trials(options, available, wanted):
    """Judge each wanted trial up to `--repeat` times; return the exit code."""

    # A trial is judged up to `--repeat` times and no further. The rounds
    # before this one judged once, and a single call is not reproducible: six
    # calls on one unchanged tree returned readability 4, 4, 4, 3, 4, 4. The
    # mean of several is what the report reads, so what is owed here is the
    # shortfall, which also makes an interrupted run resumable.
    judging = os.path.join(score.scoring_area(options.root), "judge")
    done = judged(judging)
    if options.repeat < 1:
        print("refused: --repeat is a count of judgings per trial, at least 1")
        return 2
    owed = {}
    for name in wanted:
        held = len(done.get(name, ()))
        short = options.repeat if options.rejudge else options.repeat - held
        if short <= 0:
            print("%s  already judged %d time(s) as %s; --repeat higher, or "
                  "--rejudge, to judge it again"
                  % (name, held, ", ".join(done[name])))
            continue
        owed[name] = short
    if not owed:
        lib.print_verdict(True, "0 judged, 0 failed, %d already judged"
                          % len(done))
        return 0
    wanted = [name for name in wanted if name in owed]

    try:
        options.executable = judge_executable(options.cli)
        version = (codex_version(options.executable)
                   if options.cli == "codex" else options.cli)
    except JudgeError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "no trial judged")
        return 2

    bundles = os.path.join(judging, "bundles")
    os.makedirs(bundles, exist_ok=True)

    # Shuffled with a recorded seed, so the order is reproducible and is not
    # the arm order. The map is written for the report and never passed to the
    # judge. Labels continue past any an earlier round left in this area.
    #
    # A trial owed several judgings is entered once per judging and the whole
    # list is shuffled together, so its repeats are spread through the run
    # rather than made back to back. Each repeat is a separate blind label: it
    # is a separate reading of the same tree, and the report means them.
    shuffler = random.Random(options.seed)
    order = [name for name in wanted for _ in range(owed[name])]
    shuffler.shuffle(order)
    labels = blind_labels(range(len(order)), highest_label(judging))
    repeats = {}

    schema_path = os.path.join(judging, "rubric-schema.json")
    with io.open(schema_path, "w", encoding="utf-8") as handle:
        json.dump(schema(), handle, indent=2)

    results, failures = [], 0
    for position, name in enumerate(order):
        label = labels[position]
        repeats.setdefault(name, []).append(label)
        print("%s  as %s" % (name, label))
        bundle = os.path.join(bundles, label)
        stripped = build_bundle(available[name], bundle)
        refused = refusal(stripped)
        if refused:
            answer = {"argv": None, "error": refused}
        else:
            answer = judge_bundle(bundle, options, schema_path)

        record = {"trial": name, "blind_id": label, "model": options.model,
                  "repeat": len(repeats[name]),
                  "effort": options.effort, "cli": version,
                  "seed": options.seed, "bundle": stripped,
                  "judged_at": datetime.datetime.now().isoformat(
                      timespec="seconds"),
                  "invocation": answer.get("argv")}
        if answer.get("dry_run"):
            record["outcome"] = "dry-run"
        elif "error" in answer:
            record["outcome"] = "failed"
            record["error"] = answer["error"]
            failures += 1
            print("  failed: %s" % answer["error"][:160])
        else:
            payload = answer["payload"]
            problems = validate(payload)
            record["answer"] = payload
            record["problems"] = problems
            record["evidence"] = verify_evidence(payload, bundle_text(bundle))
            record["outcome"] = "judged" if not problems else "invalid"
            if problems:
                failures += 1
            scores = {k: payload["rubric"][k]["score"] for k in PRIMARY
                      if k in payload.get("rubric", {})}
            print("  %s  primary %s  evidence found %.0f%%"
                  % (record["outcome"], scores,
                     100 * record["evidence"]["share"]))

        target = os.path.join(judging, "%s.json" % label)
        with io.open(target, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
        results.append(record)

    # The unblinding map, written last and kept out of the bundles directory
    # the judge was pointed at. An earlier round's entries stay in it.
    path = os.path.join(judging, "map.json")
    mapping = {"seed": options.seed, "blind": {}, "repeats": {}}
    if os.path.isfile(path):
        with io.open(path, encoding="utf-8") as handle:
            existing = json.load(handle)
        mapping["blind"] = existing.get("blind", {})
        mapping["repeats"] = existing.get("repeats", {})

    # `blind` keeps its one label per trial, which is what every earlier round
    # and `reuse.py` read. `repeats` carries the rest, so a reader wanting
    # every reading of a trial has them without the old shape changing.
    for name, labels_used in repeats.items():
        mapping["blind"].setdefault(name, labels_used[0])
        mapping["repeats"][name] = (mapping["repeats"].get(name, [])
                                    + labels_used)
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(mapping, handle, indent=2, sort_keys=True)

    lib.print_verdict(failures == 0,
                      "%d judged, %d failed" % (len(results) - failures,
                                                failures))
    return 1 if failures else 0


def plant(root, files):
    """Write each relative path's text under root."""
    for relative, text in files.items():
        path = os.path.join(root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)


def bundle_checks(scratch):
    """Prove a bundle leaves scoring's output out and a trial's path is a leak.

    The planted tree is shaped like one scoring leaves behind: the trial's code
    beside tool caches that hold absolute paths through the scoring area.
    """
    tree = os.path.join(scratch, "scoring", "full-2", "tree", "full-2")
    scored = "/".join((scratch.replace(os.sep, "/"), "scoring", "full-2", "tree",
                       "full-2", "src"))
    code = os.path.join("src", "app.py")

    # The trial's name outside a path, where an implementation may use it,
    # is not a leak.
    plant(tree, {code: 'CELL = "full-2"\n', "CLAUDE.md": "# rules\n"})
    output = {
        ".coverage": "SQLite format 3 %s" % scored,
        "complexipy.json": json.dumps([{"path": scored}]),
        os.path.join(".complexipy_cache", "v", "cache", "functions"):
            json.dumps(scored),
        os.path.join(".grimp_cache", "data.json"): scored,
        os.path.join("src", "tariff.egg-info", "SOURCES.txt"): scored,
    }
    plant(tree, output)

    bundle = os.path.join(scratch, "judge", "bundles", "T1")
    stripped = build_bundle(tree, bundle)
    copied = {os.path.relpath(os.path.join(base, name), bundle)
              for base, _, names in os.walk(bundle) for name in names}
    checks = [
        ("the trial's code reaches the bundle", code in copied),
        ("scoring's output stays out of the bundle",
         not any(relative in copied for relative in output)),
        ("a bundle holding neither has no leak", stripped["leaks"] == []),
    ]

    # A path naming the trial is a leak in whichever file the bundle keeps, in
    # either separator and escaped inside a JSON string.
    leaks = (
        ("a path naming the trial is a leak",
         os.path.join("docs", "run.txt"), "ran from %s\n" % scored),
        ("an escaped path naming the trial is a leak",
         os.path.join("docs", "run.json"),
         json.dumps({"cwd": scored.replace("/", "\\")})),
    )
    for label, relative, text in leaks:
        landed = os.path.join(bundle, relative)
        before = os.path.exists(landed)
        plant(tree, {relative: text})
        found = build_bundle(tree, bundle)["leaks"]
        os.remove(os.path.join(tree, relative))

        # The plant landed: the bundle lacked the file and now holds it.
        checks.append((label, not before and os.path.exists(landed)
                       and [relative, "full-2", "as a path segment"] in found))

    # The scan reads the directories the copy leaves out, because the judge
    # reads whatever the bundle holds.
    hidden = os.path.join(".git", "config")
    plant(bundle, {hidden: "worktree = %s\n" % scored})
    checks.append(("a leak in a directory the copy skips is found",
                   [hidden, "full-2", "as a path segment"]
                   in surviving_markers(bundle, "full-2")))
    return checks


def spec_checks(scratch):
    """Prove a tree is judged against the specification it carries.

    Each planted tree carries the current specification, an earlier one, an
    edited one or none, and the bundle is read back for the bytes it holds.
    """
    current = spec_text(SPEC)
    earlier = b"# tariff, as an earlier round specified it\n"
    planted = {"current": current,
               "crlf": current.replace(b"\n", b"\r\n"),
               "earlier": earlier,
               "edited": current + b"\nAlso build a blog.\n",
               "missing": None}
    saved = dict(SPECS)
    SPECS[hashlib.sha256(earlier).hexdigest()] = "an earlier round"
    built = {}
    try:
        for label, text in planted.items():
            tree = os.path.join(scratch, "specs", label, label)
            plant(tree, {os.path.join("src", "app.py"): "X = 1\n"})
            if text is not None:
                with io.open(os.path.join(tree, "SPEC.md"), "wb") as handle:
                    handle.write(text)
            bundle = os.path.join(scratch, "specs", label, "bundle")
            stripped = build_bundle(tree, bundle)
            held_path, held = os.path.join(bundle, "SPEC.md"), None
            if os.path.isfile(held_path):
                with io.open(held_path, "rb") as handle:
                    held = handle.read()
            built[label] = (stripped, held)
    finally:
        SPECS.clear()
        SPECS.update(saved)

    def judged_against(label, text):
        stripped, held = built[label]
        return (stripped["spec"] is not None and refusal(stripped) is None
                and held == text)

    def refused(label):
        stripped, _ = built[label]
        return stripped["spec"] is None and "specification" in (
            refusal(stripped) or "")

    return [
        ("a tree carrying the current spec is judged against it",
         judged_against("current", current)),
        ("a CRLF copy of it is recognised and bundled as LF",
         judged_against("crlf", current)),

        # The property the check exists for: an earlier round's tree keeps
        # its own specification rather than taking the current one.
        ("an earlier round's tree is judged against its own spec",
         judged_against("earlier", earlier)
         and built["earlier"][0]["spec"]["round"] == "an earlier round"),
        ("a tree whose spec was edited is refused", refused("edited")),
        ("a tree carrying no spec is refused", refused("missing")),
    ]


# A stand-in for the judge CLI: it reports a version, and otherwise records
# the arguments and standard input it received where the real CLI writes its
# final message. Told to refuse, it fails the way the real one does when the
# model is refused: the message file created and left empty, the cause on
# standard error.
REFUSAL = "ERROR: the model requires a newer version of Codex"
FAKE_CLI = """\
import json
import os
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli self-test")
    raise SystemExit(0)
last = args[args.index("--output-last-message") + 1]
if os.environ.get("FAKE_CODEX_REFUSES"):
    open(last, "w").close()
    sys.stderr.write(os.environ["FAKE_CODEX_REFUSES"] + "\\n")
    raise SystemExit(1)
with open(last, "w", encoding="utf-8") as handle:
    json.dump({"argv": args,
               "stdin": sys.stdin.buffer.read().decode("utf-8")}, handle)
"""


def launch_checks(scratch):
    """Prove the judge launches through a shim, with the prompt on stdin.

    The stand-in is installed the way npm installs the real CLI: a `.cmd`
    shim on Windows, so the launch crosses `cmd.exe` as the real one does.
    """
    empty = os.path.join(scratch, "empty")
    bin_dir = os.path.join(scratch, "bin")
    broken_dir = os.path.join(scratch, "broken")
    fake = os.path.join(scratch, "fake_codex.py")
    plant(scratch, {os.path.join("empty", ".keep"): "",
                    "fake_codex.py": FAKE_CLI})
    if os.name == "nt":
        plant(bin_dir, {"codex.cmd": '@echo off\r\n"%s" "%s" %%*\r\n'
                        % (sys.executable, fake)})
        plant(broken_dir, {"codex.cmd": "@echo off\r\nexit /b 1\r\n"})
    else:
        plant(bin_dir, {"codex": '#!/bin/sh\nexec "%s" "%s" "$@"\n'
                        % (sys.executable, fake)})
        plant(broken_dir, {"codex": "#!/bin/sh\nexit 1\n"})
        for directory in (bin_dir, broken_dir):
            os.chmod(os.path.join(directory, "codex"), 0o755)

    def refuses(call):
        try:
            call()
        except JudgeError:
            return True
        return False

    saved = os.environ.get("PATH", "")
    checks = []
    try:
        os.environ["PATH"] = empty
        checks.append(("a CLI missing from PATH refuses the run",
                       refuses(judge_executable)))

        os.environ["PATH"] = broken_dir
        checks.append(("a CLI that reports no version refuses the run",
                       refuses(lambda: codex_version(judge_executable("codex")))))

        os.environ["PATH"] = bin_dir
        executable = judge_executable("codex")
        checks.append(("the CLI resolves to an absolute path",
                       os.path.isabs(executable)
                       and os.path.isfile(executable)))
        checks.append(("the resolved CLI reports its version",
                       codex_version(executable) == "codex-cli self-test"))

        bundle = os.path.join(scratch, "launch", "T1")
        plant(bundle, {"SPEC.md": "# spec\n"})
        options = argparse.Namespace(executable=executable, model="m",
                                     effort="high", dry_run=False,
                                     cli="codex", timeout=120)
        answer = judge_bundle(bundle, options, os.path.join(scratch, "s.json"))

        # The refusal leaves the message file empty, so the failure is read
        # from the branch that finds a file and no JSON in it.
        os.environ["FAKE_CODEX_REFUSES"] = REFUSAL
        refused = judge_bundle(bundle, options,
                               os.path.join(scratch, "s.json"))
    finally:
        os.environ["PATH"] = saved
        os.environ.pop("FAKE_CODEX_REFUSES", None)

    received = answer.get("payload") or {}
    stdin = (received.get("stdin") or "").replace("\r\n", "\n")
    checks.append(("the prompt reaches the CLI whole, on stdin",
                   stdin == PROMPT and PROMPT not in answer["argv"]))
    checks.append(("every argument reaches the CLI intact",
                   received.get("argv") == answer["argv"][1:]))
    message = bundle + "-message.json"
    checks.append(("an empty final message carries the CLI's cause",
                   os.path.isfile(message) and os.path.getsize(message) == 0
                   and "was empty" in refused.get("error", "")
                   and REFUSAL in refused["error"]))
    return checks


def label_checks(scratch):
    """Blind labels continue past an earlier round's, and a judged trial is
    known by its canonical name."""
    judging = os.path.join(scratch, "labels", "judge")
    os.makedirs(judging)
    plant(judging, {
        "T3.json": json.dumps({"trial": "B1", "blind_id": "T3",
                               "outcome": "judged"}),
        "T10.json": json.dumps({"trial": "C2", "blind_id": "T10",
                                "outcome": "failed"}),
        "map.json": json.dumps({"seed": 1, "blind": {"A1": "T12"}}),
    })
    return [
        ("a judged trial is known under its word, a failed one is not",
         judged(judging) == {"full-1": ["T3"]}),
        ("the highest label counts every file and the map",
         highest_label(judging) == 12),
        ("new labels continue past it",
         blind_labels(["short-1", "none-1"], 12)
         == {"short-1": "T13", "none-1": "T14"}),

        # Every repeat of a trial is its own reading and its own label, so a
        # trial judged three times comes back with three, not one counted
        # thrice.
        ("a trial's repeats each carry their own label",
         list(blind_labels(range(3), 12).values())
         == ["T13", "T14", "T15"]),
    ]


def backend_checks(scratch):
    """The claude backend reads and writes nothing, and answers on stdout.

    Both failures below happened on the way to a working backend: plan mode
    wrote a plan file and answered with a summary, so no rubric reached
    standard output; and a prompt carrying the schema, passed as an argument,
    ran past the command-line length the platform allows.
    """
    bundle = os.path.join(scratch, "backend", "T1")
    plant(bundle, {"SPEC.md": "# spec\n"})
    options = argparse.Namespace(executable="claude", model="m", cli="claude",
                                 effort="high", dry_run=True, timeout=120)
    argv = judge_bundle(bundle, options,
                        os.path.join(scratch, "s.json"))["argv"]
    tools = argv[argv.index("--allowed-tools") + 1:] if (
        "--allowed-tools" in argv) else []
    return [
        ("the claude backend is not in plan mode",
         "plan" not in argv),
        ("it may read and nothing else",
         tools[:3] == ["Read", "Glob", "Grep"]
         and not any(tool in argv for tool in ("Write", "Edit", "Bash"))),
        ("its prompt goes on stdin, not the command line",
         not any("SPEC.md" in arg or "Score each" in arg for arg in argv)),

        # The effort is recorded with every reading, so it has to be the one
        # the CLI ran at: without the flag the CLI uses its own default.
        ("the recorded effort is the one passed",
         argv[argv.index("--effort") + 1:][:1] == ["high"]
         if "--effort" in argv else False),
    ]


def claim_checks(scratch):
    """A judge run refuses while another holds the area, and builds nothing.

    The planted tree gets the run past every earlier refusal, so the one it
    meets is the claim's. A dry run, so that a claim that stopped refusing
    builds a bundle and calls no model.
    """
    root = os.path.join(scratch, "claimed")
    area = score.scoring_area(root)
    os.makedirs(os.path.join(area, "scoring", "none-1", "tree", "none-1"))
    label, refused = claim_refusal_check(SCRIPT, main, root, "--dry-run")
    return [(label, refused
             and not os.path.exists(os.path.join(area, "judge")))]


def self_test():
    """Prove a bundle is blind and carries its tree's own specification,
    labels continue, the judge launches, and a live run refuses a second."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-judge-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    checks = bundle_checks(scratch)
    checks.extend(spec_checks(scratch))
    checks.extend(label_checks(scratch))
    checks.extend(launch_checks(scratch))
    checks.extend(backend_checks(scratch))
    checks.extend(claim_checks(scratch))
    for label, ok in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED"))
    shutil.rmtree(scratch, ignore_errors=True)
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Judge frozen efficacy trials, blind.")
    parser.add_argument("--root",
                        help="the harness's run root; required for "
                             "everything but --self-test")
    parser.add_argument("--self-test", action="store_true",
                        help="prove a bundle is blind and the judge launches; "
                             "judge nothing")
    parser.add_argument("--trial", action="append", default=[],
                        help="judge only this trial, as none-1; repeatable")
    parser.add_argument("--cli", default=DEFAULT_CLI,
                        choices=("codex", "claude"),
                        help="which CLI drives the judge. `claude` is the "
                             "rounds' judge; `codex` is the other vendor's, "
                             "reading a sample as a cross-check, and its "
                             "readings are never meaned with the other's.")
    parser.add_argument("--repeat", type=int, default=1,
                        help="judgings per trial; the report means them. A "
                             "trial already holding this many is left alone, "
                             "so an interrupted run resumes.")
    parser.add_argument("--rejudge", action="store_true",
                        help="judge a trial already judged; by default such "
                             "a trial is skipped")
    parser.add_argument("--model",
                        help="judge model id, recorded in the report; "
                             "defaults to the CLI's own judge model")
    parser.add_argument("--effort", default=JUDGE_EFFORT,
                        help="reasoning effort, set explicitly because the "
                             "local default is low")
    parser.add_argument("--seed", type=int, default=20260912,
                        help="shuffle seed, recorded in the report")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--dry-run", action="store_true",
                        help="build the bundles and print the command; call "
                             "no model")
    options = parser.parse_args(argv)
    options.model = options.model or JUDGE_MODELS[options.cli]
    return options


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
