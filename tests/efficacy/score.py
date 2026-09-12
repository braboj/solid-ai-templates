"""Score one frozen efficacy trial with the deterministic backbone.

The design, the metric directions and the verdict rule live in
`docs/design/efficacy-benchmark.md`. This module owns the part of section 5
that needs no judgement: the clean install, the hidden acceptance suite, the
static battery, the scope count and the cost read off the trial record. The
structural design probes and the web-quality probes live in `probes.py`; the
model judge in `judge.py`; the contrasts and the report in `report.py`.

Two rules run through everything here.

A tool that errored, timed out, or scanned nothing records the metric as
missing and flags the trial. It never records zero: zero findings and
nothing scanned are the same number and opposite facts.

Source roots are discovered, never assumed. The arms choose their own
layout, and `src/` is one of the things a context file might introduce, so a
tool pointed at a hard-coded `src` reads an empty directory for a valid flat
layout and reports a clean trial.
"""

import argparse
import datetime
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
import probes  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS = os.path.join(HERE, "scoring-requirements.txt")
TOOLCONFIG = os.path.join(HERE, "toolconfig")
RUFF_CONFIG = os.path.join(TOOLCONFIG, "ruff.toml")
MYPY_CONFIG = os.path.join(TOOLCONFIG, "mypy.ini")

# The grader lives in its own repository, private for the reason the design
# gives: this repository is public, and a suite here is one search away from
# any later trial with web access.
HIDDEN_SUITE = "braboj/tariff-hidden-suite"

# The package every arm is asked to produce, fixed by the specification.
PACKAGE = "tariff"

# Files nobody asked for. The prompt asks for an application; a trial that
# also writes a decision record or a changelog spent budget on it, which is a
# metric the design reports rather than a fault it punishes.
UNASKED = ("CHANGELOG", "ADR", "DECISIONS", "PLAYBOOK", "ONBOARDING",
           "JOURNAL", "ROADMAP", "CONTRIBUTING")

TOOL_TIMEOUT = 900


class ScoreError(Exception):
    """A trial could not be scored as the design requires."""


def measured(value, **extra):
    """A metric that was taken."""
    record = {"value": value, "missing": None}
    record.update(extra)
    return record


def absent(reason, **extra):
    """A metric that was not taken, and why.

    Called wherever a tool errored, timed out or saw no files. The reason
    reaches the report, so a suspiciously clean arm can be told from an
    unmeasured one by reading rather than by rerunning.
    """
    record = {"value": None, "missing": reason}
    record.update(extra)
    return record


def run(argv, cwd=None, env=None, timeout=TOOL_TIMEOUT):
    """Run one command and return its outcome as data.

    Every invocation is recorded with its argv, so the report can state what
    produced a number. A command that does not exist or does not finish is an
    outcome, not an exception: the caller turns it into a missing metric.
    """
    record = {"argv": list(argv), "cwd": cwd}
    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        record.update({"status": None, "stdout": "", "stderr": "",
                       "failed": "timed out after %ds" % timeout})
        return record
    except OSError as error:
        record.update({"status": None, "stdout": "", "stderr": str(error),
                       "failed": "could not be launched: %s" % error})
        return record
    record.update({"status": proc.returncode, "stdout": proc.stdout,
                   "stderr": proc.stderr, "failed": None})
    return record


def run_module(venv, module, args, cwd=None, timeout=TOOL_TIMEOUT):
    """Run one tool as `python -m <module>` inside a trial's environment.

    An absent tool is reported the way a crash is, because the two must not
    diverge here: `python -m ruff` with no ruff installed exits non-zero with
    an empty stdout, and a probe that reads that stdout as its result records
    no findings for a tree nothing scanned.
    """
    outcome = run([python_in(venv), "-m", module] + list(args), cwd=cwd,
                  timeout=timeout)
    if outcome["failed"] is None and "No module named" in (
            outcome["stderr"] or ""):
        outcome["failed"] = ("is not installed in the trial environment, so "
                             "nothing was scanned")
    return outcome


def python_in(venv):
    """The interpreter inside a virtual environment, on either platform."""
    candidate = os.path.join(venv, "Scripts", "python.exe")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(venv, "bin", "python")


def script_in(venv, name):
    """A console script inside a virtual environment, or None.

    Some of the battery has no `-m` entry point, so the script is resolved
    rather than assumed. A missing one becomes a missing metric with the
    tool's name in it.
    """
    for candidate in (os.path.join(venv, "Scripts", name + ".exe"),
                      os.path.join(venv, "Scripts", name),
                      os.path.join(venv, "bin", name)):
        if os.path.exists(candidate):
            return candidate
    return None


def extract(tarball, into, name):
    """Unpack a frozen trial and return the workspace path.

    Scoring reads the tarball the harness wrote, never the directory the
    agent worked in: a later run in that directory cannot change what was
    graded.
    """
    if not os.path.exists(tarball):
        raise ScoreError("the frozen tarball %s does not exist" % tarball)
    target = os.path.join(into, name)
    if os.path.exists(target):
        shutil.rmtree(target)
    os.makedirs(into, exist_ok=True)
    with tarfile.open(tarball) as archive:
        archive.extractall(into, filter="data")
    if not os.path.isdir(target):
        raise ScoreError("%s did not contain a %s directory" % (tarball, name))
    return target


def create_venv(where):
    """A clean virtual environment for one trial."""
    if os.path.exists(where):
        shutil.rmtree(where)
    outcome = run([sys.executable, "-m", "venv", where], timeout=600)
    if outcome["failed"] or outcome["status"] != 0:
        raise ScoreError("could not create the virtual environment at %s: %s"
                         % (where, outcome["stderr"][:400]))
    return where


def pip(venv, *args, **kwargs):
    """Run pip inside a trial's environment."""
    timeout = kwargs.pop("timeout", 1800)
    return run([python_in(venv), "-m", "pip", "--disable-pip-version-check"]
               + list(args), timeout=timeout, **kwargs)


def install_trial(venv, workspace):
    """`pip install .` in a clean environment, which is a scored metric.

    An arm whose package does not install scores zero on the hidden suite
    for a reason the report can name, so the outcome is recorded rather than
    raised.
    """
    outcome = pip(venv, "install", ".", cwd=workspace)
    ok = outcome["failed"] is None and outcome["status"] == 0
    tail = (outcome["stdout"] + outcome["stderr"])[-2000:]
    return measured(ok, invocation=outcome["argv"], output_tail=tail)


def boot_check(venv, workspace):
    """Import the package, build the app, and serve `/` once.

    Three separate facts, because an arm can install and import and still
    have no application factory. The factory's name and signature are fixed
    by the specification, so this reaches only what every arm owes.
    """
    database = os.path.join(workspace, ".score-boot.sqlite")
    code = (
        "import json, sys\n"
        "result = {'import': False, 'factory': False, 'index_status': None}\n"
        "try:\n"
        "    import %s as package\n"
        "    result['import'] = True\n"
        "except Exception as error:\n"
        "    result['import_error'] = repr(error)[:300]\n"
        "    print(json.dumps(result)); sys.exit(0)\n"
        "try:\n"
        "    app = package.create_app(%r)\n"
        "    result['factory'] = True\n"
        "except Exception as error:\n"
        "    result['factory_error'] = repr(error)[:300]\n"
        "    print(json.dumps(result)); sys.exit(0)\n"
        "try:\n"
        "    client = app.test_client()\n"
        "    result['index_status'] = client.get('/').status_code\n"
        "except Exception as error:\n"
        "    result['serve_error'] = repr(error)[:300]\n"
        "print(json.dumps(result))\n" % (PACKAGE, database)
    )
    outcome = run([python_in(venv), "-c", code], cwd=workspace, timeout=300)
    try:
        payload = json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return absent("the boot probe produced no JSON: %s"
                      % (outcome["stderr"] or outcome["stdout"])[:300],
                      invocation=outcome["argv"])
    return measured(payload, invocation=outcome["argv"])


def importable_package_dir(venv, workspace):
    """Where the installed package lives, asked of the interpreter.

    This is the layout-independent half of source discovery: whatever the
    arm chose, the installed package knows its own directory.
    """
    code = ("import importlib, json, os\n"
            "module = importlib.import_module(%r)\n"
            "print(json.dumps(os.path.dirname(os.path.abspath("
            "module.__file__))))\n" % PACKAGE)
    outcome = run([python_in(venv), "-c", code], cwd=workspace, timeout=300)
    try:
        return json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def workspace_packages(workspace):
    """Every package directory in the workspace, at the top or under `src`.

    The installed copy is not the tree a reader reviews, and a trial can ship
    modules the package does not import. Both views are kept, and the report
    says which paths each tool saw.
    """
    found = []
    for parent in (workspace, os.path.join(workspace, "src")):
        if not os.path.isdir(parent):
            continue
        for entry in sorted(os.listdir(parent)):
            path = os.path.join(parent, entry)
            if not os.path.isdir(path) or entry.startswith("."):
                continue
            if entry in ("build", "dist", "__pycache__", "node_modules"):
                continue
            if os.path.exists(os.path.join(path, "__init__.py")):
                found.append(path)
    return found


def discover_roots(venv, workspace):
    """The paths every tool is pointed at, and how each was found."""
    roots, how = [], {}
    installed = importable_package_dir(venv, workspace)

    # The installed copy answers for the package, but it sits outside the
    # workspace and a tool pointed there would grade site-packages. It is
    # recorded for the report and used only to confirm the package name.
    if installed:
        how[installed] = "the installed package's own directory"

    for path in workspace_packages(workspace):
        roots.append(path)
        how[path] = "a package directory in the workspace"

    # A single-module trial is legal: no package directory, one .py file at
    # the top. Without this the battery would see nothing and report every
    # metric missing for a tree that is perfectly scannable.
    if not roots:
        modules = [os.path.join(workspace, name)
                   for name in sorted(os.listdir(workspace))
                   if name.endswith(".py")]
        for path in modules:
            roots.append(path)
            how[path] = "a top-level module, no package directory present"

    return {"roots": roots, "how": how, "installed": installed}


def count_source(paths):
    """Files and lines the tools were pointed at.

    Every table in the report carries this beside the finding count, which is
    what lets a reader tell a clean arm from an unscanned one.
    """
    files, lines = 0, 0
    for path in paths:
        if os.path.isfile(path):
            candidates = [path]
        else:
            candidates = [os.path.join(root, name)
                          for root, _, names in os.walk(path)
                          for name in names if name.endswith(".py")]
        for candidate in candidates:
            if "__pycache__" in candidate:
                continue
            files += 1
            try:
                with io.open(candidate, encoding="utf-8",
                             errors="replace") as handle:
                    lines += sum(1 for _ in handle)
            except OSError:
                continue
    return {"files": files, "lines": lines}


def test_paths(workspace):
    """Where the trial's own tests live, if anywhere."""
    found = []
    for name in ("tests", "test"):
        path = os.path.join(workspace, name)
        if os.path.isdir(path):
            found.append(path)
    if not found:
        found = [os.path.join(workspace, name)
                 for name in sorted(os.listdir(workspace))
                 if name.startswith("test_") and name.endswith(".py")]
    return found


def clone_suite(where):
    """Clone the hidden suite at scoring time, never into the workspace.

    Returns the checkout and its revision. The revision goes into the report
    and into the suite's own result, so a score states which grader produced
    it.
    """
    if os.path.isdir(where):
        shutil.rmtree(where)
    outcome = run(["gh", "repo", "clone", HIDDEN_SUITE, where, "--",
                   "--depth", "1"], timeout=600)
    if outcome["failed"] or outcome["status"] != 0:
        raise ScoreError("the hidden suite could not be cloned: %s"
                         % (outcome["stderr"] or outcome["stdout"])[:400])
    revision = run(["git", "-C", where, "rev-parse", "HEAD"], timeout=120)
    return {"path": where, "revision": revision["stdout"].strip()}


def run_hidden_suite(venv, suite, workspace, which):
    """Run the grader against the installed package, and read its report.

    The runner installs nothing and never writes into the trial; it needs
    only `tariff` importable in the interpreter it runs under, which is the
    trial's own environment.
    """
    report = os.path.join(os.path.dirname(venv), "hidden-%s.json" % which)
    env = dict(os.environ)
    env["HIDDEN_SUITE_REVISION"] = suite["revision"]
    outcome = run([python_in(venv), os.path.join(suite["path"], "run_suite.py"),
                   "--report", report, "--suite", which, "--quiet"],
                  cwd=suite["path"], env=env, timeout=2400)
    if not os.path.exists(report):
        return absent("the grader wrote no report: %s"
                      % (outcome["stderr"] or outcome["stdout"])[-400:],
                      invocation=outcome["argv"])
    with io.open(report, encoding="utf-8") as handle:
        payload = json.load(handle)

    # A grader that collected nothing is not a failing arm. Both are scores
    # of zero and only one of them is about the trial.
    if not payload.get("graded"):
        return absent("the grader graded no checks: %s"
                      % payload.get("reason", "no reason given"),
                      invocation=outcome["argv"], report=payload)
    return measured(payload["pass_rate"], invocation=outcome["argv"],
                    report=payload)


def install_battery(venv, lock):
    """Install the rulers, from the run's lock where one exists.

    The first trial of a run resolves `scoring-requirements.txt` and freezes
    what it got; every later trial installs that. One resolved set across the
    arms is what makes the counts comparable at all.
    """
    if os.path.exists(lock):
        outcome = pip(venv, "install", "-r", lock)
        source = "the run's frozen lock"
    else:
        outcome = pip(venv, "install", "-r", REQUIREMENTS)
        source = "scoring-requirements.txt, resolved for the first time"
    if outcome["failed"] or outcome["status"] != 0:
        return absent("the battery would not install: %s"
                      % (outcome["stderr"] or outcome["stdout"])[-600:])

    frozen = pip(venv, "freeze")
    if not os.path.exists(lock) and frozen["status"] == 0:
        with io.open(lock, "w", encoding="utf-8") as handle:
            handle.write(frozen["stdout"])
    return measured(source, frozen=frozen["stdout"].splitlines())


def ruff_findings(venv, workspace, roots, seen):
    """Lint violations by category, under the harness's own configuration."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run_module(venv, "ruff",
                         ["check", "--no-cache", "--config", RUFF_CONFIG,
                          "--output-format", "json"] + roots, cwd=workspace)
    if outcome["failed"]:
        return absent("ruff %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    try:
        findings = json.loads(outcome["stdout"] or "[]")
    except ValueError:
        return absent("ruff produced no JSON: %s"
                      % (outcome["stderr"] or outcome["stdout"])[:300],
                      seen=seen, invocation=outcome["argv"])
    by_category = {}
    for finding in findings:
        code = finding.get("code") or "unknown"
        prefix = code.rstrip("0123456789") or code
        by_category[prefix] = by_category.get(prefix, 0) + 1
    return measured(len(findings), by_category=by_category, seen=seen,
                    invocation=outcome["argv"])


def ruff_format(venv, workspace, roots, seen):
    """Files the one formatter would reformat."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run_module(venv, "ruff",
                         ["format", "--check", "--no-cache",
                          "--config", RUFF_CONFIG] + roots, cwd=workspace)
    if outcome["failed"]:
        return absent("ruff format %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    count = sum(1 for line in outcome["stdout"].splitlines()
                if line.startswith("Would reformat"))
    return measured(count, seen=seen, invocation=outcome["argv"])


def mypy_errors(venv, workspace, roots, seen):
    """Type errors under `--strict`, one configuration for every arm."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run_module(venv, "mypy", ["--config-file", MYPY_CONFIG] + roots,
                         cwd=workspace)
    if outcome["failed"]:
        return absent("mypy %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    text = outcome["stdout"]

    # mypy answers "no issues found" with status 0 and a count line with
    # status 1. A crash is also non-zero, so the count is read from the text
    # and its absence is missing rather than zero.
    if "no issues found" in text:
        return measured(0, seen=seen, invocation=outcome["argv"])
    count = sum(1 for line in text.splitlines() if ": error:" in line)
    if not count:
        return absent("mypy reported neither errors nor a clean run: %s"
                      % (text or outcome["stderr"])[:300], seen=seen,
                      invocation=outcome["argv"])
    return measured(count, seen=seen, invocation=outcome["argv"])


def bandit_findings(venv, workspace, roots, seen):
    """Security findings, counted at high and medium severity."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run_module(venv, "bandit", ["-q", "-f", "json", "-r"] + roots,
                         cwd=workspace)
    if outcome["failed"]:
        return absent("bandit %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    try:
        payload = json.loads(outcome["stdout"] or "{}")
    except ValueError:
        return absent("bandit produced no JSON: %s"
                      % (outcome["stderr"] or outcome["stdout"])[:300],
                      seen=seen, invocation=outcome["argv"])
    results = payload.get("results", [])
    serious = [r for r in results
               if r.get("issue_severity") in ("HIGH", "MEDIUM")]
    scanned = len(payload.get("metrics", {})) - 1
    if scanned <= 0:
        return absent("bandit scanned no files", seen=seen,
                      invocation=outcome["argv"])
    return measured(len(serious), total=len(results), seen=seen,
                    invocation=outcome["argv"])


def complexity(venv, workspace, roots, seen):
    """Cognitive complexity per function: the maximum, the mean, the count."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    binary = script_in(venv, "complexipy")
    if binary is None:
        return absent("complexipy is not installed in the trial environment",
                      seen=seen)
    report = os.path.join(workspace, "complexipy.json")
    outcome = run([binary, "--output-json", "--quiet"] + roots, cwd=workspace)
    if outcome["failed"] or not os.path.exists(report):
        return absent("complexipy wrote no report: %s"
                      % (outcome["failed"] or outcome["stderr"]
                         or outcome["stdout"])[:300],
                      seen=seen, invocation=outcome["argv"])
    with io.open(report, encoding="utf-8") as handle:
        payload = json.load(handle)
    scores = [entry.get("complexity", 0)
              for entry in payload.get("functions", payload if
                                       isinstance(payload, list) else [])]
    if not scores:
        return absent("complexipy found no functions to measure", seen=seen,
                      invocation=outcome["argv"])
    return measured({"max": max(scores),
                     "mean": round(sum(scores) / len(scores), 2),
                     "over_15": sum(1 for s in scores if s > 15),
                     "functions": len(scores)},
                    seen=seen, invocation=outcome["argv"])


def radon_metrics(venv, workspace, roots, seen):
    """Cyclomatic complexity and the maintainability index, per module."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    cc = run_module(venv, "radon", ["cc", "-j"] + roots, cwd=workspace)
    mi = run_module(venv, "radon", ["mi", "-j"] + roots, cwd=workspace)
    if cc["failed"] or mi["failed"]:
        return absent("radon %s" % (cc["failed"] or mi["failed"]), seen=seen,
                      invocation=cc["argv"])
    try:
        cc_payload = json.loads(cc["stdout"] or "{}")
        mi_payload = json.loads(mi["stdout"] or "{}")
    except ValueError:
        return absent("radon produced no JSON: %s" % cc["stdout"][:300],
                      seen=seen, invocation=cc["argv"])
    blocks = [block for blocks in cc_payload.values()
              if isinstance(blocks, list) for block in blocks]
    ranks = [entry.get("mi") for entry in mi_payload.values()
             if isinstance(entry, dict) and entry.get("mi") is not None]
    if not blocks and not ranks:
        return absent("radon measured no modules", seen=seen,
                      invocation=cc["argv"])
    mean_cc = (round(sum(b.get("complexity", 0) for b in blocks) / len(blocks),
                     2) if blocks else None)
    return measured({"mean_cc": mean_cc,
                     "min_mi": round(min(ranks), 2) if ranks else None,
                     "blocks": len(blocks), "modules": len(ranks)},
                    seen=seen, invocation=cc["argv"])


def docstring_coverage(venv, workspace, roots, seen):
    """Docstring coverage, as a percentage of the things that can carry one."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    binary = script_in(venv, "interrogate")
    if binary is None:
        return absent("interrogate is not installed in the trial environment",
                      seen=seen)
    outcome = run([binary, "--quiet", "--fail-under", "0",
                   "--output-format", "json"] + roots, cwd=workspace)
    if outcome["failed"]:
        return absent("interrogate %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    try:
        payload = json.loads(outcome["stdout"] or "{}")
    except ValueError:
        return absent("interrogate produced no JSON: %s"
                      % (outcome["stdout"] or outcome["stderr"])[:300],
                      seen=seen, invocation=outcome["argv"])
    total = payload.get("total", {})
    if not total.get("total"):
        return absent("interrogate found nothing that can carry a docstring",
                      seen=seen, invocation=outcome["argv"])
    return measured(round(total.get("covered_percentage", 0.0), 2),
                    seen=seen, invocation=outcome["argv"])


def unused_code(venv, workspace, roots, seen):
    """Unused names, as vulture reports them."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run_module(venv, "vulture", roots, cwd=workspace)
    if outcome["failed"]:
        return absent("vulture %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])

    # vulture exits 3 when it finds nothing to do and 1 with findings, so a
    # stderr-only run is the unmeasured case.
    if outcome["status"] not in (0, 1, 3):
        return absent("vulture exited %s: %s"
                      % (outcome["status"], outcome["stderr"][:300]),
                      seen=seen, invocation=outcome["argv"])
    count = sum(1 for line in outcome["stdout"].splitlines() if ":" in line)
    return measured(count, seen=seen, invocation=outcome["argv"])


def own_test_coverage(venv, workspace, roots, seen):
    """Line and branch coverage of the trial's own tests.

    The arm's tests, not the grader's: this measures whether the trial tested
    itself, which the hidden suite cannot answer.
    """
    paths = test_paths(workspace)
    if not paths:
        return absent("the trial wrote no tests", seen=seen)
    coverage = os.path.join(workspace, ".score-coverage.json")
    outcome = run_module(venv, "pytest",
                         ["-q", "-p", "no:cacheprovider", "--cov", PACKAGE,
                          "--cov-branch", "--cov-report",
                          "json:%s" % coverage] + paths,
                         cwd=workspace, timeout=1800)
    if outcome["failed"]:
        return absent("the coverage run %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    if not os.path.exists(coverage):
        return absent("the coverage run wrote no report: %s"
                      % (outcome["failed"] or outcome["stdout"][-300:]),
                      seen=seen, invocation=outcome["argv"])
    with io.open(coverage, encoding="utf-8") as handle:
        payload = json.load(handle)
    totals = payload.get("totals", {})
    return measured({"line": totals.get("percent_covered"),
                     "branch": totals.get("percent_covered_branches"),
                     "tests_passed": outcome["status"] == 0},
                    seen=seen, invocation=outcome["argv"])


def scope(workspace, roots):
    """Files, lines, and artifacts nobody asked for."""
    tracked = run(["git", "-C", workspace, "ls-files"], timeout=120)
    if tracked["failed"] or tracked["status"] != 0:
        return absent("the workspace is not a readable git checkout: %s"
                      % tracked["stderr"][:300])
    files = [line for line in tracked["stdout"].splitlines() if line.strip()]
    unasked = [name for name in files
               if any(token in os.path.basename(name).upper()
                      for token in UNASKED)]
    source = count_source(roots)
    return measured({"tracked_files": len(files),
                     "source_files": source["files"],
                     "source_lines": source["lines"],
                     "unasked_artifacts": len(unasked)},
                    unasked=unasked)


def cost(record):
    """Tokens, turns, wall time and dollar cost, read off the trial record."""
    result = record.get("result") or {}
    usage = result.get("usage") or {}
    if not result:
        return absent("the trial record carries no result object")
    return measured({"input_tokens": usage.get("input_tokens"),
                     "output_tokens": usage.get("output_tokens"),
                     "turns": result.get("num_turns"),
                     "cost_usd": result.get("total_cost_usd"),
                     "elapsed_s": record.get("elapsed_s"),
                     "outcome": record.get("outcome")})


def score_trial(record, options, suite, lock):
    """Score one frozen trial and return its scores.

    The order matters: install first, because every later metric needs the
    package importable, and discovery needs the installed copy to answer for
    its own directory.
    """
    name = "%s%d" % (record["arm"], record["trial"])
    scoring = os.path.join(options.root, "scoring", name)
    os.makedirs(scoring, exist_ok=True)

    frozen = (record.get("frozen") or {}).get("tarball")
    workspace = extract(frozen, os.path.join(scoring, "tree"), name)
    venv = create_venv(os.path.join(scoring, "venv"))

    scores = {"arm": record["arm"], "trial": record["trial"], "name": name,
              "workspace": workspace, "templates_tree": record.get(
                  "templates_tree"),
              "model": record.get("model"), "suite_revision": suite["revision"],
              "scored_at": datetime.datetime.now().isoformat(
                  timespec="seconds")}

    scores["install"] = install_trial(venv, workspace)
    scores["boot"] = boot_check(venv, workspace)

    discovery = discover_roots(venv, workspace)
    roots = discovery["roots"]
    scores["discovery"] = {"roots": roots, "how": discovery["how"],
                           "installed": discovery["installed"]}
    seen = count_source(roots)
    scores["seen"] = seen

    # The grader needs the package importable and its own dependencies in the
    # same interpreter, so it runs before the battery installs anything that
    # could move a version out from under it.
    suite_requirements = os.path.join(suite["path"], "requirements.txt")
    pip(venv, "install", "-r", suite_requirements)
    scores["hidden_suite"] = run_hidden_suite(venv, suite, workspace,
                                             options.suite)

    scores["battery"] = install_battery(venv, lock)
    if scores["battery"]["missing"]:
        for key, _ in BATTERY:
            scores[key] = absent(scores["battery"]["missing"], seen=seen)
    else:
        for key, metric in battery(venv, workspace, roots, seen):
            scores[key] = metric

    context = probes.Context(run=run, measured=measured, absent=absent,
                             python=python_in(venv),
                             script=lambda name: script_in(venv, name))
    scores["structure"] = probes.structure(context, workspace, roots, seen)
    if options.web:
        scores["web"] = probes.web_quality(context, workspace)
    else:
        scores["web"] = absent("the web probes were not requested")

    scores["scope"] = scope(workspace, roots)
    scores["cost"] = cost(record)

    flags = [key for key, value in scores.items()
             if isinstance(value, dict) and value.get("missing")]
    scores["flagged"] = flags
    return scores


def newest_run(root):
    """The most recent run record in a run root."""
    candidates = sorted(glob.glob(os.path.join(root, "run-*.json")))
    if not candidates:
        raise ScoreError("no run record in %s; the harness writes one" % root)
    return candidates[-1]


PLANTED_MODULE = '''"""A plausible module, so the battery has something to read."""


def charge(quantity, unit_price):
    if quantity > 10:
        return quantity * unit_price * 0.9
    return quantity * unit_price
'''

PLANTED_TEST = '''from pkg import charge


def test_charge():
    assert charge(1, 2) == 2
'''


# The static battery, named once. The scorer and the self-test both read this
# list, so the control cannot drift from the thing it controls.
BATTERY = (
    ("ruff", ruff_findings),
    ("ruff_format", ruff_format),
    ("mypy", mypy_errors),
    ("bandit", bandit_findings),
    ("complexity", complexity),
    ("radon", radon_metrics),
    ("docstrings", docstring_coverage),
    ("unused", unused_code),
    ("coverage", own_test_coverage),
)


def battery(venv, workspace, roots, seen):
    """Every static metric, as (key, metric) pairs in the report's own keys."""
    return [(key, probe(venv, workspace, roots, seen))
            for key, probe in BATTERY]


def self_test():
    """Prove the missing-vs-zero rule fires before any score is believed.

    Two stages, because the first one alone proves almost nothing. Pointed at
    an empty tree every probe returns early on a guard clause, and a scorer
    whose guard clause works can still report a clean zero the moment a tool
    is absent — which is the case that actually occurs, and the defect this
    stage was written to catch: `python -m ruff` with no ruff exits non-zero
    with an empty stdout, and an empty stdout parsed as JSON is an empty
    finding list.

    So the second stage plants a real module and a real test in an
    environment that has no battery at all. Every metric must come back
    missing with a reason. Any that comes back zero is a scorer reporting a
    clean trial it never read.
    """
    scratch = os.path.join(os.environ.get("TEMP", "."), "efficacy-self-test")
    if os.path.exists(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)
    venv = create_venv(os.path.join(scratch, "venv"))
    checks = []

    empty = os.path.join(scratch, "empty")
    os.makedirs(empty)
    discovery = discover_roots(venv, empty)
    checks.append(("an empty tree yields no roots", discovery["roots"] == []))
    seen = count_source(discovery["roots"])
    checks.append(("an empty tree reports nothing seen",
                   seen == {"files": 0, "lines": 0}))
    for label, metric in battery(venv, empty, [], seen):
        checks.append(("empty tree: %s is missing, not zero" % label,
                       metric["missing"] is not None
                       and metric["value"] is None))

    # The stage that matters: files the tools could read, and no tools.
    planted = os.path.join(scratch, "planted")
    package = os.path.join(planted, "pkg")
    os.makedirs(package)
    with io.open(os.path.join(package, "__init__.py"), "w",
                 encoding="utf-8") as handle:
        handle.write(PLANTED_MODULE)
    tests = os.path.join(planted, "tests")
    os.makedirs(tests)
    with io.open(os.path.join(tests, "test_charge.py"), "w",
                 encoding="utf-8") as handle:
        handle.write(PLANTED_TEST)

    roots = workspace_packages(planted)
    planted_seen = count_source(roots)
    checks.append(("the planted package is discovered", roots == [package]))
    checks.append(("the planted module is read",
                   planted_seen["files"] == 1 and planted_seen["lines"] > 3))
    for label, metric in battery(venv, planted, roots, planted_seen):
        checks.append(("tools absent: %s is missing, not zero" % label,
                       metric["missing"] is not None
                       and metric["value"] is None))

    for label, ok in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED"))
    shutil.rmtree(scratch, ignore_errors=True)
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Score frozen efficacy-benchmark trials.")
    parser.add_argument("--root", help="the harness's run root")
    parser.add_argument("--run", help="a run record; default is the newest")
    parser.add_argument("--trial", action="append", default=[],
                        help="score only this trial, as A1; repeatable")
    parser.add_argument("--suite", choices=("build", "change"),
                        default="build",
                        help="which acceptance suite the grader runs")
    parser.add_argument("--no-web", dest="web", action="store_false",
                        help="skip the web-quality probes, which need a "
                             "browser and a Java runtime")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the missing-vs-zero rule fires; score "
                             "nothing")
    return parser.parse_args(argv)


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    try:
        run_file = options.run or newest_run(options.root)
        with io.open(run_file, encoding="utf-8") as handle:
            run_record = json.load(handle)
        suite = clone_suite(os.path.join(options.root, "hidden-suite"))
    except ScoreError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 scored, 1 refused")
        return 1

    lock = os.path.join(options.root, "tool-lock.txt")
    wanted = set(options.trial)
    scored, refused = [], 0
    for record in run_record.get("trials", []):
        name = "%s%s" % (record.get("arm"), record.get("trial"))
        if wanted and name not in wanted:
            continue
        if record.get("outcome") not in ("completed", "failed", "timeout"):
            print("%s  skipped: outcome %s" % (name, record.get("outcome")))
            continue
        print("%s  scoring" % name)
        try:
            scores = score_trial(record, options, suite, lock)
        except ScoreError as error:
            print("  refused: %s" % error)
            refused += 1
            continue
        target = os.path.join(options.root, "scores")
        os.makedirs(target, exist_ok=True)
        path = os.path.join(target, "%s.json" % name)
        with io.open(path, "w", encoding="utf-8") as handle:
            json.dump(scores, handle, indent=2, sort_keys=True)
        hidden = scores["hidden_suite"]
        print("  suite %s, %d metric(s) flagged"
              % ("%.1f%%" % (100 * hidden["value"]) if hidden["value"]
                 is not None else "not measured", len(scores["flagged"])))
        scored.append(name)

    lib.print_verdict(refused == 0 and bool(scored),
                      "%d scored, %d refused" % (len(scored), refused))
    return 0 if refused == 0 and scored else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
