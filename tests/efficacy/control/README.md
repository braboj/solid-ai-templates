# The rubric control

The benchmark's primary dimensions are a model's opinion. An opinion that does
not change when the code changes measures nothing, and nothing in a normal run
would show that: an arm that moves no row looks like an arm that changed
nothing.

This control settles it. Three trees are built from one pinned application —
the application unaltered, a deliberately damaged copy, and a deliberately
improved one — and the judge scores all three. All three pass the same 47
tests, so what separates them is structure alone.

## Running it

```bash
py tests/efficacy/control/control.py --root C:/efficacy/control-<date>
py tests/efficacy/judge.py --root C:/efficacy/control-<date>
```

The builder prints one line per entity it claims to change, read back off the
trees, and refuses when any mutation did not land. A control whose mutation
silently did nothing reports the tree it never touched as clean, and that reads
as the judge holding when it was never exercised.

To check the trees still behave identically, which is what makes the comparison
about structure:

```bash
py -m pytest -q          # in each built tree; 47 pass in all three
```

`py tests/efficacy/control/control.py --self-test` builds into a temporary
directory, checks every mutation landed and throws it away. It runs in CI.

## What each tree does

| Tree | What it is |
|---|---|
| `base-1` | the application as one trial generated it, unaltered |
| `degraded-1` | the domain merged into one module, `from flask import current_app` used inside `price`, and the package's exceptions reparented off `TariffError` |
| `improved-1` | a rule contract and self-registering kind registry, dispatch on concrete type removed from pricing and persistence, the hardcoded kinds tuple replaced by the registry, a `__class__.__name__` ladder removed from a template, and two stray error classes folded into the package hierarchy |

## Reading a result

The rubric is doing its job when `degraded-1` scores below `base-1` and
`improved-1` scores above it. Anything else is a finding about the instrument:

- a row that does not fall on `degraded-1` cannot detect damage
- a row that does not rise on `improved-1` cannot detect improvement, so no
  arm can ever win on it
- a row that moves on neither is carrying no information at all

Re-run the control whenever the judge model, its effort, or the rubric prompt
changes. Each of those silently invalidates every reading below.

## What it found on 2026-09-18

Judge `gpt-6-astra` at effort `high`, evidence found 100 % on every judging.

| Dimension | base-1 | degraded-1 | improved-1 |
|---|---|---|---|
| design | 3 | **2** | 3 |
| maintainability | 3 | **2** | 3 |
| readability | 4 | **3** | 4 |
| dip | 5 | **1** | 5 |
| srp | 3 | **2** | 3 |
| error_design | 2 | **1** | **3** |
| ocp | 2 | 2 | **3** |
| lsp | 2 | 2 | **3** |
| isp | 4 | 4 | 4 |
| naming_and_abstraction | 4 | 4 | 4 |
| test_quality | 4 | 3 | 3 |

`design` and `maintainability` fall on damage and do not rise on improvement.
On the improved tree the evidence line the judge quotes *for* `design` is
`class Rule(ABC):` — it cites the improvement and scores it 3 anyway. The
component rows do move in both directions.

Six judgings of one byte-identical `base-1` bundle returned readability 4, 4,
4, 3, 4, 4 — mean 3.83, SD 0.41 — while eight of the eleven rows returned the
same integer every time. `readability` is the only primary that has ever moved
in a round, and it is one of the three rows that is not reproducible.

The repair is tracked in #1827.

## Why the base is a pinned archive

`base.zip` holds one trial's output — 33 files, the application the three trees
are built from. It is an input to this control, not an artifact of it:
regenerating it would compare a later run against a different application, and
every number above would silently stop meaning what it says.

Two things hold it still. The builder refuses any archive whose sha256 is not
the one recorded in `control.py`, so a changed base stops the control instead
of quietly shifting what it measures. And every edit the builder makes is an
exact-text swap that refuses when its target is absent, so a base that drifts
stops the control rather than mutating less than it claims.

It is an archive rather than a directory of files because this repository's
own checks read committed Python as source to be brought into line — the
comment-layout rule flags a trailing comment in the application's test suite.
Reformatting the fixture would edit the thing the judge scores, which is the
one change this control cannot survive.
