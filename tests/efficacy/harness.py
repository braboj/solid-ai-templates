"""Set up and run one efficacy-benchmark trial.

The design, its question and its verdict rule live in
`docs/design/efficacy-benchmark.md`. This module owns section 4 of it: the
workspace an arm starts from, the isolated configuration it runs under, the
one prompt every arm receives, and the freeze that ends a trial.

Scoring is not here. A trial produces a frozen workspace and a record; the
hidden suite and the graders read them afterwards.
"""

import argparse
import contextlib
import datetime
import glob
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time

# This module sits a level below the other runners, so the shared library
# is reached by path rather than as a sibling.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "SPEC.md")
ARMS_DIR = os.path.join(HERE, "arms")

# The change task's prompt lives in a file of its own, the one copy the
# design links to. A copy restated in code could drift from it, and a prompt
# found by a heading in the design breaks when the design is restructured.
CHANGE_PROMPT = os.path.join(HERE, "change-prompt.txt")

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

# K as the design fixes it, and the ceiling of the design's one escalation. No run
# goes past the ceiling, because sampling until an interval clears zero is the
# failure the bound exists to prevent.
K_PRIMARY = 3
K_CEILING = 5

# The release every generated arm is produced from, and the one the hybrid
# arm's vendored templates are taken at. The design fixes it: the last 2.x,
# before the v3.0 split moves any template.
RELEASE = "v2.90.0"

# What the hybrid arm's workspace carries besides its file: this repository's
# `templates/` directory at the release, where a submodule would put it. The
# rest of the repository stays out, because the release's tree holds the
# benchmark's own design and the arm would be reading its brief.
VENDORED = {"ref": RELEASE, "path": "templates",
            "into": "docs/solid-ai-templates"}

# The arms, each a word, and the context file each starts with, relative to
# `arms/`. Arm `none` carries no file: it is the bare agent. The two files
# round 1 ran keep the directories its generation record names.
ARMS = {
    "none": {"label": "no context file", "context": None},
    "full": {"label": "the templates' file, inline",
             "context": "full/CLAUDE.md"},
    "short": {"label": "the templates' file, 40 lines",
              "context": "short/CLAUDE.md"},
    "hybrid": {"label": "the templates' file, hybrid",
               "context": "hybrid/CLAUDE.md", "vendor": VENDORED},
    "hand": {"label": "the hand-written file",
             "context": "hand/CLAUDE.md"},
}

# Round 1 named its arms by letter and its trials `A1`, `B2`, `C3`. Its run
# records, tarballs, scores and judgings keep those spellings, and every
# reader turns them into the words, so the round is never rewritten on disk.
ROUND_ONE = {"A": "none", "B": "full", "C": "hand"}
ROUND_ONE_NAME = re.compile(r"^([A-Z])(\d+)$")


def arm_name(raw):
    """An arm as its word, whether a record names it by word or by round 1's
    letter."""
    return ROUND_ONE.get(raw, raw)


def trial_name(arm, block):
    """A trial's name: the arm's word, a hyphen, the block it runs in."""
    return "%s-%d" % (arm, int(block))


def split_name(name):
    """A trial name as (arm, block), round 1's letters read as their words.

    The block is the last hyphenated part, so an arm's word never carries a
    hyphen of its own.
    """
    match = ROUND_ONE_NAME.match(name)
    if match and match.group(1) in ROUND_ONE:
        return ROUND_ONE[match.group(1)], int(match.group(2))
    arm, _, block = name.rpartition("-")
    if not arm or not block.isdigit():
        raise TrialError("%r is not a trial name; one reads as `full-1`, the "
                         "arm's word and its block" % name)
    return arm, int(block)


def canonical(name):
    """A trial name in the form the arms are named today, `none-1` for `A1`."""
    return trial_name(*split_name(name))


def round_one_name(name):
    """Round 1's spelling of a trial name, `B1` for `full-1`, or None where
    the arm was not in round 1."""
    arm, block = split_name(name)
    letters = {word: letter for letter, word in ROUND_ONE.items()}
    return "%s%d" % (letters[arm], block) if arm in letters else None


def spellings(name):
    """Every name a trial's files may be filed under: its canonical name
    and, for a round 1 arm, its letter."""
    return [spelled for spelled in (canonical(name), round_one_name(name))
            if spelled]


def name_of(record):
    """The trial a run record or a score describes, by canonical name."""
    return trial_name(arm_name(record.get("arm")), record.get("trial"))

# Web access is the confound the design names: an arm that reads the
# templates online is not the arm being measured. The two web tools are
# disallowed; the shell keeps its network, because every trial installs
# packages, so a fetch through it shows only in the transcript.
DISALLOWED_TOOLS = ["WebSearch", "WebFetch"]

# What a tool call names when a trial reaches for what no arm may read: this
# repository, which a generated file names in its footer, and the private
# hidden suite under any clone's name, the scorer's own included.
REACH_TERMS = ("solid-ai-templates", "hidden-suite")

# The hybrid arm's workspace carries the templates by design, so a call
# naming that tree is the arm reading its own file. For it the repository is
# reached only under an owner's name, which no path into the vendored copy
# carries and every clone or fetch of the repository does. The repository
# moved organisation and the host redirects the old name, so a fetch under
# either owner reaches it and both are terms.
REPOSITORY_TERMS = ("solid-ai-dev/solid-ai-templates",
                    "braboj/solid-ai-templates")

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


# A trial's workspace is created inside the run root, so whatever scoring wrote
# there, the hidden suite's clone and every scored trial's extracted code among
# it, would sit one `..` away from the next trial.
def scoring_area(root):
    """The directory beside a run root that scoring and judging write to."""
    return os.path.abspath(root).rstrip("\\/") + "-scoring"


def dry_run_area(root):
    """The directory beside a run root that a dry run prepares in."""
    return os.path.abspath(root).rstrip("\\/") + "-dry-run"


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


def vendor_templates(workspace, vendor):
    """Put this repository's templates at the release into the workspace,
    where a submodule would, and return the record of what was vendored.

    The copy is kept out of the workspace's index through `.git/info/exclude`
    rather than a `.gitignore`: it is the arm's reading matter, not its
    output, so it must count in no size or scope metric; a submodule would
    add one entry, and the agent may rewrite a `.gitignore` at will.
    """
    target = os.path.join(workspace, *vendor["into"].split("/"))
    os.makedirs(target, exist_ok=True)
    proc = subprocess.run(["git", "-C", repository_root(), "archive",
                           "--format=tar", vendor["ref"], vendor["path"]],
                          capture_output=True)
    if proc.returncode != 0:
        raise TrialError("could not export %s at %s: %s"
                         % (vendor["path"], vendor["ref"],
                            proc.stderr.decode("utf-8", "replace").strip()))
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as archive:
        archive.extractall(target, filter="data")
    tree = subprocess.run(["git", "-C", repository_root(), "rev-parse",
                           "%s:%s" % (vendor["ref"], vendor["path"])],
                          capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()
    exclude = os.path.join(workspace, ".git", "info", "exclude")
    os.makedirs(os.path.dirname(exclude), exist_ok=True)
    with io.open(exclude, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("/%s/\n" % vendor["into"])
    return dict(vendor, tree=tree)


def prepare_workspace(arm, trial, root):
    """Create the starting workspace for one trial; return its path and the
    record of what was vendored into it, None for every arm but the hybrid.

    Fresh directory, `git init`, the arm's starting files, one commit. The
    commit is what the freeze at the end of the trial is measured against:
    without it, a trial that wrote nothing looks the same as one whose work
    was never committed.
    """
    if arm not in ARMS:
        raise TrialError("unknown arm %r; the arms are %s"
                         % (arm, ", ".join(sorted(ARMS))))
    workspace = os.path.join(root, trial_name(arm, trial))
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
                "arm %s needs %s, which does not exist. A generated file is "
                "produced through the interview at the recorded release, "
                "never hand-written." % (arm, source))
        shutil.copyfile(source, os.path.join(workspace, "CLAUDE.md"))

    git(workspace, "init", "-q")
    vendored = None
    if ARMS[arm].get("vendor"):
        vendored = vendor_templates(workspace, ARMS[arm]["vendor"])
    git(workspace, "add", "-A")
    git(workspace, "-c", "user.name=efficacy",
        "-c", "user.email=efficacy@example.invalid",
        "commit", "-q", "-m", "start: %s arm %s" % (ARMS[arm]["label"], arm))
    return workspace, vendored


# The one thing the scratch home must inherit. Credentials live under the
# real home, so a fully scratch home authenticates as nobody and every
# trial dies on "Not logged in" — which the CLI reports as a successful
# result with `is_error` set, so it reads like a model answer rather than
# a failure to run.
CREDENTIALS = os.path.join(".claude", ".credentials.json")


def refresh_credentials(home):
    """Give the scratch home the account's live credentials; say how.

    A hard link to the real file rather than a copy. Another client of the
    account — a parallel session starting on this machine — rotates the
    tokens, and a snapshot taken before that holds a revoked token: one
    ended a trial eighteen minutes in. Through the link a rotation written
    in place reaches the trial's CLI as it happens. Where no link can be
    made the file is copied, and the copy is taken again before every
    trial and every probe, so at worst a trial starts fresh.
    """
    source = os.path.join(os.path.expanduser("~"), CREDENTIALS)
    target = os.path.join(home, CREDENTIALS)
    if not os.path.exists(source):
        return None
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.lexists(target):
        os.remove(target)
    try:
        os.link(source, target)
        return "linked"
    except OSError:
        shutil.copyfile(source, target)
        return "copied"


def prepare_home(root):
    """Create the scratch home every trial runs under, and return it.

    One home for the whole run rather than one per trial: it holds no trial
    state, and a single directory is one thing to assert about.

    Everything the design's isolation names is absent by construction —
    no global `CLAUDE.md`, no hooks, no auto-memory, no MCP — because the
    directory is new. The credential file is linked in, and nothing else
    is: it carries no context, and without it there is no run at all.
    """
    home = os.path.join(root, "home")
    os.makedirs(os.path.join(home, ".claude"), exist_ok=True)
    settings = os.path.join(home, "settings.json")
    with io.open(settings, "w", encoding="utf-8") as handle:
        json.dump(ISOLATED_SETTINGS, handle)
    refresh_credentials(home)
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


# A credential helper the machine configures answers any Git that asks, and
# the private hidden suite is one authenticated clone away. An empty helper,
# set the way `git -c` sets one, clears every helper configured before it;
# a Git that cannot prompt then fails rather than waits.
GIT_WITHOUT_CREDENTIALS = {
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": "credential.helper",
    "GIT_CONFIG_VALUE_0": "",
    "GIT_TERMINAL_PROMPT": "0",
    "GCM_INTERACTIVE": "never",
}

# The names a temporary directory is read from, on Windows and elsewhere.
TEMP_NAMES = ("TEMP", "TMP", "TMPDIR")


def agent_environment(home, environ=None, temp=None):
    """The environment a trial runs under: this machine's, minus the caller's.

    `temp`, where given, is the trial's own temporary directory.
    """
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
    env.update(GIT_WITHOUT_CREDENTIALS)
    if temp:
        env.update((name, temp) for name in TEMP_NAMES)
    return env


def agent_command(home, model, effort, budget):
    """The argv for one trial; the prompt goes on standard input.

    `--max-turns`, which the design's protocol names, is not a flag this
    CLI carries. The bound is a dollar budget and the wall-clock timeout the
    caller applies, and the record states which of them ended a trial.
    """
    argv = [
        agent_executable(), "-p",
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


def frozen_top(tarball, unpacked):
    """The one top-level directory a frozen tarball unpacked to.

    A workspace is frozen under the trial's name as spelled on the day, so a
    tarball round 1 froze as `B1` unpacks to `B1` whatever the trial is
    called now, and the reader takes the directory it finds.
    """
    entries = os.listdir(unpacked)
    if len(entries) != 1 or not os.path.isdir(os.path.join(unpacked,
                                                           entries[0])):
        raise TrialError("%s did not unpack to one directory: %s"
                         % (tarball, ", ".join(entries) or "nothing"))
    return entries[0]


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


def project_folder(workspace):
    """The folder the CLI files a workspace's sessions under."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(workspace))


def transcript_files(home, workspace, since=None):
    """The transcripts the CLI wrote for a session run in `workspace`, left
    out where last written before `since`.

    The CLI files a session under its working directory with every character
    other than a letter or digit replaced by a hyphen.
    """
    files = sorted(glob.glob(os.path.join(home, ".claude", "projects",
                                          project_folder(workspace),
                                          "*.jsonl")))

    # A voided trial re-runs in the same workspace, so its folder also holds
    # the voided attempt's transcripts. Those stopped being written before the
    # re-run started, and a scan charging them to the re-run reports calls it
    # never made.
    if since is None:
        return files
    return [file for file in files if os.path.getmtime(file) >= since]


def tool_calls(files):
    """Every tool call in the transcripts, as (tool, input as JSON text)."""
    calls = []
    for file in files:
        with io.open(file, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict):
                    continue
                content = (entry.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                calls.extend(
                    (block.get("name"),
                     json.dumps(block.get("input"), ensure_ascii=False))
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") == "tool_use")
    return calls


def read_transcripts(home, workspace, since=None):
    """A trial's transcript files and every tool call in them."""
    files = transcript_files(home, workspace, since)
    return files, tool_calls(files)


def reach(files, calls, workspace=None, temp=None, vendored=None):
    """The tool calls naming this repository or the hidden suite and, given
    the trial's workspace, the scoring area or any part of the run root other
    than the trial's own workspace and temporary directory.

    Only what the agent sent is read, never what came back: a generated file
    names this repository, and reading it is not reaching for it. A trial
    whose workspace carries the templates (`vendored`) names them in every
    read, so for it the repository counts as reached only under its owner's
    name. With no transcript the hits are None rather than empty, because
    nothing scanned and nothing found are opposite facts.
    """
    if not files:
        return {"transcripts": [], "hits": None}
    terms, outside = list(REACH_TERMS), None
    if vendored:
        terms = [owned for term in terms
                 for owned in (REPOSITORY_TERMS
                               if term == "solid-ai-templates" else (term,))]
    if workspace:
        root = os.path.dirname(os.path.abspath(workspace))
        terms.append(os.path.basename(scoring_area(root)).lower())
        outside = outside_pattern(workspace, temp)
    hits = []
    for tool, text in calls:
        lowered = text.lower()
        hits.extend({"tool": tool, "term": term, "call": text[:300]}
                    for term in terms if term in lowered)
        if outside is None:
            continue

        # A call's input arrives as JSON, which doubles a Windows path's
        # backslashes; both spellings become forward slashes.
        normal = lowered.replace("\\\\", "/").replace("\\", "/")
        hits.extend({"tool": tool, "term": match.group(0),
                     "call": text[:300]}
                    for match in outside.finditer(normal))
    return {"transcripts": files, "hits": hits}


# Where a path ends on a command line: the end of the text, a separator, a
# space, a quote or a list delimiter.
PATH_END = "(?=$|[/\\s\"';,])"


def path_forms(paths):
    """Each path lowercased with forward slashes, in its Windows form and its
    Git Bash `/c/` form."""
    forms = set()
    for path in paths:
        full = os.path.abspath(path).replace("\\", "/").lower().rstrip("/")
        forms.add(full)
        if len(full) > 1 and full[1] == ":":
            forms.add("/%s%s" % (full[0], full[2:]))
    return sorted(forms)


def path_pattern(paths):
    """A pattern matching any of `paths` the way a command line spells it.

    It ends where the path does, so `A1` matches neither `A10` nor `A1.tar`.
    """
    return re.compile("(?:%s)%s" % (
        "|".join(re.escape(form) for form in path_forms(paths)), PATH_END))


def outside_pattern(workspace, temp):
    """A pattern matching a path into the run root other than the trial's own
    workspace or temporary directory, as normalised by `reach`."""
    workspace = os.path.abspath(workspace)
    root = os.path.dirname(workspace)
    own = [re.escape(os.path.basename(workspace).lower())]
    if temp:
        name = os.path.basename(os.path.abspath(temp)).lower()
        own.append("tmp/" + re.escape(name))

    # A sentence can end on the trial's own path, as in "the repo at
    # ...\A1. I need", so punctuation before the path ends still leaves it
    # the trial's own, and so does a pip extra, as in `pip install
    # "...\hybrid-2[dev]"`. A suffix is not punctuation: `A1.tar` stays
    # another entry of the root.
    not_own = "(?!(?:%s)(?:\\[[^\\]/\\s\"';,]*\\])?[.:!?)\\]]*%s)" % (
        "|".join(own), PATH_END)
    forms = "|".join(re.escape(form) for form in path_forms([root]))

    # The root itself, whose listing names every other trial, and any entry
    # of it named from the root. The entries hold earlier trials' workspaces,
    # their tarballs, and the shared home with every transcript.
    alternatives = ["(?:%s)/?(?=$|[\\s\"';,])" % forms,
                    "(?:%s)/%s[^/\\s\"';,]+" % (forms, not_own)]

    # An entry of the root climbed to from inside the workspace.
    entries = (sorted(entry.lower() for entry in os.listdir(root))
               if os.path.isdir(root) else [])
    if entries:
        alternatives.append("\\.\\./%s(?:%s)%s" % (
            not_own, "|".join(re.escape(entry) for entry in entries),
            PATH_END))
    return re.compile("|".join(alternatives))


def process_table():
    """Every running process, as (pid, executable, command line)."""
    if os.name == "nt":
        script = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
                  "Get-CimInstance Win32_Process | Select-Object ProcessId, "
                  "ExecutablePath, CommandLine | ConvertTo-Json -Compress")
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120)
        rows = json.loads(proc.stdout or "[]")
        if isinstance(rows, dict):
            rows = [rows]
        return [(row["ProcessId"], row.get("ExecutablePath") or "",
                 row.get("CommandLine") or "") for row in rows]
    proc = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120)
    table = []
    for line in proc.stdout.splitlines():
        pid, _, command = line.strip().partition(" ")
        if pid.isdigit():
            table.append((int(pid), "", command))
    return table


def stop_processes(paths, table=None):
    """Stop every process running from one of `paths`; return what stopped.

    A server the agent started in the background outlives the CLI, holds its
    files open, and answers on a port the next trial may choose.
    """
    pattern = path_pattern(paths)
    spared = {os.getpid(), os.getppid()}
    stopped = []
    for pid, executable, command in (process_table() if table is None
                                     else table):
        text = ("%s %s" % (executable, command)).replace("\\", "/").lower()
        if pid in spared or not pattern.search(text):
            continue

        # A process the tree kill already took is not an error.
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, timeout=60)
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        stopped.append({"pid": pid, "command": (command or executable)[:300]})
    return stopped


class LiveRunError(Exception):
    """Another run of the same tool is live against the same scoring area."""


def claim_path(area, tool):
    """Where a run of `tool` marks `area` as in use."""
    return os.path.join(area, "%s.running" % os.path.splitext(tool)[0])


def read_claim(path):
    """The run a marker names, or None when it holds no readable record."""
    try:
        with io.open(path, encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, ValueError):
        return None
    return record if isinstance(record.get("pid"), int) else None


def running_as(pid, tool):
    """Whether process `pid` is running and its command line names `tool`.

    The command line is read as well as the pid, because an ended run's pid
    is soon reused by some other process, and that process holds nothing.
    """
    table = process_table()

    # A listing that cannot see this process cannot see any other either, and
    # read as empty it would call every live run ended.
    if not any(listed == os.getpid() for listed, _, _ in table):
        raise LiveRunError("the process listing does not show this run, so "
                           "whether another is live cannot be told")
    named = re.compile(r"(?:^|[\\/\s\"'])%s(?:$|[\s\"'])" % re.escape(tool),
                       re.IGNORECASE)
    return any(listed == pid and named.search(command or "")
               for listed, _, command in table)


def claim_area(area, tool):
    """Mark `area` as in use by this run of `tool`; return the marker's path.

    Every tool clears a trial's working directory before rebuilding it, so a
    second run against the same area deletes what the first is reading. A
    marker naming a live run of `tool` refuses this one. A marker whose
    process has ended, or whose pid now belongs to something else, is taken
    over, so a run that crashed does not hold the area for good.
    """
    os.makedirs(area, exist_ok=True)
    path = claim_path(area, tool)
    record = {"pid": os.getpid(), "tool": tool, "argv": sys.argv,
              "started": datetime.datetime.now().isoformat(timespec="seconds")}

    # Two attempts: the second follows a takeover, and failing it means
    # another run took the area over in between.
    for _ in range(2):
        try:
            handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            holder = read_claim(path)
            if holder is None:
                raise LiveRunError("%s names no run; remove it if no %s run "
                                   "is live" % (path, tool))
            if running_as(holder["pid"], tool):
                raise LiveRunError("a %s run is live against %s: pid %d, "
                                   "started %s" % (tool, area, holder["pid"],
                                                   holder.get("started")))
            print("taking over %s: pid %d, started %s, is no longer a %s run"
                  % (path, holder["pid"], holder.get("started"), tool))
            try:
                os.remove(path)
            except FileNotFoundError:
                pass
            continue
        with io.open(handle, "w", encoding="utf-8") as out:
            json.dump(record, out)
        return path
    raise LiveRunError("another %s run claimed %s during the takeover"
                       % (tool, area))


def release_area(path):
    """Remove this run's marker, and leave one another run holds."""
    holder = read_claim(path)
    if holder is not None and holder["pid"] == os.getpid():
        os.remove(path)


def created_at(path):
    """When a file or directory was created, or last changed where the
    platform records no creation time."""
    stat = os.stat(path)
    return getattr(stat, "st_birthtime", stat.st_ctime)


def shared_leftovers(shared, since, calls):
    """What a trial left in the machine's temporary directory, by name.

    Git Bash maps `/tmp` to that directory whatever `TEMP` says, so a trial
    writing to `/tmp` by name bypasses its own. An entry counts only when it
    appeared after the trial started and a tool call names it, because other
    programs write there too.
    """
    named = "\n".join(text.lower() for _, text in calls)
    found = []
    for entry in sorted(os.listdir(shared)) if os.path.isdir(shared) else []:
        try:
            if created_at(os.path.join(shared, entry)) < since:
                continue
        except OSError:
            continue
        if re.search(r"(?<![\w.-])%s(?![\w.-])" % re.escape(entry.lower()),
                     named):
            found.append(entry)
    return found


def gather_leftovers(shared, entries, target):
    """Move the entries from `shared` under `target`; return where each went."""
    moved = []
    for entry in entries:
        source = os.path.join(shared, entry)
        destination = os.path.join(target, entry)
        try:
            os.makedirs(target, exist_ok=True)
            shutil.move(source, destination)
            moved.append({"from": source, "to": destination})
        except OSError as error:
            moved.append({"from": source, "to": None, "error": str(error)})
    return moved


def contain(workspace, temp, home, shared, since, vendored=None):
    """Close a finished trial off from the next one; say what it left.

    Processes are stopped before anything moves, because a running process
    holds its files open.
    """
    files, calls = read_transcripts(home, workspace, since)
    leftovers = shared_leftovers(shared, since, calls)
    owned = [workspace, temp, home] + [os.path.join(shared, entry)
                                       for entry in leftovers]
    result = {"reach": reach(files, calls, workspace, temp, vendored),
              "shared_temp_dir": shared}
    try:
        result["stopped"] = stop_processes(owned)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result["stopped"], result["stop_error"] = None, str(error)
    result["shared_temp"] = gather_leftovers(shared, leftovers,
                                             os.path.join(temp, "shared"))
    return result


def read_input(path):
    """A pinned input's text, stripped; refused where the file is empty."""
    try:
        with io.open(path, encoding="utf-8") as handle:
            text = handle.read().strip()
    except OSError as error:
        raise TrialError("cannot read %s: %s" % (path, error))
    if not text:
        raise TrialError("%s is empty" % path)
    return text


def read_change_prompt(path=CHANGE_PROMPT):
    """The change task's prompt, as the design pins it."""
    return read_input(path)


def prepare_change_workspace(arm, trial, root, build):
    """Unpack a build trial's frozen workspace for its change task.

    Returns the workspace and the commit its starting state is recorded in.
    """
    name = "change-%s" % trial_name(arm, trial)
    workspace = os.path.join(root, name)
    if os.path.exists(workspace):
        raise TrialError("workspace %s already exists; a trial never reuses "
                         "one" % workspace)
    tarball = (build.get("frozen") or {}).get("tarball")
    if not tarball or not os.path.isfile(tarball):
        raise TrialError("build trial %s left no frozen tarball at %s"
                         % (trial_name(arm, trial), tarball))

    # Unpacked beside the workspace and renamed, because the tarball's top
    # directory carries the build trial's name as it was spelled when frozen,
    # not the change task's.
    unpacking = os.path.join(root, ".unpacking-%s" % name)
    shutil.rmtree(unpacking, ignore_errors=True)
    try:
        with tarfile.open(tarball) as archive:
            archive.extractall(unpacking, filter="data")
        shutil.move(os.path.join(unpacking, frozen_top(tarball, unpacking)),
                    workspace)
    except (OSError, tarfile.TarError) as error:
        raise TrialError("could not unpack %s: %s" % (tarball, error))
    finally:
        shutil.rmtree(unpacking, ignore_errors=True)

    # What the build trial left uncommitted is part of the starting state, so
    # it is committed here and churn counts only what the change adds.
    git(workspace, "add", "-A")
    git(workspace, "-c", "user.name=efficacy",
        "-c", "user.email=efficacy@example.invalid",
        "commit", "-q", "--allow-empty", "-m",
        "start: change task, %s arm %s" % (ARMS[arm]["label"], arm))
    return workspace, git(workspace, "rev-parse", "HEAD")


def run_trial(arm, trial, root, home, options):
    """Run one build trial and return its record."""
    workspace, vendored = prepare_workspace(arm, trial, root)
    record = {"arm": arm, "label": ARMS[arm]["label"], "trial": trial,
              "task": "build", "vendored": vendored}
    return run_agent(workspace, trial_name(arm, trial), PROMPT, record, root,
                     home, options)


def run_change_trial(arm, trial, root, home, options, build):
    """Run one change task on a copy of its build trial; return its record."""
    workspace, base = prepare_change_workspace(arm, trial, root, build)
    record = {"arm": arm, "label": ARMS[arm]["label"], "trial": trial,
              "task": "change", "base": base,
              "build_frozen": build.get("frozen"),
              "vendored": build.get("vendored")}
    return run_agent(workspace, "change-%s" % trial_name(arm, trial),
                     read_change_prompt(), record, root, home, options)


# The endings a trial is scored on. A blocked trial was voided and its re-run
# carries the score; a refused one never started.
SCORABLE = ("completed", "budget", "timeout")


def scorable_trials(root, run=None, task="build"):
    """Every trial of `task` the run records offer for scoring, by name."""
    if run:
        files = [run]
    else:
        files = sorted(os.path.join(root, entry)
                       for entry in (os.listdir(root)
                                     if os.path.isdir(root) else [])
                       if entry.startswith("run-") and entry.endswith(".json"))
    if not files:
        raise TrialError("no run record in %s; the harness writes one" % root)
    found, sources = {}, {}
    for file in files:
        with io.open(file, encoding="utf-8") as handle:
            records = json.load(handle).get("trials", [])
        for record in records:
            name = name_of(record)

            # A record written before the change task existed is a build one.
            if record.get("task", "build") != task:
                continue
            if record.get("outcome") not in SCORABLE:
                continue

            # Two records offering one trial means two workspaces for one
            # slot. Picking either would be a choice made after the fact.
            if name in found:
                raise TrialError("%s is offered for scoring by both %s and %s"
                                 % (name, sources[name], file))
            found[name] = record
            sources[name] = file
    return found


# How long the CLI gets to exit after printing its result. It usually exits
# at once; a shell it left running keeps its pipes open, and on Windows the
# `.CMD` shim it runs behind is the process a plain timeout kills, leaving
# the CLI an orphan that holds the pipes for good — which is how round 2's
# `none-3` sat finished for six hours. So the output is watched for the
# result line, and after the grace the whole tree is ended.
RESULT_GRACE_S = 120


def kill_tree(proc):
    """End a process and everything running under it."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True, timeout=60)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()


def result_of(stdout):
    """The CLI's result object in its output, or None."""
    try:
        payload = json.loads(stdout)
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        return payload
    for line in stdout.splitlines():
        if line.startswith("{") and '"result"' in line:
            try:
                payload = json.loads(line)
            except ValueError:
                continue
            if isinstance(payload, dict) and payload.get("type") == "result":
                return payload
    return None


def run_cli(argv, prompt, cwd, env, timeout, grace=RESULT_GRACE_S,
            clock=time.monotonic):
    """Run the CLI on a prompt; return its status, output, errors and how it
    ended: `exited` on its own, `hung` with its result printed and the tree
    ended after the grace, or `timeout` with the tree ended at the bound and
    whatever it printed kept."""
    extra = {} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=cwd, env=env, text=True, encoding="utf-8",
                            errors="replace", **extra)
    out, err, seen = [], [], []

    def read(stream, sink, watch):
        for line in stream:
            sink.append(line)
            if watch and not seen and line.startswith("{") \
                    and result_of(line) is not None:
                seen.append(clock())

    readers = [threading.Thread(target=read, args=(proc.stdout, out, True),
                                daemon=True),
               threading.Thread(target=read, args=(proc.stderr, err, False),
                                daemon=True)]
    for reader in readers:
        reader.start()
    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except OSError:
        pass

    started, ended = clock(), "exited"
    while proc.poll() is None:
        now = clock()
        if now - started > timeout:
            ended = "timeout"
            kill_tree(proc)
            break
        if seen and now - seen[0] > grace:
            ended = "hung"
            kill_tree(proc)
            break
        time.sleep(0.5)
    proc.wait()

    # The pipes close once every holder is gone, which the tree kill sees to.
    for reader in readers:
        reader.join(timeout=120)
    return proc.returncode, "".join(out), "".join(err), ended


def run_agent(workspace, name, prompt, record, root, home, options):
    """Run the agent in a prepared workspace and complete its record.

    The record carries everything the protocol says a trial must report:
    what ran, under which model and configuration, what it cost, how long
    it took, and the frozen state it left.
    """
    assert_no_ambient_context(workspace, home)
    argv = agent_command(home, options.model, options.effort, options.budget)
    record.update({
        "workspace": workspace,
        "prompt": prompt,
        "command": argv,
        "model": options.model,
        "effort": options.effort,
        "budget_usd": options.budget,
        "timeout_s": options.timeout,
        "environment_removed": {"names": inherited_names(os.environ),
                                "path": interpreter_directories(os.environ)},
        "templates_tree": lib.tree_id(),
        "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
    })
    if options.dry_run:
        record["outcome"] = "dry-run"
        return record

    # The trial's own temporary directory, apart from the machine's, which
    # every trial shares. Stamped, because a voided trial re-runs under its
    # own name.
    temp = os.path.join(root, "tmp", "%s-%s" % (
        name, datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")))
    os.makedirs(temp)
    record["temp"] = temp
    shared = tempfile.gettempdir()
    since = time.time()
    started = time.monotonic()

    # On standard input, not as an argument: on Windows the CLI is a `.CMD`
    # shim, and `cmd.exe` expands a `%NAME%` pair inside an argument.
    status, stdout, stderr, ended = run_cli(
        argv, prompt, workspace, agent_environment(home, temp=temp),
        options.timeout)
    record["exit_status"] = status
    record["stdout"] = stdout
    record["stderr"] = stderr[-4000:]
    record["ended"] = ended
    record["result"] = result_of(stdout)
    if ended == "timeout" and record["result"] is None:
        record["outcome"], record["reason"] = "timeout", None
    else:

        # A CLI that printed its result and then had to be ended finished
        # the trial; the status the kill left is not the trial's ending.
        record["outcome"], record["reason"] = classify(
            status if ended == "exited" else 0, record["result"])

    record["elapsed_s"] = round(time.monotonic() - started, 1)
    record.update(contain(workspace, temp, home, shared, since,
                          record.get("vendored")))
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
    """Interleave the trials by block: none-1, short-1, hybrid-1, none-2, ...

    A model-side change part-way through a run then lands across the arms
    rather than on one of them, which is the confound the design names.
    """
    return [(arm, trial) for trial in range(1, k + 1) for arm in arms]


def pending_trials(arms, k, start=None):
    """The interleaved order, from `start` onwards where one is given."""
    if not 1 <= k <= K_CEILING:
        raise TrialError("--k %d is outside 1 to %d: the design escalates once "
                         "to K = %d and never further"
                         % (k, K_CEILING, K_CEILING))
    trials = order(arms, k)
    if start is None:
        return trials
    names = [trial_name(*pair) for pair in trials]
    if start not in names:
        raise TrialError("--from %s is not in this run's order: %s"
                         % (start, ", ".join(names)))
    return trials[names.index(start):]


def write_run(run_file, started_at, records, task="build", prompt=PROMPT):
    """Rewrite the run record with every trial so far."""

    # Written to a sibling and swapped in, so a run killed mid-write leaves
    # the previous record whole rather than half of a new one.
    partial = run_file + ".partial"
    with io.open(partial, "w", encoding="utf-8") as handle:
        json.dump({"started_at": started_at.isoformat(timespec="seconds"),
                   "task": task, "prompt": prompt, "trials": records},
                  handle, indent=2)
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
    name = trial_name(arm, trial)
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
        hits = (record.get("reach") or {}).get("hits")
        if hits:
            print("  REACHED for %s" % ", ".join(sorted({hit["term"]
                                                         for hit in hits})))
        if record.get("stopped"):
            print("  stopped %d process(es) the trial left running"
                  % len(record["stopped"]))
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
    workspace = os.path.join(scratch, "none-1")
    os.makedirs(workspace)
    with io.open(os.path.join(workspace, "partial.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("# partial work\n")
    tarball = os.path.join(scratch, "none-1.tar")
    with io.open(tarball, "wb") as handle:
        handle.write(b"frozen")

    # The plant is read before the move, so an empty void is the function's
    # failure and not a workspace that was never there.
    checks.append(("the workspace to void exists",
                   os.path.isfile(os.path.join(workspace, "partial.py"))
                   and os.path.isfile(tarball)))
    try:
        moved = void(scratch, workspace, {"tarball": tarball}, "none-1")
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
        carried_on = run_in_place("none", 1, runner, wait, records,
                                  lambda: writes.append(len(records)))
    finally:
        sys.stdout = saved
    return {"carried_on": carried_on, "records": records, "writes": writes,
            "waits": len(waits),
            "outcomes": [record["outcome"] for record in records]}


def resume_checks():
    """A blocked trial re-runs once in its place; the run stops when it must."""
    checks = []
    arms = ["none", "short", "hybrid"]
    names = [trial_name(*pair) for pair in pending_trials(arms, 3, "short-2")]
    checks.append(("--from short-2 starts there and keeps the order",
                   names == ["short-2", "hybrid-2", "none-3", "short-3",
                             "hybrid-3"]))
    try:
        pending_trials(arms, 3, "other-1")
        checks.append(("--from an unknown trial refuses", False))
    except TrialError:
        checks.append(("--from an unknown trial refuses", True))
    try:
        pending_trials(arms, K_CEILING + 1)
        checks.append(("a K past the escalation's ceiling refuses", False))
    except TrialError:
        checks.append(("a K past the escalation's ceiling refuses", True))
    first_escalated = trial_name("none", K_PRIMARY + 1)
    names = [trial_name(*pair)
             for pair in pending_trials(arms, K_CEILING, first_escalated)]
    checks.append(("the escalation runs its blocks from none-4",
                   names == ["none-4", "short-4", "hybrid-4", "none-5",
                             "short-5", "hybrid-5"]))

    blocked = {"outcome": "blocked", "reason": "planted",
               "void": {"dir": os.path.join("void", "none-1-planted")}}
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


def remove_tree(path):
    """Delete a directory, including the read-only files git writes."""
    def writable(function, target, _):
        os.chmod(target, 0o700)
        function(target)

    if os.path.exists(path):
        shutil.rmtree(path, onexc=writable)


def change_checks():
    """The change prompt is its file's, whole, and names what the grader
    drives; its workspace starts committed."""
    prompt = read_change_prompt()
    with io.open(CHANGE_PROMPT, encoding="utf-8") as handle:
        whole = handle.read().strip()
    checks = [
        ("the change prompt is read whole from its file",
         prompt == whole
         and prompt.startswith("Add a **spend-threshold** discount")),

        # Round 1's grader drove names the prompt never gave, and its pass
        # rate measured which trials guessed them.
        ("the change prompt names the API and fields the grader drives",
         all(name in prompt for name in (
             "tariff.ThresholdRule", "caps=", "`threshold`", "`minimum`",
             "`caps`", "/invoices/preview"))),
    ]

    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-change-self-test")
    remove_tree(scratch)
    build = os.path.join(scratch, "A1")
    os.makedirs(build)
    git(build, "init", "-q")
    with io.open(os.path.join(build, "app.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("committed = True\n")
    git(build, "add", "-A")
    git(build, "-c", "user.name=efficacy",
        "-c", "user.email=efficacy@example.invalid",
        "commit", "-q", "-m", "build")
    with io.open(os.path.join(build, "draft.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("left_uncommitted = True\n")

    # Frozen under round 1's spelling of the trial, so the change task of
    # `none-1` has to find a top directory named `A1`.
    frozen = freeze(build, scratch, "A1")

    # The plant landed: the build trial ended with work it never committed,
    # which is the state a change task has to take into its starting commit.
    checks.append(("the build trial left uncommitted work",
                   frozen["uncommitted"] == ["?? draft.py"]))
    try:
        workspace, base = prepare_change_workspace("none", 1, scratch,
                                                   {"frozen": frozen})
    except TrialError:
        workspace, base = None, None
    checks.append(("the change workspace unpacks under its own name, from "
                   "a tarball frozen under round 1's",
                   workspace == os.path.join(scratch, "change-none-1")
                   and os.path.isfile(os.path.join(workspace, "draft.py"))))
    checks.append(("its starting state is committed", workspace is not None
                   and git(workspace, "status", "--porcelain") == ""
                   and git(workspace, "rev-parse", "HEAD") == base
                   and base != frozen["head"]))
    try:
        prepare_change_workspace("none", 1, scratch, {"frozen": frozen})
        checks.append(("a change workspace is never reused", False))
    except TrialError:
        checks.append(("a change workspace is never reused", True))
    remove_tree(scratch)
    return checks


def listing(path):
    """Every path under `path`, relative to it, sorted."""
    return sorted(os.path.relpath(os.path.join(base, name), path)
                  for base, dirs, files in os.walk(path)
                  for name in dirs + files)


def dry_run_checks():
    """A dry run leaves the root as it found it, so the run that follows in
    the same root prepares every trial the dry run did.

    The root holds what a change task starts from: a frozen build trial and
    the run record offering it. The generator is a stand-in on `PATH` and the
    home a scratch one, so no real CLI or credential is reached.
    """
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-dry-run-self-test")
    remove_tree(scratch)
    root = os.path.join(scratch, "root")
    build = os.path.join(scratch, "built", "none-1")
    os.makedirs(build)
    os.makedirs(root)
    git(build, "init", "-q")
    with io.open(os.path.join(build, "app.py"), "w",
                 encoding="utf-8") as handle:
        handle.write("built = True\n")
    git(build, "add", "-A")
    git(build, "-c", "user.name=efficacy",
        "-c", "user.email=efficacy@example.invalid",
        "commit", "-q", "-m", "build")
    frozen = freeze(build, root, "none-1")
    write_run(os.path.join(root, "run-planted.json"), datetime.datetime.now(),
              [{"arm": "none", "trial": 1, "task": "build",
                "outcome": "completed", "frozen": frozen}])

    stand_in = os.path.join(scratch, "bin")
    os.makedirs(stand_in)
    claude = os.path.join(stand_in,
                          "claude.cmd" if os.name == "nt" else "claude")
    with io.open(claude, "w", encoding="utf-8") as handle:
        handle.write("@echo off\r\n" if os.name == "nt" else "#!/bin/sh\n")
    os.chmod(claude, 0o755)
    saved = {key: os.environ.get(key) for key in ("PATH", "HOME", "USERPROFILE")}
    os.environ["PATH"] = stand_in + os.pathsep + saved["PATH"]
    os.environ["HOME"] = os.environ["USERPROFILE"] = os.path.join(scratch, "me")

    dry = dry_run_area(root)
    before = listing(root)
    outcomes = []
    try:
        for task, prepared in (("change", "change-none-1"), ("build", "none-1")):
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--root", root, "--arms", "none", "--k", "1",
                             "--task", task, "--dry-run"])
            outcomes.append((task, code == 0
                             and os.path.isdir(os.path.join(dry, prepared)),
                             listing(root) == before))
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    # The run proper prepares in the root, where a workspace a dry run left
    # would refuse it.
    try:
        prepare_change_workspace("none", 1, root, {"frozen": frozen})
        prepare_workspace("none", 1, root)
        followed = True
    except TrialError:
        followed = False
    remove_tree(scratch)
    checks = [("the root holds a frozen build and its run record",
               "none-1.tar" in before and "run-planted.json" in before)]
    for task, prepared, untouched in outcomes:
        checks.append(("a %s dry run prepares beside the root" % task,
                       prepared))
        checks.append(("a %s dry run leaves the root as it was" % task,
                       untouched))
    checks.append(("the run that follows prepares in the same root",
                   followed))
    return checks


def credential_checks():
    """A trial's Git cannot borrow a credential the machine stores."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-credential-self-test")
    remove_tree(scratch)
    os.makedirs(scratch)
    config = os.path.join(scratch, "gitconfig")
    with io.open(config, "w", encoding="utf-8") as handle:
        handle.write('[credential]\n\thelper = "!f() { echo username=planted; '
                     'echo password=planted-secret; }; f"\n')

    # Only the planted helper is configured, so the check neither depends on
    # nor prompts through whatever helper this machine carries.
    planted = dict(os.environ, GIT_CONFIG_GLOBAL=config,
                   GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")

    def answers(env):
        proc = subprocess.run(["git", "credential", "fill"],
                              input="protocol=https\nhost=example.invalid\n\n",
                              env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=60)
        return "planted-secret" in proc.stdout

    temp = os.path.join(scratch, "tmp")
    env = agent_environment(os.path.join(scratch, "home"), planted, temp)
    checks = [("a planted Git helper answers outside a trial",
               answers(planted)),
              ("it does not answer inside one", not answers(env)),
              ("the trial's temp directory is its own",
               all(env.get(name) == temp for name in TEMP_NAMES))]
    remove_tree(scratch)
    return checks


def process_checks():
    """A process running from a trial's directory is stopped, and no other."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-process-self-test")
    owned = os.path.join(scratch, "none-1")
    neighbour = os.path.join(scratch, "none-10")
    sleeper = [sys.executable, "-c", "import time; time.sleep(120)"]
    procs = [subprocess.Popen(sleeper + [os.path.join(where, "server.db")])
             for where in (owned, neighbour)]
    try:

        # Both run and are listed before the stop, so one that ends was
        # stopped rather than never started.
        listed = {pid for pid, _, _ in process_table()}
        started = all(proc.poll() is None and proc.pid in listed
                      for proc in procs)
        stopped = stop_processes([owned])
        try:
            procs[0].wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass
        checks = [("two planted processes run and are listed", started),
                  ("the one running from the trial is stopped",
                   procs[0].poll() is not None),
                  ("one whose path only extends it is not",
                   procs[1].poll() is None),
                  ("the record lists what was stopped",
                   any(entry["pid"] == procs[0].pid for entry in stopped))]
    finally:
        stop_processes([neighbour])
        for proc in procs:
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
    return checks


def planted_run(tool):
    """Start a process that reads as a live run of `tool`: a sleeping
    interpreter whose command line names it."""
    return subprocess.Popen([sys.executable, "-c",
                             "import time; time.sleep(120)", tool])


def plant_claim(area, tool, pid):
    """Write a marker naming `pid` as a run of `tool`; return its path."""
    path = claim_path(area, tool)
    os.makedirs(area, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump({"pid": pid, "tool": tool, "started": "planted"}, handle)
    return path


def claimed(area, tool):
    """The marker's path when claiming `area` for `tool` succeeds, or None
    when it is refused."""
    try:
        return claim_area(area, tool)
    except LiveRunError:
        return None


def claimed_pid(path):
    """The pid a marker names, or None."""
    return (read_claim(path) or {}).get("pid")


def claim_checks():
    """A live run refuses a second; an ended or reused one is taken over."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-claim-self-test")
    remove_tree(scratch)
    live = planted_run("judge.py")
    try:

        # Listed first, so a takeover below is the rule's rather than a
        # stand-in that had not started.
        listed = running_as(live.pid, "judge.py")
        judge = plant_claim(scratch, "judge.py", live.pid)
        planted = claimed_pid(judge) == live.pid
        refused = claimed(scratch, "judge.py") is None
        kept = claimed_pid(judge) == live.pid

        # The same live pid under another tool's marker is a reused pid: in
        # use, and not by that tool.
        score_path = plant_claim(scratch, "score.py", live.pid)
        reused_before = claimed_pid(score_path) == live.pid
        reused = (claimed(scratch, "score.py") == score_path
                  and claimed_pid(score_path) == os.getpid())
    finally:
        live.kill()
        live.wait()
    ended = not running_as(live.pid, "judge.py")
    taken = (claimed(scratch, "judge.py") == judge
             and claimed_pid(judge) == os.getpid())
    release_area(judge)
    released = not os.path.exists(judge)

    plant_claim(scratch, "judge.py", live.pid)
    release_area(judge)
    left = claimed_pid(judge) == live.pid
    with io.open(judge, "w", encoding="utf-8") as handle:
        handle.write("")
    unreadable = claimed(scratch, "judge.py") is None
    remove_tree(scratch)
    return [("a planted live run is listed as that tool",
             listed and planted and reused_before),
            ("a live run refuses a second, and keeps its marker",
             refused and kept),
            ("a live pid that is not the tool is taken over", reused),
            ("an ended run is taken over", ended and taken),
            ("a run removes its own marker, and no other",
             released and left),
            ("a marker naming no run refuses", unreadable)]


def claim_refusal_check(tool, main, root, *extra):
    """Whether `main` on `root`, given `extra` arguments, refuses while a live
    run of `tool` holds the scoring area, and leaves that run's marker as it
    was."""
    live = planted_run(tool)
    try:
        path = plant_claim(scoring_area(root), tool, live.pid)
        before = claimed_pid(path)
        listed = running_as(live.pid, tool)
        printed = io.StringIO()

        # A run that got past the claim may fail anywhere after it, and that
        # is the check failing, not the self-test.
        with contextlib.redirect_stdout(printed):
            try:
                code = main(["--root", root] + list(extra))
            except Exception:
                code = None
        after = claimed_pid(path)
    finally:
        live.kill()
        live.wait()
    return ("a live %s run refuses a second" % tool,
            listed and before == live.pid and after == before
            and bool(code) and "is live" in printed.getvalue())


def leftover_checks():
    """A temp entry a trial made and named moves to its own; nothing else."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-leftover-self-test")
    remove_tree(scratch)
    shared = os.path.join(scratch, "shared")
    before = os.path.join(shared, "old_named")
    os.makedirs(before)

    # Apart in time on either side of the start, so no plant can share a tick
    # of the file system's clock with it.
    time.sleep(0.1)
    since = time.time()
    time.sleep(0.1)
    made = os.path.join(shared, "planted_venv")
    unnamed = os.path.join(shared, "unnamed.tmp")
    os.makedirs(made)
    os.makedirs(unnamed)
    landed = (created_at(before) < since
              <= min(created_at(made), created_at(unnamed)))

    calls = [("Bash", json.dumps({"command": "py -m venv /tmp/planted_venv "
                                             "&& ls /tmp/old_named"}))]
    found = shared_leftovers(shared, since, calls)
    target = os.path.join(scratch, "trial", "shared")
    gather_leftovers(shared, found, target)
    checks = [("the plants straddle the trial's start", landed),
              ("an entry the trial made and named is found",
               found == ["planted_venv"]),
              ("it moves under the trial's own directory",
               os.path.isdir(os.path.join(target, "planted_venv"))
               and not os.path.exists(made)),
              ("an older or unnamed entry stays",
               os.path.isdir(before) and os.path.isdir(unnamed))]
    remove_tree(scratch)
    return checks


# On Windows, the folder name the CLI itself wrote for a real trial, so the
# check holds the harness to the CLI rather than to the harness's own rule.
PLANTED_TRANSCRIPT = ((r"C:\efficacy\run-v290\A1", "C--efficacy-run-v290-A1")
                      if os.name == "nt" else
                      ("/efficacy/run-v290/A1", "-efficacy-run-v290-A1"))


def reach_checks():
    """A tool call fetching the templates is flagged; reading them is not."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-reach-self-test")
    remove_tree(scratch)
    home = os.path.join(scratch, "home")
    workspace, folder = PLANTED_TRANSCRIPT
    os.makedirs(os.path.join(home, ".claude", "projects", folder))
    transcript = os.path.join(home, ".claude", "projects", folder,
                              "planted.jsonl")
    fetch = ("curl -sL https://github.com/solid-ai-dev/solid-ai-templates/"
             "archive/main.zip -o t.zip")
    entries = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": fetch}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result",
             "content": "<!-- Generated with solid-ai-templates -->"}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "The footer names solid-ai-templates."}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read",
             "input": {"file_path": "CLAUDE.md"}}]}},
    ]
    with io.open(transcript, "w", encoding="utf-8") as handle:
        handle.writelines(json.dumps(entry) + "\n" for entry in entries)

    files, calls = read_transcripts(home, workspace)
    hits = reach(files, calls)["hits"] or []
    unscanned = reach(*read_transcripts(home, workspace + "0"))
    checks = [("the planted transcript is found", files == [transcript]),
              ("a fetch of the templates is flagged, and only that",
               [(hit["tool"], hit["term"]) for hit in hits]
               == [("Bash", "solid-ai-templates")]),
              ("no transcript reads as not scanned",
               unscanned["hits"] is None)]

    # A voided attempt in the same workspace: its transcript was last written
    # an hour before the re-run started, and the re-run's is written after.
    voided = os.path.join(os.path.dirname(transcript), "voided.jsonl")
    with io.open(voided, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(entries[0]) + "\n")
    since = time.time()
    os.utime(voided, (since - 3600, since - 3600))
    os.utime(transcript, (since + 1, since + 1))
    landed = (sorted(transcript_files(home, workspace))
              == sorted([transcript, voided])
              and os.path.getmtime(voided) < since
              <= os.path.getmtime(transcript))
    checks.append(("a re-run reads only transcripts written since it "
                   "started", landed
                   and transcript_files(home, workspace, since)
                   == [transcript]))
    remove_tree(scratch)
    return checks


def outside_checks():
    """A call into another part of the run is flagged; the trial's own
    workspace and temporary directory are not."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-outside-self-test")
    remove_tree(scratch)
    root = os.path.abspath(os.path.join(scratch, "run"))
    workspace = os.path.join(root, "none-1")
    temp = os.path.join(root, "tmp", "none-1-planted")
    for directory in (workspace, temp, os.path.join(root, "short-1"),
                      os.path.join(root, "tmp", "short-1-planted"),
                      os.path.join(root, "home", ".claude")):
        os.makedirs(directory)
    io.open(os.path.join(root, "short-1.tar"), "wb").close()
    bash_root = root.replace("\\", "/")
    if bash_root[1:2] == ":":
        bash_root = "/%s%s" % (bash_root[0].lower(), bash_root[2:])

    # The first five stay inside the trial; each of the last four reaches out.
    calls = [
        ("Write", {"file_path": os.path.join(workspace, "tariff", "rules.py")}),
        ("Bash", {"command": 'cd "%s" && ls' % workspace}),
        ("Bash", {"command": "pip install . --cache-dir %s"
                             % os.path.join(temp, "pip")}),
        ("Agent", {"prompt": "The repo is at %s. Map its modules."
                             % workspace}),
        ("PowerShell", {"command": 'pip install "%s[dev]"' % workspace}),
        ("Bash", {"command": "cat ../short-1/src/tariff/pricing.py"}),
        ("PowerShell", {"command": "Get-Item %s"
                                   % os.path.join(root, "short-1.tar")}),
        ("Bash", {"command": "ls %s/home/.claude/projects" % bash_root}),
        ("Read", {"file_path": os.path.join(scoring_area(root),
                                            "hidden-suite", "conftest.py")}),
    ]
    texts = [(tool, json.dumps(payload)) for tool, payload in calls]

    # The plant landed: the root holds another trial beside this one, so a
    # call left unflagged is the scan's doing and not an empty run.
    landed = sorted(os.listdir(root)) == ["home", "none-1", "short-1",
                                          "short-1.tar", "tmp"]
    hits = reach(["planted.jsonl"], texts, workspace, temp)["hits"] or []
    flagged = sorted({index for index, (_, text) in enumerate(texts)
                      for hit in hits if hit["call"] == text[:300]})
    remove_tree(scratch)
    return [("the planted run holds another trial", landed),
            ("the scoring area lies outside the run root",
             not scoring_area(root).startswith(root + os.sep)),
            ("the trial's own paths are not flagged, a pip extra included",
             not [index for index in flagged if index < 5]),
            ("every call reaching past the trial is flagged",
             flagged == [5, 6, 7, 8])]


def naming_checks():
    """A trial is named by its arm's word and its block, and round 1's
    letters read as the words they became."""
    checks = [
        ("a trial is the arm's word, a hyphen and its block",
         trial_name("short", 2) == "short-2"
         and split_name("short-2") == ("short", 2)),
        ("round 1's letters read as their words",
         [split_name(name) for name in ("A1", "B2", "C3")]
         == [("none", 1), ("full", 2), ("hand", 3)]
         and canonical("B2") == "full-2"),
        ("a record names its trial whichever way it spells the arm",
         name_of({"arm": "B", "trial": 1}) == "full-1"
         and name_of({"arm": "hybrid", "trial": 3}) == "hybrid-3"),
        ("a word name canonicalises to itself",
         canonical("hybrid-3") == "hybrid-3"),
    ]
    for name in ("none", "D1", "short-x", "-1"):
        try:
            split_name(name)
            checks.append(("%r is refused as a trial name" % name, False))
        except TrialError:
            checks.append(("%r is refused as a trial name" % name, True))
    return checks


# A stand-in for the CLI: prints a result, or not, and then lingers with a
# child that inherits its pipes — the shape of a shell left running.
LINGERING_CLI = """\
import json, os, subprocess, sys, time
mode = sys.argv[1]
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(90)"])
open(sys.argv[2], "w").write(str(child.pid))
if mode != "silent":
    print(json.dumps({"type": "result", "subtype": "success",
                      "is_error": False, "result": "done"}), flush=True)
if mode == "exits":
    child.kill()
    sys.exit(0)
time.sleep(90)
"""


def alive(pid):
    """Whether a process exists, without signalling it."""
    if os.name == "nt":
        proc = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                              capture_output=True, text=True, timeout=60)
        return str(pid) in proc.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def hang_checks():
    """A CLI that lingers after its result, or never answers, is ended with
    everything under it, and what it printed is kept."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-hang-self-test")
    remove_tree(scratch)
    os.makedirs(scratch)
    script = os.path.join(scratch, "cli.py")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(LINGERING_CLI)
    checks = []
    for label, mode, timeout, grace, expected, has_result in (
            ("a CLI that exits after its result is read as exited",
             "exits", 30, 30, "exited", True),
            ("one that lingers after its result is ended after the grace",
             "lingers", 60, 2, "hung", True),
            ("one that never answers is ended at the timeout",
             "silent", 3, 30, "timeout", False)):
        pid_file = os.path.join(scratch, "%s.pid" % mode)
        started = time.monotonic()
        status, stdout, _, ended = run_cli(
            [sys.executable, script, mode, pid_file], "", scratch,
            dict(os.environ), timeout, grace)
        elapsed = time.monotonic() - started
        with io.open(pid_file, encoding="utf-8") as handle:
            child = int(handle.read())
        time.sleep(1)
        checks.append((label, ended == expected and elapsed < 40
                       and (result_of(stdout) is not None) == has_result
                       and (status == 0 if expected == "exited" else True)
                       and not alive(child)))
    remove_tree(scratch)
    return checks


def credential_link_checks():
    """The scratch home reads the account's live credentials, and gets them
    back before a trial where they went missing."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-credential-link-self-test")
    remove_tree(scratch)
    real = os.path.join(os.path.expanduser("~"), CREDENTIALS)
    if not os.path.exists(real):
        return [("no credentials on this machine, so nothing to link", True)]
    home = prepare_home(scratch)
    target = os.path.join(home, CREDENTIALS)
    checks = [("the scratch home's credentials are the live file itself",
               os.path.exists(target) and os.path.samefile(real, target))]
    os.remove(target)
    how = refresh_credentials(home)
    checks.append(("a refresh before a trial restores them, live",
                   how == "linked" and os.path.samefile(real, target)))
    remove_tree(scratch)
    checks.append(("removing the scratch home leaves the live file",
                   os.path.exists(real)))
    return checks


def vendor_checks():
    """The hybrid arm's workspace carries the templates at the release, out
    of its index, and the reach scan reads that tree as the arm's own."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-vendor-self-test")
    remove_tree(scratch)
    workspace = os.path.join(scratch, "hybrid-1")
    os.makedirs(workspace)
    git(workspace, "init", "-q")
    vendored = vendor_templates(workspace, VENDORED)
    git(workspace, "add", "-A")
    expected = git(repository_root(), "rev-parse",
                   "%s:%s" % (VENDORED["ref"], VENDORED["path"]))
    planted = os.path.join(workspace, "docs", "solid-ai-templates",
                           "templates", "base", "core", "git.md")
    checks = [
        ("the templates at the release are in the workspace",
         os.path.isfile(planted) and len(expected) == 40
         and vendored["tree"] == expected),
        ("the vendored tree is out of the workspace's index",
         git(workspace, "ls-files") == ""
         and git(workspace, "status", "--porcelain") == ""),
    ]

    # The first call reads the vendored tree; the second and third fetch the
    # repository, under its owner and under the owner the host redirects
    # from. All three name it, and only the fetches reach for it.
    calls = [("Read", json.dumps({"file_path": planted})),
             ("Bash", json.dumps({"command": "git clone https://github.com/"
                                             "solid-ai-dev/solid-ai-templates"})),
             ("Bash", json.dumps({"command": "git clone https://github.com/"
                                             "braboj/solid-ai-templates"}))]
    own = reach(["planted.jsonl"], calls, workspace, None, vendored)["hits"]
    bare = reach(["planted.jsonl"], calls, workspace, None)["hits"]
    checks.append(("a read of the vendored tree is not a reach for the arm "
                   "carrying it, and a fetch of the repository is",
                   [hit["call"] for hit in own]
                   == [calls[1][1], calls[2][1]]))
    checks.append(("the same read is a reach for an arm carrying no copy",
                   [hit["call"] for hit in bare]
                   == [calls[0][1][:300], calls[1][1], calls[2][1]]))
    remove_tree(scratch)
    return checks


def self_test():
    """Prove the naming, isolation, outcome, resume, change and vendoring
    rules before a trial."""
    checks = (naming_checks() + environment_checks() + credential_checks()
              + credential_link_checks() + outcome_checks() + hang_checks()
              + resume_checks() + change_checks() + dry_run_checks()
              + process_checks()
              + claim_checks() + leftover_checks() + reach_checks() + outside_checks()
              + vendor_checks())
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
    parser.add_argument("--task", choices=("build", "change"),
                        default="build",
                        help="run the build trials, or the change task on "
                             "each scorable build trial")
    parser.add_argument("--arms",
                        help="which arms to run, as words separated by "
                             "commas: none,full,short,hybrid,hand. Required "
                             "for a run, so a run names the arms it "
                             "holds")
    parser.add_argument("--k", type=int, default=K_PRIMARY,
                        help="trials per arm (default %d, the K the design "
                             "fixes; at most %d, the escalation's ceiling)"
                             % (K_PRIMARY, K_CEILING))
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
                             "as short-2")
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

    # A dry run prepares its workspaces, home and record beside the root
    # rather than in it. A workspace is never reused, so one a dry run left
    # in the root would refuse the same trial when the run proper follows.
    work = options.root
    if options.dry_run:
        work = dry_run_area(options.root)
        remove_tree(work)
    os.makedirs(work, exist_ok=True)
    home = prepare_home(work)

    arms = [arm.strip() for arm in (options.arms or "").split(",")
            if arm.strip()]
    unknown = [arm for arm in arms if arm not in ARMS]
    if not arms or unknown:
        print("--arms names %s; the arms are %s"
              % (", ".join(unknown) if unknown else "nothing",
                 ", ".join(ARMS)))
        return 2
    try:
        pending = pending_trials(arms, options.k, options.start)
    except TrialError as error:
        print("refused: %s" % error)
        return 2

    # The change task needs its prompt and its build trials before anything
    # runs, so a design or a run root that cannot supply them refuses here.
    builds, prompt = {}, PROMPT
    if options.task == "change":
        try:
            prompt = read_change_prompt()
            builds = scorable_trials(options.root, task="build")
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
        work, "run-%s.json" % started_at.strftime("%Y-%m-%dT%H-%M-%S"))
    records = []

    def runner(arm, trial):
        refresh_credentials(home)
        if options.task == "build":
            return run_trial(arm, trial, work, home, options)
        name = trial_name(arm, trial)
        if name not in builds:
            raise TrialError("build trial %s has no scorable outcome, so it "
                             "has no change task" % name)
        return run_change_trial(arm, trial, work, home, options,
                                builds[name])

    def write():
        write_run(run_file, started_at, records, options.task, prompt)

    def probe():
        refresh_credentials(home)
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
