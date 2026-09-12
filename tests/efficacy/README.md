# Efficacy benchmark

Does a generated context file improve the result? The design, the
pre-registered question and the verdict rule live in
`docs/design/efficacy-benchmark.md`. This directory holds the parts that
run.

| Path | What it is |
|---|---|
| `SPEC.md` | the application every arm is asked to build; the harness copies it into each workspace under this name |

Still to come, in the order they are being built: the harness that sets up
and runs an arm, the scoring backbone, and the report writer.

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
