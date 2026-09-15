# Efficacy benchmark

Does a generated context file improve the result? The design, the
pre-registered question and the verdict rule live in
`docs/design/efficacy-benchmark.md`. This directory holds the parts that
run.

| Path | What it is |
|---|---|
| `SPEC.md` | the application every arm is asked to build; the harness copies it into each workspace under this name |
| `harness.py` | sets up a workspace, runs one trial under an isolated configuration, freezes the result |
| `arms/C-reference/CLAUDE.md` | the hand-written reference context file, the arm that asks whether the effect is the templates or merely having a file |
| `arms/B-candidate/CLAUDE.md` | the generated context file, produced once by `generate_arm_b.py` and never hand-edited |
| `generate_arm_b.py` | produces that file: resolves the chain at the recorded release, builds the prompt from the interview and the pinned brief, scans for a specification leak |
| `score.py` | takes one frozen trial to a JSON score: clean install, boot, source discovery, the hidden suite, the static battery, the adherence checklist, scope and cost |
| `probes.py` | the measurements that must run inside the trial's own interpreter — the structural design probes, and the web-quality probes |
| `scoring-requirements.txt`, `toolconfig/` | the one ruler: the tools, and the lint and type configuration every arm is measured under |
| `judge.py` | builds a blind bundle per trial and runs the model judge over it, with the rubric as a JSON Schema |
| `report.py` | the paired contrasts, the bootstrap intervals, the verdict vector, and the report under `docs/audits/` |

Still to come: nothing in this directory. The first attended trial is what
tells us which of the battery's command lines need correcting, because a tool
whose flags moved records a missing metric rather than a wrong one.

## Before a run

The harness, the scorer and the judge reach outside Python. Each missing
piece shows up as a refusal or a metric recorded missing, not as a crash:

| Needs | For | Without it |
|---|---|---|
| `claude` on `PATH`, logged in | every trial and arm B's generation | the preflight refuses the run |
| `gh`, logged in with access to `braboj/tariff-hidden-suite` | scoring clones the hidden suite | scoring refuses |
| a Java runtime on `PATH` | `html5validator`, the HTML validity metric | that metric is recorded missing |
| a Playwright Chromium for the `playwright` version scoring resolves | the accessibility probe | that metric is recorded missing |
| `codex` on `PATH`, logged in | the judge | each bundle's judging fails |

`score.py --no-web` skips both browser-side probes.

## Generating arm B

```bash
py tests/efficacy/generate_arm_b.py --self-test
py tests/efficacy/generate_arm_b.py --root <outside this repository> --dry-run
py tests/efficacy/generate_arm_b.py --root <outside this repository>
```

One non-interactive invocation, per the design's section 11. Nobody answers
questions: the brief is read out of the design and treated as the client's
answers, so the arm is reproducible and re-running it would produce a
different one. It refuses to overwrite an existing file without `--replace`.

The record of the generation behind the committed file sits beside it as
`arms/B-candidate/generation.json`: the release and the chain it resolved,
the model, the CLI's result and both leak scans. The generator writes it
there whenever it writes the file, and the report reads it from there.

The self test proves the leak scan can fail before it is trusted. The dry
run builds and scans the prompt without calling a model, which is the cheap
way to check the wiring after any change to the brief or the roots.

Two scans run, and they ask different questions. The prompt scan is broad,
because arm B's generation is never handed `SPEC.md` and a hit means the
plumbing is wrong. The output scan is narrow, and the prompt scan earns it:
once the prompt is clean the model demonstrably never read the
specification, so only data nobody could derive, a seed sku or a rule id or
a figure from the worked example, is evidence of a leak.

## Running it

```bash
py tests/efficacy/harness.py --root <a directory outside this repository> \
    --k 3 --model <exact id> --dry-run
```

A dry run prepares every workspace and records the command without calling
a model. Drop `--dry-run` to run the trials. Trials are interleaved — A1,
B1, C1, A2 and so on — so a model-side change part-way through lands
across the arms rather than on one of them.

The root must lie outside this repository, and the harness refuses one
that does not: an arm working inside the templates repository can read the
templates that arm A is defined not to have. It also refuses a run that a
context file above the workspace would reach, and refuses to reuse a
workspace.

Arm B refuses until its context file exists. That file is generated once,
through the interview at the recorded release, and is never hand-written.

One preflight runs before the first trial: a trivial prompt through the
isolated home. The CLI answers an unauthenticated run with a result object
rather than a crash, so without it a whole run can complete having never
reached a model.

A trial inherits this machine's environment, not the launching process's.
A shell inside an agent session or an editor carries that session's
variables, an activated virtual environment on `PATH` and credentials, and
a trial started there would join the session, share one interpreter with
every other trial, and hold keys it has no use for. All of them are removed
before the CLI starts, and each trial record lists the names removed.

Three more routes reach past the environment, and each is closed or
caught:

- **Git's stored credentials.** A helper the machine configures answers
  any Git that asks, and the hidden suite is one authenticated clone away.
  A trial's Git runs with every helper cleared.
- **The temporary directory.** Each trial gets its own under `tmp/` in the
  run root. Git Bash maps `/tmp` to the machine's temporary directory
  whatever `TEMP` says, so an entry that appeared there during the trial,
  and that one of its tool calls names, is moved into the trial's own when
  it ends.
- **Processes.** A server started in the background outlives the CLI. When
  a trial ends, every process running from its workspace, its temporary
  directory, a moved entry or the scratch home is stopped before the
  workspace is frozen, and the record lists them.

The shell keeps its network, because every trial installs packages; only
the two web tools are disallowed. Arm B's file names this repository in its
footer, and a trial's workspace sits in the run root beside earlier trials,
so each transcript is scanned for a tool call naming this repository, the
hidden suite, the scoring area, the run root, or any entry of the root other
than the trial's own workspace and temporary directory, whether spelled from
the root or climbed to with `..`. The trial record carries the hits. The
report scans again under the current rule wherever the transcripts remain,
and names every trial with a hit. A trial with no transcript is recorded as
not scanned, never as clean.

```bash
py tests/efficacy/harness.py --self-test
```

The self test plants one variable of each kind in a copy of the environment
and fails if any survives, or if `PATH` loses an entry it should keep. It
also plants a Git credential helper, a process running from a trial's
directory beside one whose name only extends it, temporary entries made
before, during and without being named, and a transcript that fetches this
repository, and fails if any of them is handled otherwise.

### How a trial ends

| Outcome | What ended it | Scored |
|---|---|---|
| `completed` | the agent finished | yes |
| `budget` | `--budget`, $100 by default, read against the CLI's own cost figure | yes |
| `timeout` | `--timeout`, two hours by default | yes |
| `blocked` | any other error: a usage limit, a rate limit, a crash, a run that returned no result | no |
| `refused` | the harness would not start it, such as a workspace that already exists | no |

A blocked trial is the provider's cut, not the agent's work. Its workspace
and tarball move under `void/`, and the run stops unless it was started with
`--resume-after-block`. That flag probes the generator every `--probe-every`
minutes and re-runs the trial in its own place once it answers. A second
block of the same trial stops the run, and so do `--give-up-after` hours
without an answer.

The run record is rewritten after every trial, so a run stopped part-way
keeps the record of everything it finished. `--from` starts a new run at a
given trial in the interleaved order:

```bash
py tests/efficacy/harness.py --root <the run root> --from B2 --resume-after-block
```

## The change task

```bash
py tests/efficacy/harness.py --root <the run root> --task change --dry-run
py tests/efficacy/harness.py --root <the run root> --task change --resume-after-block
py tests/efficacy/score.py --root <the run root> --task change
```

The change task measures how far each design has to be disturbed to take a
change it was not built for. Its prompt is read from the design, never
restated here. Each change task starts from a copy of its build trial's
frozen workspace and runs under the same isolation, bounds and outcome
rules, in the same order. The copy's state is committed first, so churn
counts only what the agent changed. Scoring re-runs the build suite, runs
the change suite and counts the files and lines changed against that commit,
and writes to `scores-change/` in the scoring area, apart from the build
scores.

Both tasks hand the CLI its prompt on standard input rather than as an
argument. On Windows the CLI is a `.CMD` shim, and `cmd.exe` expands a
`%NAME%` pair inside an argument: sent through one, `%PATH%` arrives as the
value of `PATH`. A prompt passed as an argument is safe only while it
happens to hold no such pair.

## Scoring, judging and reporting

```bash
py tests/efficacy/score.py --self-test
py tests/efficacy/score.py --root <the run root>
py tests/efficacy/judge.py --root <the run root> --dry-run
py tests/efficacy/judge.py --root <the run root> --holdout
py tests/efficacy/judge.py --root <the run root> --record-holdout
py tests/efficacy/judge.py --self-test
py tests/efficacy/report.py --self-test
py tests/efficacy/report.py --root <the run root>
```

Scoring reads every run record in the root, so a run stopped and resumed
`--from` a later trial scores whole; a trial two records both offer is
refused rather than picked. It reads the tarball the harness froze, never
the directory the agent worked in.

Scoring, judging and the aggregate write nothing into the run root. They
write to a scoring area beside it, `<run root>-scoring`: the hidden suite's
clone, each trial's extracted tree and environment, the tool environment and
its lock, the scores and the judge's bundles. Inside the root they would sit
one `..` away from the next trial's workspace.

Each trial gets a clean virtual environment, the trial's package
installed into it, the hidden suite run against that interpreter, and the
static battery at one resolved set of tool versions. The first trial scored
resolves `scoring-requirements.txt` in an environment of its own that holds
nothing else and freezes it to `tool-lock.txt`; every trial installs from
there, so the ruler is identical across the arms and carries no trial's
dependencies.

HTML validity counts the validator's errors less those on HTMX's `hx-*`
attributes. The specification requires HTMX and the HTML standard has no such
attributes, so without the filter the metric would count how much HTMX a trial
uses. The score records the pattern and how many errors it set aside.

The lock leaves out anything installed from a local path, in editable mode
or under the package's own name. A freeze lists the scored trial's package
too, and a lock carrying it installs the first trial's code over every later
trial's. After the battery installs, scoring also checks that the package
under score still comes from the trial's own tree. If it does not, every
metric that imports the package is recorded missing with that reason, never
measured on another trial's code.

Both self tests are controls rather than smoke. `score.py --self-test` plants
a real module in an environment with no tools and requires every metric to
come back *missing*: a tool that scanned nothing must never record a zero,
because zero findings and nothing scanned are the same number and opposite
facts. It also plants a freeze carrying a package installed from a local
path, one in editable mode and one under the package's own name, and fails
if any of them reaches the lock or if a replaced package goes unnoticed.
`report.py --self-test` runs the design's own worked cases through the
verdict rule, including the row an earlier draft of the design read wrongly.

The report also computes the design's one escalation to K = 5, so nobody
decides it by eye. It is owed where a primary dimension's interval contains
zero while its mean paired difference exceeds 0.5 points, in either direction,
on any contrast. At K = 3 the report names the rows that owe it and the
`--k 5 --from A4` run that settles it. At K = 5 it judges the first three
blocks alone, prints their verdict vector beside the K = 5 one, and flags an
escalation no row owed. The harness refuses `--k` above 5, and the report
refuses a run past it. The self test plants a row on each side of the rule.

Judging builds a blind bundle per trial: the context file removed, condition
markers masked, the order shuffled at a recorded seed, the unblinding map
written where the judge cannot reach it. A bundle that still names its
condition is not judged at all. The rubric is passed as a JSON Schema, so a
score is machine-read rather than parsed out of prose, and every evidence line
is checked against the bundle it was quoted from — a judge that never opened
the code returns plausible numbers, and that check is what tells the two
apart.

`--holdout` also writes `judge/holdout-sheet.md` in the scoring area, a table
for the owner's blind scores. Once every cell holds one, `--record-holdout`
writes the
scores file the report reads. A blank cell, a score outside 1-5 or a bundle
that was never judged refuses the whole sheet, and until it records the
report calls the subjective row unvalidated.

## What is not here

The hidden acceptance suite lives in the private repository
`braboj/tariff-hidden-suite`. This repository is public, so a suite kept
here would be reachable by any trial with web access, and the design's web
ban protects only the arms of one run. The harness clones it at scoring
time and never into a workspace under test.

It is written and validated, ahead of any trial as the design requires.

<!-- measured: 2026-09-12 -->
It holds 377 checks across 16 modules, covering the public API, every
refusal, the pricing arithmetic, every route and form, both export formats
byte by byte, the seed, the JavaScript-disabled path and four browser
flows. No generator here can recount them, because the suite is in another
repository; its own README carries the live figure.
<!-- /measured -->

Two things establish that it grades rather than merely runs, and both live
beside it in that repository.

- A reference implementation of `SPEC.md`, written from the specification
  alone by an agent that never saw the tests. Every check passes against
  it, so a correct implementation is not marked wrong. It stays out of
  every workspace, being a worked answer to the task the arms are set.
- A mutation control that plants one specification violation at a time and
  expects a failure: half-up rounding, a tier boundary excluding its own
  threshold, the line rules in the wrong kind order, bulk charging every
  unit, and the allocation's spare cents going to the wrong lines. Five of
  five caught, with a green baseline either side.

Writing the two against the same specification, independently, is what
found the specification's own gaps. It named no form field, so no POST
could be issued at all; it left the fragment response and the
JavaScript-disabled response contradicting each other; and it admitted two
readings of whether a rule that changed nothing counts as applied. Those
are fixed in `SPEC.md`, before any arm was asked to build against it.

A fourth gap was not found that way, because the suite and the reference
implementation read it alike. Section 6 put the application factory "in
the package": both agents in the first two trials read that as anywhere
inside it, while the suite reads the package root, so every check that
needs the application errored in both. Section 6 now names
`tariff.create_app`.

## What the arms receive

Each arm starts from an empty git repository holding `SPEC.md` and, for
the arms that have one, a `CLAUDE.md`. The generated context file is
produced once at `v2.90.0`, the last release before the v3.0 split, and
recorded with the report. Nothing else about the arms differs — the same
prompt, the same model, the same turn limit, the same isolated agent
configuration.

`SPEC.md` fixes the domain semantics, the public Python API, the HTTP
routes and the export formats, because the hidden suite drives them. It
deliberately fixes nothing about layout, tooling, error hierarchy shape,
logging, test convention or template organisation: those are what a
context file adds, so a spec that named them would answer the question
being asked.

## Reports

Each run writes a dated report to `docs/audits/`, naming the model ids,
the template revision, K, every trial's raw numbers, the judge agreement
and the verdict vector.
