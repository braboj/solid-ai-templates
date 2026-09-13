"""Judge one frozen efficacy trial, blind, through a different vendor.

The design's section 5 fixes what this asks for: a 1-5 rubric with a quoted
evidence line per score, a pattern census that says what each pattern removes
or opens, and the three primary dimensions the report leads with. Section 7
fixes the controls: a different vendor from the generator, blind to arm,
order shuffled, condition markers stripped, model id and reasoning effort
recorded.

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

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "SPEC.md")

# A different vendor from the generator, which is the stronger form of the
# design's control: a different family of the same vendor shares a training
# pipeline with the thing it grades.
JUDGE_MODEL = "gpt-6-astra"

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
)

# What the report leads with, owner-declared in the design.
PRIMARY = ("design", "readability", "maintainability")

# Never shown to the judge. A context file names the condition, and so does a
# README that thanks one: both are stripped from the bundle, and what was
# stripped is recorded.
EXCLUDED_NAMES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules",
                  ".windsurfrules", "copilot-instructions.md")
EXCLUDED_DIRS = (".git", ".cursor", ".github", "venv", ".venv", "__pycache__",
                 ".score-pages", "node_modules", ".pytest_cache", ".ruff_cache",
                 "build", "dist", ".mypy_cache")

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
           "arm A", "arm B", "arm C")

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
        directories[:] = [d for d in directories if d not in EXCLUDED_DIRS]
        for name in names:
            source = os.path.join(base, name)
            relative = os.path.relpath(source, tree)
            if name in EXCLUDED_NAMES:
                removed.append(relative)
                continue
            if name.startswith(".score-") or name.endswith(".sqlite"):
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

    # The judge needs the task to score against it, and the specification is
    # identical for every arm, so it carries no condition.
    shutil.copyfile(SPEC, os.path.join(target, "SPEC.md"))
    return {"removed": removed, "markers_masked": masked,
            "leaks": surviving_markers(target), "digest": digest(target)}


def surviving_markers(bundle):
    """Markers still readable in the built bundle.

    The masking pass is checked rather than trusted: a marker in a file
    extension the copy treated as binary, or in a name rather than in text,
    would leave the arm legible and every later control would read as blind.
    """
    found = []
    for base, directories, names in os.walk(bundle):
        directories[:] = [d for d in directories if d not in EXCLUDED_DIRS]
        for name in names:
            path = os.path.join(base, name)
            relative = os.path.relpath(path, bundle)
            for marker in MARKERS:
                if marker.lower() in name.lower():
                    found.append([relative, marker, "in the file name"])

            # Every file, decoded loosely, not only the suffixes the masker
            # recognises. A scan that skipped what the masker skipped would
            # share its blind spot exactly, and a marker in an extension
            # neither of them knows would read as a blind bundle.
            with io.open(path, "rb") as handle:
                text = handle.read().decode("utf-8", "replace").lower()
            for marker in MARKERS:
                if marker.lower() in text:
                    found.append([relative, marker, "in the bytes"])
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


def codex_version():
    """The judge CLI's version, which goes in the report."""
    outcome = score.run(["codex", "--version"], timeout=120)
    return (outcome["stdout"] or outcome["stderr"]).strip() or "unknown"


def judge_bundle(bundle, options, schema_path):
    """Run the judge over one bundle and return its answer.

    Read-only and ephemeral: the judge inspects a tree and writes nothing, and
    no session file carries one trial's reading into the next.
    """
    last = os.path.join(os.path.dirname(bundle),
                        os.path.basename(bundle) + "-message.json")
    argv = ["codex", "exec",
            "--model", options.model,
            "-c", 'model_reasoning_effort="%s"' % options.effort,
            "--sandbox", "read-only",
            "--ephemeral",
            "--skip-git-repo-check",
            "-C", bundle,
            "--output-schema", schema_path,
            "--output-last-message", last,
            PROMPT]
    if options.dry_run:
        return {"argv": argv, "dry_run": True}
    outcome = score.run(argv, cwd=bundle, timeout=options.timeout)
    if not os.path.exists(last):
        return {"argv": argv, "error": "the judge wrote no final message: %s"
                % (outcome["stderr"] or outcome["stdout"])[-400:]}
    with io.open(last, encoding="utf-8") as handle:
        text = handle.read().strip()
    try:
        payload = json.loads(text)
    except ValueError:
        return {"argv": argv, "error": "the final message was not JSON: %s"
                % text[:400]}
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


def trees(root):
    """Every scored trial's extracted tree, by trial name."""
    found = {}
    for path in sorted(glob.glob(os.path.join(root, "scoring", "*",
                                             "tree", "*"))):
        if os.path.isdir(path):
            found[os.path.basename(path)] = path
    return found


def main(argv):
    options = parse_args(argv)
    available = trees(options.root)
    if not available:
        print("no extracted trial trees under %s; score.py writes them"
              % options.root)
        return 2

    wanted = sorted(options.trial) if options.trial else sorted(available)
    missing = [name for name in wanted if name not in available]
    if missing:
        print("no tree for %s" % ", ".join(missing))
        return 2

    judging = os.path.join(options.root, "judge")
    bundles = os.path.join(judging, "bundles")
    os.makedirs(bundles, exist_ok=True)

    # Shuffled with a recorded seed, so the order is reproducible and is not
    # the arm order. The map is written for the report and never passed to the
    # judge.
    shuffler = random.Random(options.seed)
    order = list(wanted)
    shuffler.shuffle(order)
    blind = {name: "T%d" % (index + 1) for index, name in enumerate(order)}

    schema_path = os.path.join(judging, "rubric-schema.json")
    with io.open(schema_path, "w", encoding="utf-8") as handle:
        json.dump(schema(), handle, indent=2)

    version = codex_version()
    results, failures = [], 0
    for name in order:
        label = blind[name]
        print("%s  as %s" % (name, label))
        bundle = os.path.join(bundles, label)
        stripped = build_bundle(available[name], bundle)

        # A bundle that still names its condition is not judged at all. A
        # score taken from a tree that says which arm it is cannot be
        # un-taken, and the design's blinding would read as held.
        if stripped["leaks"]:
            answer = {"argv": None, "error": "the bundle still names its "
                      "condition: %s" % stripped["leaks"][:5]}
        else:
            answer = judge_bundle(bundle, options, schema_path)

        record = {"trial": name, "blind_id": label, "model": options.model,
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
    # the judge was pointed at.
    with io.open(os.path.join(judging, "map.json"), "w",
                 encoding="utf-8") as handle:
        json.dump({"seed": options.seed, "blind": blind}, handle, indent=2,
                  sort_keys=True)

    if options.holdout:
        write_holdout(judging, blind, results)

    lib.print_verdict(failures == 0,
                      "%d judged, %d failed" % (len(results) - failures,
                                                failures))
    return 1 if failures else 0


def write_holdout(judging, blind, results):
    """A blind sheet for the owner's three scores, one per arm.

    The holdout validates the judge rather than producing a metric, so it
    names blind ids and the three primary dimensions and nothing else. No
    verdict waits on it; a run whose sheet is unscored reports the subjective
    row as unvalidated.
    """
    by_arm = {}
    for record in results:
        arm = record["trial"][0]
        by_arm.setdefault(arm, record)
    lines = ["# Human holdout — three outputs, three dimensions", "",
             "Score each 1-5 after reading the bundle. The mapping from a",
             "blind id to an arm is in `map.json`, which is not needed to",
             "score and should be read afterwards.", ""]
    lines.append("| Bundle | design | readability | maintainability |")
    lines.append("|---|---|---|---|")
    for arm in sorted(by_arm):
        lines.append("| `bundles/%s` |  |  |  |" % by_arm[arm]["blind_id"])
    lines.extend(["", "Agreement is reported as the share of scores where the",
                  "judge lands on this number or within one point of it."])
    with io.open(os.path.join(judging, "holdout-sheet.md"), "w",
                 encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Judge frozen efficacy trials, blind.")
    parser.add_argument("--root", required=True, help="the harness's run root")
    parser.add_argument("--trial", action="append", default=[],
                        help="judge only this trial, as A1; repeatable")
    parser.add_argument("--model", default=JUDGE_MODEL,
                        help="judge model id, recorded in the report")
    parser.add_argument("--effort", default=JUDGE_EFFORT,
                        help="reasoning effort, set explicitly because the "
                             "local default is low")
    parser.add_argument("--seed", type=int, default=20260912,
                        help="shuffle seed, recorded in the report")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--holdout", action="store_true",
                        help="also write the owner's blind scoring sheet")
    parser.add_argument("--dry-run", action="store_true",
                        help="build the bundles and print the command; call "
                             "no model")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
