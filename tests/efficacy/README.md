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

Still to come: the rest of the scoring backbone beyond the acceptance
suites, the judge runner, and the report writer.

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
