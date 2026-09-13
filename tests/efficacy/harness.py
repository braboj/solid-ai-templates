"""Set up and run one efficacy-benchmark trial.

The design, the pre-registered question and the verdict rule live in
`docs/design/efficacy-benchmark.md`. This module owns section 4 of it: the
workspace an arm starts from, the isolated configuration it runs under, the
one prompt every arm receives, and the freeze that ends a trial.

Scoring is not here. A trial produces a frozen workspace and a record; the
hidden suite and the graders read them afterwards.
"""

import argparse
import datetime
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

# This module sits a level below the other runners, so the shared library
# is reached by path rather than as a sibling.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "SPEC.md")
ARMS_DIR = os.path.join(HERE, "arms")

# Identical for every arm, per the design's section 4. Changing it changes
# what the benchmark measures, so it is a constant and not an option.
PROMPT = (
    "Implement the application described in SPEC.md. Done means: "
    "`pip install .` succeeds in a clean virtualenv, your own tests pass, "
    "and every page and route in the spec works end to end against the "
    "seed fixture. Commit when done."
)

# The two bounds on a trial, fixed in the design's section 4. The budget is
# read against the CLI's own cost figure and checked between turns.
BUDGET_USD = 100.0
TIMEOUT_S = 7200

# The context file each arm starts with, relative to `arms/`. Arm A carries
# none: it is the bare agent.
ARMS = {
    "A": {"label": "control", "context": None},
    "B": {"label": "candidate", "context": "B-candidate/CLAUDE.md"},
    "C": {"label": "reference", "context": "C-reference/CLAUDE.md"},
}

# Web access is the confound the design names: an arm that reads the
# templates online is not the arm being measured.
DISALLOWED_TOOLS = ["WebSearch", "WebFetch"]

# No user, project or local settings, and no MCP server the harness did not
# pass -- which is none. Both flags are isolation, not preference.
SETTING_SOURCES = ""

# A minimal settings file, so `--settings` names something real rather than
# falling back to whatever the machine carries.
ISOLATED_SETTINGS = {"includeCoAuthoredBy": False}


class TrialError(Exception):
    """A trial could not be set up or run as the protocol requires."""


def agent_executable():
    """The generator CLI's absolute path.

    A bare "claude" in an argv list is not launchable on Windows, where the
    command is a `.CMD` shim and `CreateProcess` resolves no extension: the
    run dies with "the system cannot find the file specified" before a
    single trial starts. Resolving it here fails with a sentence naming the
    problem instead.
    """
    found = shutil.which("claude")
    if found is None:
        raise TrialError(
            "the `claude` CLI is not on PATH, so no trial can run")
    return found


def repository_root():
    """This repository's absolute root."""
    return os.path.abspath(lib.ROOT)


def assert_outside_repository(root):
    """Refuse a workspace root inside this repository.

    A workspace under the templates repository lets the agent walk up and
    read the very templates arm A is defined not to have. The design lists
    that as a confound and controls it by not mounting the repository, so
    the mount is refused here rather than trusted to the caller.
    """
    root = os.path.abspath(root)
    repo = repository_root()
    if root == repo or root.startswith(repo + os.sep):
        raise TrialError(
            "workspace root %s is inside the templates repository at %s; "
            "an arm there can read the templates" % (root, repo))


def assert_no_ambient_context(workspace, home):
    """Refuse a run that a context file outside the arm would reach.

    The scratch home exists so no global `CLAUDE.md` reaches the bare arm.
    An assertion that it is empty of one is cheap and deterministic, where
    reading the loaded context back costs a model call. Every directory
    from the workspace up to the filesystem root is checked too, because
    memory discovery walks parents.
    """
    found = []
    candidate = os.path.join(home, ".claude", "CLAUDE.md")
    if os.path.exists(candidate):
        found.append(candidate)
    if os.path.exists(os.path.join(home, "CLAUDE.md")):
        found.append(os.path.join(home, "CLAUDE.md"))

    # The workspace's own CLAUDE.md is the arm's, so start above it.
    current = os.path.dirname(os.path.abspath(workspace))
    while True:
        candidate = os.path.join(current, "CLAUDE.md")
        if os.path.exists(candidate):
            found.append(candidate)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    if found:
        raise TrialError(
            "a context file outside the arm would reach this run: %s"
            % ", ".join(found))


def git(workspace, *args):
    """Run git in the workspace, raising on a non-zero status."""
    proc = subprocess.run(["git", "-C", workspace] + list(args),
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise TrialError("git %s failed in %s: %s"
                         % (" ".join(args), workspace, proc.stderr.strip()))
    return proc.stdout.strip()


def prepare_workspace(arm, trial, root):
    """Create the starting workspace for one trial and return its path.

    Fresh directory, `git init`, the arm's starting files, one commit. The
    commit is what the freeze at the end of the trial is measured against:
    without it, a trial that wrote nothing looks the same as one whose work
    was never committed.
    """
    if arm not in ARMS:
        raise TrialError("unknown arm %r; the arms are %s"
                         % (arm, ", ".join(sorted(ARMS))))
    workspace = os.path.join(root, "%s%d" % (arm, trial))
    if os.path.exists(workspace):
        raise TrialError("workspace %s already exists; a trial never reuses "
                         "one" % workspace)
    os.makedirs(workspace)

    shutil.copyfile(SPEC, os.path.join(workspace, "SPEC.md"))
    context = ARMS[arm]["context"]
    if context:
        source = os.path.join(ARMS_DIR, context)
        if not os.path.isfile(source):
            raise TrialError(
                "arm %s needs %s, which does not exist. Arm B's file is "
                "generated through the interview at the recorded release, "
                "never hand-written." % (arm, source))
        shutil.copyfile(source, os.path.join(workspace, "CLAUDE.md"))

    git(workspace, "init", "-q")
    git(workspace, "add", "-A")
    git(workspace, "-c", "user.name=efficacy",
        "-c", "user.email=efficacy@example.invalid",
        "commit", "-q", "-m", "start: %s arm %s" % (ARMS[arm]["label"], arm))
    return workspace


# The one thing the scratch home must inherit. Credentials live under the
# real home, so a fully scratch home authenticates as nobody and every
# trial dies on "Not logged in" — which the CLI reports as a successful
# result with `is_error` set, so it reads like a model answer rather than
# a failure to run.
CREDENTIALS = os.path.join(".claude", ".credentials.json")


def prepare_home(root):
    """Create the scratch home every trial runs under, and return it.

    One home for the whole run rather than one per trial: it holds no trial
    state, and a single directory is one thing to assert about.

    Everything the design's isolation names is absent by construction —
    no global `CLAUDE.md`, no hooks, no auto-memory, no MCP — because the
    directory is new. The credential file is copied in, and nothing else
    is: it carries no context, and without it there is no run at all.
    """
    home = os.path.join(root, "home")
    os.makedirs(os.path.join(home, ".claude"), exist_ok=True)
    settings = os.path.join(home, "settings.json")
    with io.open(settings, "w", encoding="utf-8") as handle:
        json.dump(ISOLATED_SETTINGS, handle)

    real = os.path.expanduser("~")
    source = os.path.join(real, CREDENTIALS)
    if os.path.exists(source):
        shutil.copyfile(source, os.path.join(home, CREDENTIALS))
    return home


def assert_authenticated(home, env_builder, executable):
    """Refuse a run the CLI would answer without reaching a model.

    "Not logged in" comes back as a result object with `is_error` true and
    a zero cost, not as a crash, so a whole run can complete with nine
    trials that never called anything. One cheap call up front is the
    difference between a failed run and a run of failures.
    """
    proc = subprocess.run(
        [executable, "-p", "--output-format", "json",
         "--setting-sources", "", "--settings",
         os.path.join(home, "settings.json"), "--strict-mcp-config"],
        input="Reply with the single word: ready", env=env_builder(home),
        capture_output=True, text=True, encoding="utf-8", timeout=180)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        raise TrialError("the CLI returned no JSON for a trivial prompt: %s"
                         % (proc.stdout or proc.stderr)[:400])
    if payload.get("is_error"):
        raise TrialError("the CLI is not usable in the isolated home: %s"
                         % payload.get("result", "")[:200])
    return payload.get("result", "").strip()


# A trial inherits this machine, not the process that launched it. Each group
# reaches a child process through its environment, which the scratch home and
# the isolated settings leave untouched.
INHERITED_PREFIXES = (
    # The calling agent session: a nested CLI that sees these joins that
    # session, takes its effort, or answers on its socket.
    "CLAUDE", "ANTHROPIC_", "MCP_", "AI_AGENT",

    # The editor the caller runs in.
    "VSCODE_", "ELECTRON_", "TERM_PROGRAM", "GIT_EDITOR", "COPILOT_",

    # An activated interpreter, which every trial would otherwise share.
    "VIRTUAL_ENV", "CONDA_", "PYTHONPATH", "PYTHONHOME",
)

# Credentials the caller holds. A trial runs with every permission bypassed,
# and nothing in the task needs another service's key.
CREDENTIAL_SUFFIXES = ("_API_KEY", "_TOKEN", "_SECRET", "_PASSWORD")

# Kept despite its prefix: it locates a binary and carries no context.
KEPT = ("CLAUDE_CODE_GIT_BASH_PATH",)

# Where an activated interpreter lives. Its directories leave PATH as well,
# or `python` in a trial still resolves into it.
INTERPRETER_ROOTS = ("VIRTUAL_ENV", "CONDA_PREFIX")


def inherited_names(environ):
    """The variable names a trial must not inherit, sorted."""
    return sorted(
        name for name in environ
        if name.upper() not in KEPT
        and (name.upper().startswith(INHERITED_PREFIXES)
             or name.upper().endswith(CREDENTIAL_SUFFIXES)))


def interpreter_directories(environ):
    """The PATH entries that lie inside an activated interpreter."""
    roots = [os.path.normcase(os.path.abspath(environ[name]))
             for name in INTERPRETER_ROOTS if environ.get(name)]
    found = []
    for entry in environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        normal = os.path.normcase(os.path.abspath(entry))
        if any(normal == root or normal.startswith(root + os.sep)
               for root in roots):
            found.append(entry)
    return found


def agent_environment(home, environ=None):
    """The environment a trial runs under: this machine's, minus the caller's."""
    source = dict(os.environ if environ is None else environ)
    dropped = set(inherited_names(source))
    stale = set(interpreter_directories(source))
    env = {name: value for name, value in source.items()
           if name not in dropped}
    if "PATH" in source:
        env["PATH"] = os.pathsep.join(
            entry for entry in source["PATH"].split(os.pathsep)
            if entry and entry not in stale)
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    return env


def agent_command(home, model, effort, budget):
    """The argv for one trial.

    `--max-turns`, which the design's protocol names, is not a flag this
    CLI carries. The bound is a dollar budget and the wall-clock timeout the
    caller applies, and the record states which of them ended a trial.
    """
    argv = [
        agent_executable(), "-p", PROMPT,
        "--output-format", "json",
        "--model", model,
        "--effort", effort,
        "--permission-mode", "bypassPermissions",
        "--setting-sources", SETTING_SOURCES,
        "--settings", os.path.join(home, "settings.json"),
        "--strict-mcp-config",
        "--disallowed-tools",
    ]
    argv.extend(DISALLOWED_TOOLS)
    if budget is not None:
        argv.extend(["--max-budget-usd", str(budget)])
    return argv


def freeze(workspace, record_dir, name):
    """Freeze the workspace before anything scores it.

    Returns the commit the trial ended on and the tarball path. Scoring
    reads the tarball, so a later run in the same directory cannot change
    what was graded.
    """
    status = git(workspace, "status", "--porcelain")
    head = git(workspace, "rev-parse", "HEAD")
    tarball = os.path.join(record_dir, "%s.tar" % name)
    with tarfile.open(tarball, "w") as archive:
        archive.add(workspace, arcname=name)
    return {"head": head, "uncommitted": status.splitlines(), "tarball": tarball}


# The one error ending the protocol sets itself. A trial the budget stopped
# stands and is scored, as a timed-out one does.
BUDGET_SUBTYPE = "error_max_budget_usd"


def classify(status, result):
    """A finished CLI run's outcome, and why where it was blocked."""

    # Fail closed. What a usage limit returns cannot be observed on demand,
    # so a check matching its wording would pass any limit worded otherwise
    # straight into scoring as the model's own failure.
    if not isinstance(result, dict):
        return "blocked", "the CLI returned no JSON result (status %s)" % status
    if result.get("subtype") == BUDGET_SUBTYPE:
        return "budget", None
    if status == 0 and not result.get("is_error"):
        return "completed", None
    return "blocked", ("the CLI ended with an error (status %s, subtype %s, "
                       "API status %s): %s"
                       % (status, result.get("subtype"),
                          result.get("api_error_status"),
                          str(result.get("result") or "")[:300]))


def void(root, workspace, frozen, name):
    """Move a blocked trial's workspace and tarball under `void/`."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    target = os.path.join(root, "void", "%s-%s" % (name, stamp))
    moved = {"dir": target, "workspace": os.path.join(target, name),
             "tarball": os.path.join(target, "%s.tar" % name)}

    # A process the agent left running can hold a file open. A workspace that
    # cannot move would block the re-run, so the caller stops the run.
    try:
        os.makedirs(target)
        shutil.move(workspace, moved["workspace"])
        shutil.move(frozen["tarball"], moved["tarball"])
    except OSError as error:
        raise TrialError("could not void %s: %s" % (name, error))
    return moved


def run_trial(arm, trial, root, home, options):
    """Run one trial and return its record.

    The record carries everything the protocol says a trial must report:
    what ran, under which model and configuration, what it cost, how long
    it took, and the frozen state it left.
    """
    workspace = prepare_workspace(arm, trial, root)
    assert_no_ambient_context(workspace, home)
    argv = agent_command(home, options.model, options.effort, options.budget)

    record = {
        "arm": arm,
        "label": ARMS[arm]["label"],
        "trial": trial,
        "workspace": workspace,
        "prompt": PROMPT,
        "command": argv,
        "model": options.model,
        "effort": options.effort,
        "budget_usd": options.budget,
        "timeout_s": options.timeout,
        "environment_removed": {"names": inherited_names(os.environ),
                                "path": interpreter_directories(os.environ)},
        "templates_tree": lib.tree_id(),
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    if options.dry_run:
        record["outcome"] = "dry-run"
        return record

    started = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=workspace,
                              env=agent_environment(home),
                              capture_output=True, text=True,
                              encoding="utf-8", timeout=options.timeout)
        record["exit_status"] = proc.returncode
        record["stdout"] = proc.stdout
        record["stderr"] = proc.stderr[-4000:]
        try:
            record["result"] = json.loads(proc.stdout)
        except ValueError:
            record["result"] = None
        record["outcome"], record["reason"] = classify(proc.returncode,
                                                       record["result"])
    except subprocess.TimeoutExpired:
        record["outcome"], record["reason"] = "timeout", None
        record["exit_status"] = None

    record["elapsed_s"] = round(time.monotonic() - started, 1)
    name = "%s%d" % (arm, trial)
    record["frozen"] = freeze(workspace, root, name)
    if record["outcome"] == "blocked":
        try:
            record["void"] = void(root, workspace, record["frozen"], name)
            record["frozen"]["tarball"] = record["void"]["tarball"]
        except TrialError as error:
            record["void"] = None
            record["void_error"] = str(error)
    return record


def order(arms, k):
    """Interleave the trials: A1, B1, C1, A2, ...

    A model-side change part-way through a run then lands across the arms
    rather than on one of them, which is the confound the design names.
    """
    return [(arm, trial) for trial in range(1, k + 1) for arm in arms]


def pending_trials(arms, k, start=None):
    """The interleaved order, from `start` onwards where one is given."""
    trials = order(arms, k)
    if start is None:
        return trials
    names = ["%s%d" % pair for pair in trials]
    if start not in names:
        raise TrialError("--from %s is not in this run's order: %s"
                         % (start, ", ".join(names)))
    return trials[names.index(start):]


def write_run(run_file, started_at, records):
    """Rewrite the run record with every trial so far."""

    # Written to a sibling and swapped in, so a run killed mid-write leaves
    # the previous record whole rather than half of a new one.
    partial = run_file + ".partial"
    with io.open(partial, "w", encoding="utf-8") as handle:
        json.dump({"started_at": started_at.isoformat(timespec="seconds"),
                   "prompt": PROMPT, "trials": records}, handle, indent=2)
    os.replace(partial, run_file)


def wait_for_generator(probe, every_s, limit_s, sleep=time.sleep,
                       clock=time.monotonic):
    """Probe on an interval until the generator answers; False on giving up."""
    deadline = clock() + limit_s
    while clock() < deadline:
        sleep(every_s)
        try:
            probe()
            return True
        except (TrialError, subprocess.TimeoutExpired) as error:
            print("  still blocked: %s" % str(error)[:160])
    return False


def run_in_place(arm, trial, runner, wait, records, write):
    """Run one trial, re-running it once in its place if it was blocked.

    Returns False when the run has to stop.
    """
    name = "%s%d" % (arm, trial)
    lost = None
    while True:
        print("%s  %s%s" % (name, ARMS[arm]["label"],
                            "  (re-run)" if lost else ""))
        try:
            record = runner(arm, trial)
        except TrialError as error:
            print("  refused: %s" % error)
            records.append({"arm": arm, "trial": trial, "outcome": "refused",
                            "error": str(error)})
            write()
            return True
        if lost:
            record["substitutes"] = lost["void"]["dir"]
        records.append(record)
        write()
        print("  %s in %ss" % (record["outcome"], record.get("elapsed_s", 0)))
        if record["outcome"] != "blocked":
            return True

        print("  blocked: %s" % (record.get("reason") or "")[:200])
        if not record.get("void"):
            print("  stopping: %s" % record.get("void_error"))
            return False
        if lost:
            print("  stopping: %s was blocked twice" % name)
            return False
        lost = record
        if not wait():
            print("  stopping the run")
            return False


# One variable of each kind the trial environment sheds, and two it must keep.
# Planted in a copy rather than in this process, so the check exercises the
# function and not whatever happened to launch the test.
PLANTED_LEAKS = {
    "CLAUDECODE": "1",
    "CLAUDE_EFFORT": "low",
    "CLAUDE_CODE_MESSAGING_SOCKET": "planted",
    "ANTHROPIC_API_KEY": "planted",
    "AI_AGENT": "planted",
    "VSCODE_PID": "1",
    "GIT_EDITOR": "code --wait",
    "LINEAR_API_KEY": "planted",
    "NOTION_TOKEN": "planted",
}
PLANTED_KEPT = {
    "SYSTEMROOT": "planted",
    "CLAUDE_CODE_GIT_BASH_PATH": "planted",
}


def environment_checks():
    """A trial's environment sheds what the launching process carries."""
    interpreter = os.path.abspath(os.path.join(os.sep, "planted", "venv"))
    stale = os.path.join(interpreter, "Scripts")
    kept = os.path.abspath(os.path.join(os.sep, "planted", "tools"))
    home = os.path.abspath(os.path.join(os.sep, "planted", "home"))

    planted = dict(PLANTED_LEAKS)
    planted.update(PLANTED_KEPT)
    planted["VIRTUAL_ENV"] = interpreter
    planted["PATH"] = os.pathsep.join([stale, kept])
    env = agent_environment(home, planted)

    checks = []

    # The plant landed: every name is in the input, so an absent name in the
    # output is the function's doing and not a missing plant.
    checks.append(("every planted name is in the input",
                   all(name in planted for name in PLANTED_LEAKS)
                   and planted["VIRTUAL_ENV"] == interpreter))
    for name in sorted(PLANTED_LEAKS) + ["VIRTUAL_ENV"]:
        checks.append(("%s is removed" % name, name not in env))
    for name, value in sorted(PLANTED_KEPT.items()):
        checks.append(("%s is kept" % name, env.get(name) == value))
    checks.append(("the interpreter leaves PATH", stale not in
                   env.get("PATH", "").split(os.pathsep)))
    checks.append(("every other PATH entry stays",
                   env.get("PATH") == kept))
    checks.append(("the scratch home is the home", env.get("HOME") == home
                   and env.get("USERPROFILE") == home))
    checks.append(("the record names what was removed",
                   "VIRTUAL_ENV" in inherited_names(planted)
                   and interpreter_directories(planted) == [stale]))
    return checks


# Fabricated CLI endings, one per branch of `classify`. The budget ending has
# the shape the installed CLI returned when a real run reached its cap.
ENDINGS = (
    ("a clean finish", 0, {"subtype": "success", "is_error": False},
     "completed"),
    ("the budget cap", 1,
     {"subtype": BUDGET_SUBTYPE, "is_error": True,
      "errors": ["Reached maximum budget ($0.001)"]}, "budget"),
    ("a usage limit, by its wording", 1,
     {"subtype": "success", "is_error": True,
      "result": "Claude AI usage limit reached"}, "blocked"),
    ("a rate limit, by its status", 1,
     {"subtype": "success", "is_error": True, "api_error_status": 429},
     "blocked"),
    ("an error subtype nobody listed", 1,
     {"subtype": "error_during_execution", "is_error": True}, "blocked"),
    ("an error behind a zero status", 0,
     {"subtype": "success", "is_error": True, "result": "Not logged in"},
     "blocked"),
    ("no JSON at all", 1, None, "blocked"),
)


def outcome_checks():
    """Every ending classifies as the protocol says, and a blocked one moves."""
    checks = [("%s is %s" % (label, expected),
               classify(status, result)[0] == expected)
              for label, status, result, expected in ENDINGS]

    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-void-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    workspace = os.path.join(scratch, "A1")
    os.makedirs(workspace)
    with io.open(os.path.join(workspace, "partial.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("# partial work\n")
    tarball = os.path.join(scratch, "A1.tar")
    with io.open(tarball, "wb") as handle:
        handle.write(b"frozen")

    # The plant is read before the move, so an empty void is the function's
    # failure and not a workspace that was never there.
    checks.append(("the workspace to void exists",
                   os.path.isfile(os.path.join(workspace, "partial.py"))
                   and os.path.isfile(tarball)))
    try:
        moved = void(scratch, workspace, {"tarball": tarball}, "A1")
    except TrialError:
        moved = None
    checks.append(("a voided workspace leaves its slot", moved is not None
                   and not os.path.exists(workspace)
                   and not os.path.exists(tarball)))
    checks.append(("a voided workspace is kept under void/", moved is not None
                   and os.path.isfile(os.path.join(moved["workspace"],
                                                   "partial.py"))
                   and os.path.isfile(moved["tarball"])
                   and os.path.dirname(moved["dir"])
                   == os.path.join(scratch, "void")))
    shutil.rmtree(scratch, ignore_errors=True)
    return checks


def replay(outcomes, answers):
    """Drive `run_in_place` through planted outcomes and report what it did."""
    queue, replies = list(outcomes), list(answers)
    records, writes, waits = [], [], []

    def runner(arm, trial):
        return dict(queue.pop(0))

    def wait():
        waits.append(True)
        return replies.pop(0)

    saved, sys.stdout = sys.stdout, io.StringIO()
    try:
        carried_on = run_in_place("A", 1, runner, wait, records,
                                  lambda: writes.append(len(records)))
    finally:
        sys.stdout = saved
    return {"carried_on": carried_on, "records": records, "writes": writes,
            "waits": len(waits),
            "outcomes": [record["outcome"] for record in records]}


def resume_checks():
    """A blocked trial re-runs once in its place; the run stops when it must."""
    checks = []
    names = ["%s%d" % pair for pair in pending_trials("ABC", 3, "B2")]
    checks.append(("--from B2 starts there and keeps the order",
                   names == ["B2", "C2", "A3", "B3", "C3"]))
    try:
        pending_trials("ABC", 3, "D1")
        checks.append(("--from an unknown trial refuses", False))
    except TrialError:
        checks.append(("--from an unknown trial refuses", True))

    blocked = {"outcome": "blocked", "reason": "planted",
               "void": {"dir": os.path.join("void", "A1-planted")}}
    completed = {"outcome": "completed"}

    rerun = replay([blocked, completed], [True])
    checks.append(("a blocked trial re-runs in its place",
                   rerun["carried_on"]
                   and rerun["outcomes"] == ["blocked", "completed"]))
    checks.append(("the re-run names the trial it substitutes",
                   rerun["records"][-1].get("substitutes")
                   == blocked["void"]["dir"]))
    checks.append(("the record is written after every trial",
                   rerun["writes"] == [1, 2]))

    twice = replay([blocked, blocked], [True])
    checks.append(("a second block stops the run", not twice["carried_on"]
                   and twice["outcomes"] == ["blocked", "blocked"]))

    unanswered = replay([blocked], [False])
    checks.append(("no answer stops the run", not unanswered["carried_on"]
                   and unanswered["waits"] == 1))

    unmoved = replay([dict(blocked, void=None, void_error="planted")], [])
    checks.append(("a workspace that could not move stops the run",
                   not unmoved["carried_on"] and unmoved["waits"] == 0))

    clock = [0.0]

    def sleep(seconds):
        clock[0] += seconds

    replies = [TrialError("planted"), TrialError("planted"), None]

    def probe():
        reply = replies.pop(0)
        if reply is not None:
            raise reply

    def refuse():
        raise TrialError("planted")

    saved, sys.stdout = sys.stdout, io.StringIO()
    try:
        answered = wait_for_generator(probe, 60, 600, sleep=sleep,
                                      clock=lambda: clock[0])
        answered_at = clock[0]
        clock[0] = 0.0
        gave_up = wait_for_generator(refuse, 60, 180, sleep=sleep,
                                     clock=lambda: clock[0])
    finally:
        sys.stdout = saved
    checks.append(("probing stops when the generator answers",
                   answered and answered_at == 180))
    checks.append(("probing gives up at its limit",
                   not gave_up and clock[0] == 180))
    return checks


def self_test():
    """Prove the environment, outcome and resume rules before any trial."""
    checks = environment_checks() + outcome_checks() + resume_checks()
    for label, ok in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED"))
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run efficacy-benchmark trials.")
    parser.add_argument("--root",
                        help="where workspaces are created; MUST be outside "
                             "this repository. Required for everything but "
                             "--self-test")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the environment, outcome and resume "
                             "rules; run no trial")
    parser.add_argument("--arms", default="ABC",
                        help="which arms to run, as letters (default ABC)")
    parser.add_argument("--k", type=int, default=3,
                        help="trials per arm (default 3, the pre-registered K)")
    parser.add_argument("--model", default="claude-sonnet-5",
                        help="exact generator model id, recorded in the report")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--budget", type=float, default=BUDGET_USD,
                        help="dollar ceiling per trial, read against the "
                             "CLI's own cost figure (default %s, the design's)"
                        % BUDGET_USD)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_S,
                        help="wall-clock ceiling per trial, in seconds "
                             "(default %s, the design's)" % TIMEOUT_S)
    parser.add_argument("--from", dest="start",
                        help="start at this trial in the interleaved order, "
                             "as B2")
    parser.add_argument("--resume-after-block", action="store_true",
                        help="after a blocked trial, probe until the "
                             "generator answers and re-run it in its place")
    parser.add_argument("--probe-every", type=float, default=30,
                        help="minutes between probes while blocked")
    parser.add_argument("--give-up-after", type=float, default=12,
                        help="hours of probing before the run stops")
    parser.add_argument("--dry-run", action="store_true",
                        help="prepare the workspaces and print the command; "
                             "call no model")
    return parser.parse_args(argv)


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    # A refused root is a finding about the run, so it is reported and
    # exits, rather than reaching the caller as a traceback.
    try:
        assert_outside_repository(options.root)
    except TrialError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 trial(s), 0 done, 1 refused")
        return 1

    os.makedirs(options.root, exist_ok=True)
    home = prepare_home(options.root)

    arms = list(options.arms.upper())
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        print("unknown arm(s): %s" % ", ".join(unknown))
        return 2
    try:
        pending = pending_trials(arms, options.k, options.start)
    except TrialError as error:
        print("refused: %s" % error)
        return 2

    # One call before the first trial, because the CLI answers an
    # unauthenticated run with a result object rather than a crash: without
    # this, a whole run completes having never reached a model. A dry run
    # calls nothing by definition and is exempt.
    if not options.dry_run:
        try:
            ready = assert_authenticated(home, agent_environment,
                                         agent_executable())
        except (TrialError, subprocess.TimeoutExpired) as error:
            print("refused: %s" % error)
            lib.print_verdict(False, "0 trial(s), 0 done, 1 refused")
            return 1
        print("generator ready: %s" % ready)

    started_at = datetime.datetime.now()
    run_file = os.path.join(
        options.root, "run-%s.json" % started_at.strftime("%Y-%m-%dT%H-%M-%S"))
    records = []

    def runner(arm, trial):
        return run_trial(arm, trial, options.root, home, options)

    def write():
        write_run(run_file, started_at, records)

    def probe():
        return assert_authenticated(home, agent_environment,
                                    agent_executable())

    def wait():
        if not options.resume_after_block:
            print("  --resume-after-block was not given")
            return False
        return wait_for_generator(probe, options.probe_every * 60,
                                  options.give_up_after * 3600)

    finished = all(run_in_place(arm, trial, runner, wait, records, write)
                   for arm, trial in pending)
    write()
    print("\nRun record: %s" % run_file)

    refused = sum(1 for r in records if r["outcome"] == "refused")
    blocked = sum(1 for r in records if r["outcome"] == "blocked")
    done = sum(1 for r in records if r["outcome"]
               in ("completed", "budget", "timeout", "dry-run"))
    lib.print_verdict(refused == 0 and finished,
                      "%d trial(s), %d done, %d blocked, %d refused%s"
                      % (len(records), done, blocked, refused,
                         "" if finished else ", run stopped"))
    return 0 if refused == 0 and finished else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
