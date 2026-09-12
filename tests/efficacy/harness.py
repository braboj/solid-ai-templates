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


def agent_environment(home):
    """The environment a trial runs under, isolated from this machine."""
    env = dict(os.environ)
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
        record["outcome"] = "completed" if proc.returncode == 0 else "failed"
        record["exit_status"] = proc.returncode
        record["stdout"] = proc.stdout
        record["stderr"] = proc.stderr[-4000:]
        try:
            record["result"] = json.loads(proc.stdout)
        except ValueError:
            record["result"] = None
    except subprocess.TimeoutExpired:
        record["outcome"] = "timeout"
        record["exit_status"] = None

    record["elapsed_s"] = round(time.monotonic() - started, 1)
    record["frozen"] = freeze(workspace, root, "%s%d" % (arm, trial))
    return record


def order(arms, k):
    """Interleave the trials: A1, B1, C1, A2, ...

    A model-side change part-way through a run then lands across the arms
    rather than on one of them, which is the confound the design names.
    """
    return [(arm, trial) for trial in range(1, k + 1) for arm in arms]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run efficacy-benchmark trials.")
    parser.add_argument("--root", required=True,
                        help="where workspaces are created; MUST be outside "
                             "this repository")
    parser.add_argument("--arms", default="ABC",
                        help="which arms to run, as letters (default ABC)")
    parser.add_argument("--k", type=int, default=3,
                        help="trials per arm (default 3, the pre-registered K)")
    parser.add_argument("--model", default="claude-sonnet-5",
                        help="exact generator model id, recorded in the report")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--budget", type=float, default=None,
                        help="dollar ceiling per trial")
    parser.add_argument("--timeout", type=int, default=7200,
                        help="wall-clock ceiling per trial, in seconds")
    parser.add_argument("--dry-run", action="store_true",
                        help="prepare the workspaces and print the command; "
                             "call no model")
    return parser.parse_args(argv)


def main(argv):
    options = parse_args(argv)

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

    started_at = datetime.datetime.now()
    records = []
    for arm, trial in order(arms, options.k):
        print("%s%d  %s" % (arm, trial, ARMS[arm]["label"]))
        try:
            record = run_trial(arm, trial, options.root, home, options)
        except TrialError as error:
            print("  refused: %s" % error)
            records.append({"arm": arm, "trial": trial, "outcome": "refused",
                            "error": str(error)})
            continue
        print("  %s in %ss" % (record["outcome"],
                               record.get("elapsed_s", 0)))
        records.append(record)

    run_file = os.path.join(
        options.root, "run-%s.json" % started_at.strftime("%Y-%m-%dT%H-%M-%S"))
    with io.open(run_file, "w", encoding="utf-8") as handle:
        json.dump({"started_at": started_at.isoformat(timespec="seconds"),
                   "prompt": PROMPT, "trials": records}, handle, indent=2)
    print("\nRun record: %s" % run_file)

    refused = sum(1 for r in records if r["outcome"] == "refused")
    done = sum(1 for r in records if r["outcome"] in ("completed", "dry-run"))
    lib.print_verdict(refused == 0,
                      "%d trial(s), %d done, %d refused"
                      % (len(records), done, refused))
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
