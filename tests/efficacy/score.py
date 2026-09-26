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
import subprocess
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
import probes  # noqa: E402
from harness import (SCORABLE, LiveRunError, TrialError,  # noqa: E402
                     arm_name, canonical, claim_area, claim_refusal_check,
                     frozen_top, name_of, release_area, remove_tree,
                     scorable_trials, scoring_area, spellings)

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.basename(__file__)
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


def run(argv, cwd=None, env=None, timeout=TOOL_TIMEOUT, stdin=None):
    """Run one command and return its outcome as data.

    Every invocation is recorded with its argv, so the report can state what
    produced a number. A command that does not exist or does not finish is an
    outcome, not an exception: the caller turns it into a missing metric.
    `stdin` is text written to the command's standard input.
    """
    record = {"argv": list(argv), "cwd": cwd}
    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, input=stdin,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
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
    if os.path.exists(into):
        remove_tree(into)
    os.makedirs(into)
    with tarfile.open(tarball) as archive:
        archive.extractall(into, filter="data")

    # The tarball's top directory carries the trial's name as spelled when it
    # was frozen; round 1's `B1` is scored under `full-1` today.
    try:
        top = frozen_top(tarball, into)
    except TrialError as error:
        raise ScoreError(str(error))
    if top != name:
        os.rename(os.path.join(into, top), target)
    return target


def create_venv(where):
    """A clean virtual environment for one trial."""
    if os.path.exists(where):
        remove_tree(where)
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
        remove_tree(where)
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
    return suite_result(payload, outcome["argv"])


# A check the grader skipped is a check nobody ran: the browser flows skip
# where the browser is absent, and the modules that build the application skip
# where it cannot be built. The rate is taken over what ran, so a skip left
# unsaid pays a trial for the checks it never faced.
def suite_result(payload, argv):
    """The hidden suite's metric: its pass rate, and the skips beside it."""
    counts = payload.get("counts") or {}
    skipped = counts.get("skipped") or 0
    partial = None
    if skipped:
        partial = ("%d of %d check(s) were skipped, so the pass rate is over "
                   "the rest" % (skipped, counts.get("total") or 0))
    return measured(payload["pass_rate"], invocation=argv, report=payload,
                    skipped=skipped, partial=partial)


def lock_lines(text):
    """The lines of a `pip freeze` that belong in the tool lock.

    A freeze lists everything installed, the trial's own package included.
    Carried into the lock, that line installs the first trial's package into
    every later trial's environment, over the package being scored. Anything
    installed from a local path or in editable mode is a trial's, and so is
    anything under the package's own name; none of it is a ruler.
    """
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        name = stripped.split("==")[0].split(" @ ")[0].strip().lower()
        if (" @ file:" in stripped or stripped.startswith(("-e ", "--editable"))
                or name == PACKAGE):
            continue
        kept.append(line)
    return kept


def resolve_lock(lock, where, requirements=REQUIREMENTS):
    """Resolve the tools alone and freeze them to the lock; None, or why not.

    The environment at `where` holds nothing but the tools, so the lock
    carries what they need and never a trial's own dependencies.
    """
    venv = create_venv(where)
    outcome = pip(venv, "install", "-r", requirements)
    if outcome["failed"] or outcome["status"] != 0:
        return ("the battery would not resolve: %s"
                % (outcome["stderr"] or outcome["stdout"])[-600:])
    frozen = pip(venv, "freeze")
    if frozen["failed"] or frozen["status"] != 0:
        return ("the resolved battery could not be frozen: %s"
                % (frozen["stderr"] or frozen["stdout"])[-600:])
    with io.open(lock, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lock_lines(frozen["stdout"])) + "\n")
    return None


# The browser the resolved Playwright needs, which is a build of its own. The
# suite skips its browser flows without it and the accessibility probe cannot
# run, and both read as a trial with less to answer for.
def install_browser(venv):
    """Install the browser for the Playwright in `venv`; None, or why not."""
    outcome = run([python_in(venv), "-m", "playwright", "install", "chromium"],
                  timeout=1800)
    if outcome["failed"] or outcome["status"] != 0:
        return ("the browser for the resolved Playwright could not be "
                "installed: %s"
                % (outcome["stderr"] or outcome["stdout"])[-400:])
    return None


def install_battery(venv, lock, requirements=REQUIREMENTS):
    """Install the rulers from the run's lock, resolving it where none exists.

    One resolved set across the arms is what makes the counts comparable at
    all, and every trial installs it, the first included.
    """
    source = "the run's frozen lock"

    # Resolved apart from every trial. Frozen from the first trial's own
    # environment, the lock carried that trial's dependencies and installed
    # them into every later trial, under the metrics measured after it.
    if not os.path.exists(lock):
        reason = resolve_lock(
            lock, os.path.join(os.path.dirname(lock), "scoring", "tools"),
            requirements)
        if reason:
            return absent(reason)
        source = ("scoring-requirements.txt, resolved for the first time in an "
                  "environment holding only the tools")

    # A lock frozen before trial packages were left out can still carry
    # one, so it is filtered on the way in as well as on the way out.
    with io.open(lock, encoding="utf-8") as handle:
        rulers = lock_lines(handle.read())
    filtered = os.path.join(venv, "tool-lock.txt")
    with io.open(filtered, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rulers) + "\n")
    outcome = pip(venv, "install", "-r", filtered)
    if outcome["failed"] or outcome["status"] != 0:
        return absent("the battery would not install: %s"
                      % (outcome["stderr"] or outcome["stdout"])[-600:])
    frozen = pip(venv, "freeze")
    return measured(source, frozen=frozen["stdout"].splitlines())


# Where the installed package came from, by the installer's own record of the
# directory it was built from. Printed as JSON; null where nothing is
# installed under the package's name.
PACKAGE_SOURCE = (
    "import json, importlib.metadata as metadata\n"
    "names = metadata.packages_distributions().get(%r) or []\n"
    "url = None\n"
    "if names:\n"
    "    text = metadata.distribution(names[0]).read_text('direct_url.json')\n"
    "    url = json.loads(text).get('url') if text else None\n"
    "print(json.dumps(url))\n" % PACKAGE)


def package_source(venv):
    """The URL the package under score was installed from, or None."""
    outcome = run([python_in(venv), "-c", PACKAGE_SOURCE], timeout=120)
    if outcome["failed"] or outcome["status"] != 0:
        return None
    try:
        return json.loads(outcome["stdout"].strip() or "null")
    except ValueError:
        return None


def package_moved(before, after):
    """Why the package under score is no longer the trial's, or None."""
    if after == before:
        return None
    return ("the battery install replaced the package under score: it was "
            "installed from %s and is now installed from %s" % (before, after))


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

    # The exit status is not read: complexipy exits non-zero whenever a
    # function passes its own threshold, which is a finding, not a failure.
    outcome = run([binary, "--output-format", "json", "--output", report,
                   "--quiet"] + roots, cwd=workspace)
    if outcome["failed"] or not os.path.exists(report):
        return absent("complexipy wrote no report: %s"
                      % (outcome["failed"] or outcome["stderr"]
                         or outcome["stdout"])[:300],
                      seen=seen, invocation=outcome["argv"])
    with io.open(report, encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = (payload if isinstance(payload, list)
               else payload.get("functions", []))
    scores = [entry.get("complexity", 0) for entry in entries]
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


# interrogate writes no machine-readable report, and its table is for
# people. Its own API answers the count the table prints, with the
# defaults the command line uses.
DOCSTRING_COUNT = (
    "import json, sys\n"
    "from interrogate import config, coverage\n"
    "results = coverage.InterrogateCoverage(\n"
    "    paths=sys.argv[1:], conf=config.InterrogateConfig()).get_coverage()\n"
    "print(json.dumps({'total': results.total, 'covered': results.covered,\n"
    "                  'percent': results.perc_covered}))\n")


def docstring_coverage(venv, workspace, roots, seen):
    """Docstring coverage, as a percentage of the things that can carry one."""
    if not roots:
        return absent("no source roots were discovered", seen=seen)
    outcome = run([python_in(venv), "-c", DOCSTRING_COUNT] + roots,
                  cwd=workspace)
    if outcome["failed"]:
        return absent("interrogate %s" % outcome["failed"], seen=seen,
                      invocation=outcome["argv"])
    if "No module named" in (outcome["stderr"] or ""):
        return absent("interrogate is not installed in the trial environment",
                      seen=seen, invocation=outcome["argv"])
    try:
        payload = json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return absent("interrogate produced no count: %s"
                      % (outcome["stderr"] or outcome["stdout"])[:300],
                      seen=seen, invocation=outcome["argv"])
    if not payload.get("total"):
        return absent("interrogate found nothing that can carry a docstring",
                      seen=seen, invocation=outcome["argv"])
    return measured(round(payload["percent"], 2), total=payload["total"],
                    covered=payload["covered"], seen=seen,
                    invocation=outcome["argv"])


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

    # With branch measurement on, `percent_covered` blends statements and
    # branches, so each is read from its own key.
    return measured({"line": totals.get("percent_statements_covered"),
                     "branch": totals.get("percent_branches_covered"),
                     "tests_passed": outcome["status"] == 0},
                    seen=seen, invocation=outcome["argv"])


def pyproject_complete(workspace):
    """Whether the packaging metadata carries what a published project owes."""
    path = os.path.join(workspace, "pyproject.toml")
    if not os.path.exists(path):
        return None
    try:
        import tomllib
        with io.open(path, "rb") as handle:
            payload = tomllib.load(handle)
    except Exception:
        return None
    project = payload.get("project") or {}
    dynamic = set(project.get("dynamic") or [])
    owed = ("name", "version", "description", "requires-python")
    return all(key in project or key in dynamic for key in owed)


def readme_usable(workspace):
    """Whether a README says how to install it and how to use it."""
    for name in sorted(os.listdir(workspace)):
        if not name.upper().startswith("README"):
            continue
        with io.open(os.path.join(workspace, name), encoding="utf-8",
                     errors="replace") as handle:
            text = handle.read().lower()
        return ("install" in text
                and ("usage" in text or "example" in text
                     or "getting started" in text))
    return None


def adherence(workspace, scores):
    """The fixed checklist, scored on every arm.

    It is a quality checklist rather than a template checklist, which is why
    the control scores on it too. An item no tool could measure is recorded as
    unmeasured and leaves the denominator, so the fraction never credits a
    trial for a check that did not run.
    """
    structure = scores.get("structure") or {}
    facts = structure.get("value") or {}
    coverage = (scores.get("coverage") or {}).get("value") or {}
    complexity_value = (scores.get("complexity") or {}).get("value") or {}
    logging_facts = facts.get("logging") or {}
    roots = (scores.get("discovery") or {}).get("roots") or []

    def clean(key):
        metric = scores.get(key) or {}
        return None if metric.get("missing") else metric.get("value") == 0

    items = {
        "ruff_clean": clean("ruff"),
        "mypy_clean": clean("mypy"),
        "formatted": clean("ruff_format"),
        "coverage_80": (None if coverage.get("line") is None
                        else coverage["line"] >= 80),
        "complexity_15": (None if not complexity_value
                          else complexity_value.get("over_15") == 0),
        "src_layout": (None if not roots
                       else any(os.sep + "src" + os.sep in path
                                for path in roots)),
        "one_error_hierarchy": (None if not facts
                                else len(facts.get("exception_bases") or []) <= 1),
        "no_print_in_library": (None if not facts
                                else not facts.get("print_calls")),
        "citation_ban": None if not facts else not facts.get("citations"),
        "null_handler": (None if not logging_facts.get("used")
                         else bool(logging_facts.get("null_handler"))),
        "pyproject_metadata": pyproject_complete(workspace),
        "readme_install_and_usage": readme_usable(workspace),
        "tests_discoverable": (None if (scores.get("coverage") or {}).get(
            "missing") else True),
    }
    taken = {key: value for key, value in items.items() if value is not None}
    if not taken:
        return absent("no checklist item could be measured", items=items)
    return measured(round(sum(1 for v in taken.values() if v) / len(taken), 3),
                    items=items, measured_items=len(taken),
                    total_items=len(items))


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


# A metric nested under another is still a metric. `web` carries the HTML
# validity and accessibility readings inside itself, and a flag list that read
# only the top level called a trial clean whose accessibility probe never ran.
def metric_flags(scores):
    """Every metric recorded missing or partial, nested ones included."""
    flags = []
    for key, value in sorted(scores.items()):
        if not isinstance(value, dict) or "missing" not in value:
            continue
        if value.get("missing") or value.get("partial"):
            flags.append(key)
        for inner, nested in sorted(value.items()):
            if (isinstance(nested, dict) and "missing" in nested
                    and (nested.get("missing") or nested.get("partial"))):
                flags.append("%s.%s" % (key, inner))
    return flags


def score_trial(record, options, suite, lock):
    """Score one frozen trial and return its scores.

    The order matters: install first, because every later metric needs the
    package importable, and discovery needs the installed copy to answer for
    its own directory.
    """
    name = name_of(record)
    scoring = os.path.join(scoring_area(options.root), "scoring", name)
    os.makedirs(scoring, exist_ok=True)

    frozen = (record.get("frozen") or {}).get("tarball")
    workspace = extract(frozen, os.path.join(scoring, "tree"), name)
    venv = create_venv(os.path.join(scoring, "venv"))

    scores = {"arm": arm_name(record["arm"]), "trial": record["trial"],
              "name": name,
              "workspace": workspace, "templates_tree": record.get(
                  "templates_tree"),
              "model": record.get("model"), "suite_revision": suite["revision"],
              "scored_at": datetime.datetime.now().isoformat(
                  timespec="seconds")}

    scores["install"] = install_trial(venv, workspace)
    source = package_source(venv)
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

    # Before the grader, because its browser flows skip without a browser and
    # a skipped check is not a passed one.
    if options.web:
        refusal = install_browser(venv)
        if refusal:
            raise ScoreError("%s; score with --no-web to accept the skips"
                             % refusal)
    scores["hidden_suite"] = run_hidden_suite(venv, suite, workspace, "build")

    scores["battery"] = install_battery(venv, lock)

    # Again after the battery, which installs the lock's own Playwright over
    # the grader's: the browser matched the version before, not this one.
    if options.web and not scores["battery"]["missing"]:
        refusal = install_browser(venv)
        if refusal:
            raise ScoreError("%s; score with --no-web to accept the skips"
                             % refusal)

    # What runs from here runs in the trial's interpreter, and much of it
    # imports the package. A package the battery replaced would be measured
    # as another trial's code without any error, so every such metric is
    # recorded missing instead.
    moved = package_moved(source, package_source(venv))
    if moved:
        scores["battery"] = absent(moved)
    if scores["battery"]["missing"]:
        for key, _ in BATTERY:
            scores[key] = absent(scores["battery"]["missing"], seen=seen)
    else:
        for key, metric in battery(venv, workspace, roots, seen):
            scores[key] = metric

    context = probes.Context(run=run, measured=measured, absent=absent,
                             python=python_in(venv),
                             script=lambda name: script_in(venv, name))
    if moved:
        scores["structure"] = absent(moved, seen=seen)
        scores["web"] = absent(moved)
    else:
        scores["structure"] = probes.structure(context, workspace, roots,
                                               seen)
        if options.web:
            scores["web"] = probes.web_quality(context, workspace)
        else:
            scores["web"] = absent("the web probes were not requested")

    # After the battery and the structure probe, because every item it scores
    # is read from one of them.
    scores["adherence"] = adherence(workspace, scores)

    scores["scope"] = scope(workspace, roots)
    scores["cost"] = cost(record)

    scores["flagged"] = metric_flags(scores)
    return scores


# What churn does not count: environments, caches, build output and the
# application's database. Each changes when the agent runs the code rather
# than when it changes the design.
CHURN_EXCLUDED = ("venv", ".venv", "__pycache__", "node_modules",
                  ".pytest_cache", ".ruff_cache", ".mypy_cache", "build",
                  "dist", "*.egg-info", "*.sqlite", "*.sqlite3", "*.db")


def churn(workspace, base):
    """Files and lines the change task touched, against its starting commit."""

    # Intent-to-add first, so a file the agent created and never staged is
    # counted: a diff against the base commit sees only what git tracks.
    staged = run(["git", "-C", workspace, "add", "--all", "--intent-to-add"],
                 timeout=120)
    excluded = [":(exclude,glob)**/%s" % pattern for pattern in CHURN_EXCLUDED]
    excluded += [":(exclude,glob)**/%s/**" % pattern
                 for pattern in CHURN_EXCLUDED if "*" not in pattern]
    outcome = run(["git", "-C", workspace, "diff", "--numstat", base, "--",
                   "."] + excluded, timeout=120)
    for step in (staged, outcome):
        if step["failed"] or step["status"] != 0:
            return absent("git could not diff the change against %s: %s"
                          % (base, (step["failed"] or step["stderr"])[:300]),
                          invocation=step["argv"])

    files, added, removed, binary = 0, 0, 0, 0
    for line in outcome["stdout"].splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        if parts[0] == "-":
            binary += 1
            continue
        added += int(parts[0])
        removed += int(parts[1])
    return measured({"files": files, "added": added, "removed": removed,
                     "lines": added + removed, "binary_files": binary},
                    invocation=outcome["argv"])


def score_change_trial(record, options, suite):
    """Score one frozen change task: install, both suites, churn and cost."""
    name = name_of(record)
    frozen = "change-%s" % name

    # Apart from `scoring/`, whose extracted trees the judge takes for build
    # trials; a change tree there would be judged as one.
    scoring = os.path.join(scoring_area(options.root), "scoring-change", name)
    os.makedirs(scoring, exist_ok=True)
    workspace = extract((record.get("frozen") or {}).get("tarball"),
                        os.path.join(scoring, "tree"), frozen)
    venv = create_venv(os.path.join(scoring, "venv"))

    scores = {"arm": arm_name(record["arm"]), "trial": record["trial"],
              "name": name,
              "task": "change", "workspace": workspace,
              "base": record.get("base"), "model": record.get("model"),
              "suite_revision": suite["revision"],
              "scored_at": datetime.datetime.now().isoformat(
                  timespec="seconds")}
    scores["install"] = install_trial(venv, workspace)

    # The build suite re-runs unchanged beside the change suite: a change that
    # passes its own checks by breaking the application has not scored well.
    pip(venv, "install", "-r", os.path.join(suite["path"], "requirements.txt"))

    # Both suites carry browser flows, which skip where there is no browser.
    if options.web:
        refusal = install_browser(venv)
        if refusal:
            raise ScoreError("%s; score with --no-web to accept the skips"
                             % refusal)
    scores["build_suite"] = run_hidden_suite(venv, suite, workspace, "build")
    scores["change_suite"] = run_hidden_suite(venv, suite, workspace,
                                              "change")
    scores["churn"] = (churn(workspace, record["base"]) if record.get("base")
                       else absent("the change record names no starting "
                                   "commit"))
    scores["cost"] = cost(record)
    scores["flagged"] = metric_flags(scores)
    return scores


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


def run_record_checks(scratch):
    """Blocked trials are never offered, and a trial offered twice refuses."""
    def plant(name, trials):
        with io.open(os.path.join(scratch, name), "w",
                     encoding="utf-8") as handle:
            json.dump({"trials": trials}, handle)

    # Round 1's records name their arms by letter, and a record of this round
    # by word; both are offered under the words.
    plant("run-1.json", [{"arm": "A", "trial": 1, "outcome": "blocked"},
                         {"arm": "A", "trial": 1, "outcome": "completed"},
                         {"arm": "B", "trial": 1, "outcome": "budget"},
                         {"arm": "C", "trial": 1, "outcome": "refused"},
                         {"arm": "short", "trial": 1, "outcome": "timeout"}])
    offered = scorable_trials(scratch)
    checks = [("only completed, budget and timeout endings are offered, "
               "under the arms' words",
               sorted(offered) == ["full-1", "none-1", "short-1"]),
              ("a blocked trial yields to its re-run",
               offered["none-1"]["outcome"] == "completed")]

    plant("run-2.json", [{"arm": "A", "trial": 1, "outcome": "completed",
                          "task": "change"}])
    checks.append(("a change task is offered only as a change task",
                   sorted(scorable_trials(scratch, task="change"))
                   == ["none-1"]
                   and sorted(scorable_trials(scratch))
                   == ["full-1", "none-1", "short-1"]))

    plant("run-3.json", [{"arm": "none", "trial": 1, "outcome": "completed"}])
    try:
        scorable_trials(scratch)
        checks.append(("a trial two records offer refuses", False))
    except TrialError:
        checks.append(("a trial two records offer refuses", True))

    # A score round 1 wrote under its letter is the trial's score under its
    # word, and a revision it was graded at is read back.
    written = os.path.join(scratch, "scores")
    os.makedirs(written)
    with io.open(os.path.join(written, "A1.json"), "w",
                 encoding="utf-8") as handle:
        json.dump({"name": "A1", "suite_revision": "earlier"}, handle)
    checks.append(("an existing score is found under either spelling",
                   existing_score(written, "none-1")
                   == os.path.join(written, "A1.json")
                   and existing_score(written, "short-1") is None
                   and graded_revisions(written) == {"earlier"}))
    return checks


def churn_checks(scratch):
    """Churn counts an edit and a new file, and never an environment."""
    repo = os.path.join(scratch, "churn")
    os.makedirs(repo)

    def git_in(*args):
        return run(["git", "-C", repo] + list(args), timeout=120)

    def plant(name, text):
        path = os.path.join(repo, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)

    git_in("init", "-q")
    plant("rules.py", "one\ntwo\n")
    git_in("add", "-A")
    git_in("-c", "user.name=efficacy", "-c",
           "user.email=efficacy@example.invalid", "commit", "-q", "-m",
           "base")
    base = git_in("rev-parse", "HEAD")["stdout"].strip()
    plant("rules.py", "one\nthree\n")
    plant("threshold.py", "new\nrule\n")
    plant(os.path.join(".venv", "lib", "site.py"), "installed\n")
    plant("tariff.sqlite", "rows\n")

    # The plant landed: an edit, a new file and two paths churn must not
    # count are all on disk before the count is read.
    landed = bool(base) and all(
        os.path.isfile(os.path.join(repo, name))
        for name in ("threshold.py", os.path.join(".venv", "lib", "site.py"),
                     "tariff.sqlite"))
    counted = churn(repo, base).get("value") or {}
    return [("the churn plant landed", landed),
            ("churn counts an edit and a new file, not an environment",
             counted.get("files") == 2 and counted.get("lines") == 4)]


def lock_checks():
    """A trial's own package never reaches the lock, and a replaced one shows."""
    freeze = ("ruff==0.16.0\n"
              "tariff @ file:///C:/efficacy/run/scoring/A1/tree/A1\n"
              "-e git+https://example.invalid/other.git#egg=other\n"
              "Tariff==0.1.0\n"
              "pytest==9.1.1\n")

    # The plant landed: each kind of trial package is in the input, so a line
    # missing from the output is the filter's doing.
    landed = all(marker in freeze for marker in (" @ file:", "-e ", "Tariff=="))
    return [("the planted freeze carries each kind of trial package", landed),
            ("only the tools reach the lock",
             lock_lines(freeze) == ["ruff==0.16.0", "pytest==9.1.1"]),
            ("a package that stays put is not flagged",
             package_moved("file:///run/B1", "file:///run/B1") is None),
            ("a package the battery replaced is flagged",
             package_moved("file:///run/B1", "file:///run/A1") is not None)]


# The validator's JSON report in the shape html5validator 0.4.2 prints: the
# first message as it printed it over a real trial's pages, then one other
# error and one note planted beside it.
PLANTED_VALIDATOR_REPORT = json.dumps({"messages": [
    {"type": "error", "message": "Attribute 'hx-post' not allowed on element "
                                 "'form' at this point."},
    {"type": "error", "message": "Element 'div' not allowed as child of "
                                 "element 'ul' in this context."},
    {"type": "info", "message": "Trailing slash on void elements has no "
                                "effect and interacts badly with unquoted "
                                "attribute values."},
]})


def html_checks():
    """The validator's report is read, and only HTMX attributes set aside."""

    # The plant landed: the report carries both kinds of error and a note, so
    # a count of one is the filter's doing and not a missing message.
    kinds = [message["type"] for message
             in json.loads(PLANTED_VALIDATOR_REPORT)["messages"]]
    counted = probes.html_errors(PLANTED_VALIDATOR_REPORT)
    return [("the planted report has two errors and a note",
             kinds == ["error", "error", "info"]),
            ("the validator's report is read as one object",
             counted is not None),
            ("an hx-* error is set aside and another counts",
             counted == {"errors": 1, "ignored": 1, "messages": 3}),
            ("a bare list is not read as the report",
             probes.html_errors("[]") is None)]


def readonly_checks(scratch):
    """A tree holding a read-only file is replaced, as Git's pack files are."""
    into = os.path.join(scratch, "readonly")
    target = os.path.join(into, "none-1")
    pack = os.path.join(target, ".git", "objects", "pack")
    os.makedirs(pack)
    planted = os.path.join(pack, "pack-planted.idx")
    with io.open(planted, "w", encoding="utf-8") as handle:
        handle.write("planted")
    os.chmod(planted, 0o444)
    source = os.path.join(scratch, "readonly-source", "A1")
    os.makedirs(source)
    with io.open(os.path.join(source, "app.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("fresh = True\n")

    # Frozen under round 1's spelling, so the extract under the word has to
    # take the directory it finds and rename it.
    tarball = os.path.join(scratch, "readonly-A1.tar")
    with tarfile.open(tarball, "w") as archive:
        archive.add(source, arcname="A1")

    # The plant landed: the file the extract must replace is read-only, which
    # is what stops a plain removal on Windows.
    landed = not os.access(planted, os.W_OK)
    try:
        workspace = extract(tarball, into, "none-1")
    except (OSError, ScoreError):
        workspace = None
    return [("the planted pack file is read-only", landed),
            ("an extract replaces a tree holding it, under the trial's "
             "name whatever the tarball spelled",
             workspace == target and not os.path.exists(planted)
             and os.path.isfile(os.path.join(target, "app.py"))
             and os.listdir(into) == ["none-1"])]


# The grader's report as `run_suite.py` writes it, cut to the counts: five
# checks skipped for want of a browser, as a re-score of A1 recorded.
PLANTED_SUITE_REPORT = {"graded": True, "pass_rate": 0.9973,
                        "counts": {"error": 0, "failed": 1, "passed": 371,
                                   "skipped": 5, "total": 377}}


def unrun_checks(scratch):
    """A skipped check and a missing nested metric both reach the flags."""
    partial = suite_result(PLANTED_SUITE_REPORT, ["planted"])
    whole = suite_result({"graded": True, "pass_rate": 1.0,
                          "counts": {"skipped": 0, "total": 377}}, ["planted"])
    planted = {"hidden_suite": partial,
               "web": measured({"builder_status": 200},
                               accessibility=absent("axe could not run"),
                               html_validity=measured(0)),
               "install": measured(True)}
    flags = metric_flags(planted)

    # The plant landed: the report carries skips, and the nested metric is
    # missing inside a metric that was taken.
    landed = (PLANTED_SUITE_REPORT["counts"]["skipped"] == 5
              and planted["web"]["missing"] is None
              and planted["web"]["accessibility"]["missing"])
    return [("the plant skips five checks inside a measured web", landed),
            ("a skipped check is recorded beside the rate",
             partial["skipped"] == 5 and bool(partial["partial"])),
            ("a suite that skipped nothing is not partial",
             whole["skipped"] == 0 and whole["partial"] is None),
            ("a partial suite is flagged", "hidden_suite" in flags),
            ("a missing nested metric is flagged",
             "web.accessibility" in flags),
            ("a metric that was taken is not flagged",
             flags == ["hidden_suite", "web.accessibility"]),
            ("a venv with no interpreter cannot install a browser",
             install_browser(os.path.join(scratch, "no-such-venv"))
             is not None)]


def lock_source_checks(scratch):
    """The lock is resolved apart from the trial, so its dependencies stay out."""
    where = os.path.join(scratch, "lock-source")
    trial = create_venv(os.path.join(where, "trial"))
    site = run([python_in(trial), "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))"],
               timeout=120)["stdout"].strip()

    # An installer's record is all a freeze reads, so a planted one stands for
    # a dependency the trial installed, with no network and no build.
    record = os.path.join(site, "Flask_WTF-1.3.0.dist-info")
    os.makedirs(record)
    with io.open(os.path.join(record, "METADATA"), "w",
                 encoding="utf-8") as handle:
        handle.write("Metadata-Version: 2.1\nName: Flask-WTF\nVersion: 1.3.0\n")
    io.open(os.path.join(record, "RECORD"), "w", encoding="utf-8").close()
    requirements = os.path.join(where, "requirements.txt")
    with io.open(requirements, "w", encoding="utf-8") as handle:
        handle.write("# no tools, so the check needs no network\n")
    lock = os.path.join(where, "tool-lock.txt")

    # The plant landed: the trial's own environment lists the dependency, so
    # a lock without it was not frozen from there.
    landed = "Flask-WTF==1.3.0" in pip(trial, "freeze")["stdout"]
    installed = install_battery(trial, lock, requirements)
    written = None
    if os.path.exists(lock):
        with io.open(lock, encoding="utf-8") as handle:
            written = handle.read()
    return [("the trial's environment lists a planted dependency", landed),
            ("the battery installs from a lock it resolved",
             installed["missing"] is None and written is not None),
            ("the lock carries none of the trial's dependencies",
             written is not None and "Flask-WTF" not in written)]


def claim_checks(scratch):
    """A scoring run refuses while another holds the area, and clears
    nothing: the hidden suite is never cloned."""
    root = os.path.join(scratch, "claimed")
    label, refused = claim_refusal_check(SCRIPT, main, root)
    return [(label, refused and not os.path.exists(
        os.path.join(scoring_area(root), "hidden-suite")))]


def security_checks(scratch):
    """A build scoring reads security for what it scored and what lacks a
    reading, and leaves a skipped trial's reading alone."""
    target = os.path.join(scratch, "security-scores")
    os.makedirs(target)
    for name in ("full-1", "none-1"):
        with io.open(os.path.join(target, "%s.json" % name), "w",
                     encoding="utf-8") as handle:
            handle.write("{}")
    owed = security_owed(target, ["full-1", "hand-1", "none-1"], ["none-1"])
    return [("a rescored trial is read again, a skipped one only if unread",
             owed == ["hand-1", "none-1"])]


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
    remove_tree(scratch)
    os.makedirs(scratch)
    checks = (run_record_checks(scratch) + churn_checks(scratch)
              + lock_checks() + html_checks() + readonly_checks(scratch)
              + lock_source_checks(scratch) + unrun_checks(scratch)
              + claim_checks(scratch) + security_checks(scratch))
    venv = create_venv(os.path.join(scratch, "venv"))

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
    remove_tree(scratch)
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def existing_score(target, name):
    """The score file already written for a trial, in either spelling, or
    None."""
    for spelled in spellings(name):
        path = os.path.join(target, "%s.json" % spelled)
        if os.path.isfile(path):
            return path
    return None


def graded_revisions(target):
    """Every hidden-suite revision the scores already in `target` were
    graded at."""
    revisions = set()
    for file in glob.glob(os.path.join(target, "*.json")):
        with io.open(file, encoding="utf-8") as handle:
            revision = json.load(handle).get("suite_revision")
        if revision:
            revisions.add(revision)
    return revisions


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Score frozen efficacy-benchmark trials.")
    parser.add_argument("--root", help="the harness's run root")
    parser.add_argument("--rescore", action="store_true",
                        help="score a trial whose score is already written; "
                             "by default such a trial is skipped")
    parser.add_argument("--run",
                        help="score only this run record; default is every "
                             "run record in the root")
    parser.add_argument("--trial", action="append", default=[],
                        help="score only this trial, as none-1; repeatable")
    parser.add_argument("--task", choices=("build", "change"),
                        default="build",
                        help="score the build trials, or the change tasks "
                             "run on them")
    parser.add_argument("--no-web", dest="web", action="store_false",
                        help="skip the web-quality probes, which need a "
                             "browser and a Java runtime")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the missing-vs-zero rule fires; score "
                             "nothing")
    return parser.parse_args(argv)


def summary(scores):
    """One line on what a scored trial came to."""
    def rate(key):
        value = (scores.get(key) or {}).get("value")
        return "not measured" if value is None else "%.1f%%" % (100 * value)

    flagged = len(scores.get("flagged") or [])
    if scores.get("task") == "change":
        changed = (scores.get("churn") or {}).get("value") or {}
        return ("change suite %s, build suite %s, %s file(s) and %s line(s) "
                "changed, %d metric(s) flagged"
                % (rate("change_suite"), rate("build_suite"),
                   changed.get("files", "?"), changed.get("lines", "?"),
                   flagged))
    return "suite %s, %d metric(s) flagged" % (rate("hidden_suite"), flagged)


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    # A run clears the hidden suite's clone, and each trial's tree and
    # environment, before rebuilding them, so a second run against the area
    # deletes what a live one is reading.
    try:
        claim = claim_area(scoring_area(options.root), SCRIPT)
    except LiveRunError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 scored, 1 refused")
        return 1
    try:
        return score_trials(options)
    finally:
        release_area(claim)


def score_trials(options):
    """Score every trial the run records offer; return the exit code."""
    try:
        offered = scorable_trials(options.root, options.run, options.task)
        if not offered:
            raise ScoreError("no %s trial in the run records ended %s"
                             % (options.task, " or ".join(SCORABLE)))
        suite = clone_suite(os.path.join(scoring_area(options.root),
                                         "hidden-suite"))
    except (ScoreError, TrialError) as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 scored, 1 refused")
        return 1

    # Change scores go apart from the build scores: both are keyed by the
    # trial, and one must never overwrite the other.
    area = scoring_area(options.root)
    lock = os.path.join(area, "tool-lock.txt")
    target = os.path.join(area, "scores" if options.task == "build"
                          else "scores-change")
    try:
        wanted = {canonical(name) for name in options.trial}
    except TrialError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 scored, 1 refused")
        return 1

    # A root holding two rounds carries the earlier round's scores, graded
    # at its suite revision. A grader corrected since is never run on the
    # same trials, and the two rounds are never graded by two suites.
    earlier = graded_revisions(target) - {suite["revision"]}
    if earlier:
        print("refused: %s holds scores graded at %s, and the hidden suite "
              "is at %s; a run at another revision is another root"
              % (target, ", ".join(sorted(earlier)), suite["revision"]))
        lib.print_verdict(False, "0 scored, 1 refused")
        return 1

    scored, skipped, refused = [], [], 0
    for name in sorted(wanted - set(offered)):
        print("%s  refused: no run record offers it for scoring" % name)
        refused += 1
    for name, record in sorted(offered.items()):
        if wanted and name not in wanted:
            continue
        written = existing_score(target, name)
        if written and not options.rescore:
            print("%s  already scored at %s; --rescore to score it again"
                  % (name, written))
            skipped.append(name)
            continue
        print("%s  scoring the %s task" % (name, options.task))
        try:
            if options.task == "change":
                scores = score_change_trial(record, options, suite)
            else:
                scores = score_trial(record, options, suite, lock)
        except ScoreError as error:
            print("  refused: %s" % error)
            refused += 1
            continue
        os.makedirs(target, exist_ok=True)
        path = os.path.join(target, "%s.json" % name)
        with io.open(path, "w", encoding="utf-8") as handle:
            json.dump(scores, handle, indent=2, sort_keys=True)
        print("  %s" % summary(scores))
        scored.append(name)

    # The probe pass rates are primary, so a build scoring files them rather
    # than leaving them to a second command someone must remember.
    owed = []
    if options.task == "build":
        owed = security_owed(os.path.join(area, "security-scores"),
                             scored + skipped, scored)
    if owed:
        # Imported here, because security.py imports this module.
        import security
        security.file_readings(area, {name: existing_score(target, name)
                                      for name in owed}, owed)

    done = bool(scored or skipped)
    lib.print_verdict(refused == 0 and done,
                      "%d scored, %d already scored, %d refused, %d read for "
                      "security" % (len(scored), len(skipped), refused,
                                    len(owed)))
    return 0 if refused == 0 and done else 1


def security_owed(target, names, fresh):
    """The trials owed a security reading: each one scored in this run, whose
    reading must describe the tree its new score does, and any other that
    has none."""
    return sorted(name for name in names
                  if name in fresh or existing_score(target, name) is None)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
