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

Still to come: arm B's generated context file, the scoring backbone, and
the report writer.

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

## What is not here

The hidden acceptance suite lives in a private repository. This repository
is public, so a suite kept here would be reachable by any trial with web
access, and the design's web ban protects only the arms of one run. The
harness clones it at scoring time and never into a workspace under test.

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
