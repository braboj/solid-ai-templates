# The rubric control

The benchmark's primary dimensions are a model's opinion. An opinion that does
not change when the code changes measures nothing, and nothing in a normal run
would show that: an arm that moves no row looks like an arm that changed
nothing.

This control settles it. Six trees are built from one pinned application and
the judge scores each. Every tree passes the application's whole suite, so what
separates them is structure alone, and each damages or improves one thing, so a
row that moves says which.

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
py -m pytest -q          # in each built tree; every tree passes
```

`py tests/efficacy/control/control.py --self-test` builds into a temporary
directory, checks every mutation landed and throws it away. It runs in CI.

A second judge reads the same trees through the `claude` CLI:

```bash
py tests/efficacy/control/control.py --root C:/efficacy/control-<date>-claude
py tests/efficacy/judge.py --root C:/efficacy/control-<date>-claude --cli claude --model <model>
```

Give it a root of its own. The rounds' judge is a different vendor from the
generator by design, so this backend reads the control only, and its readings
are never meaned with the other judge's; a separate root keeps them apart on
disk as well as in the report.

A second judge run against a root while one is live is refused: both would
take the same next label, and the second would delete the bundle the first is
reading. A root left claimed by a run that crashed is taken over by the next.

## What each tree does

| Tree | What it is |
|---|---|
| `base-1` | the application as one trial generated it, unaltered |
| `degraded-1` | the domain merged into one module, `from flask import current_app` used inside `price`, and the package's exceptions reparented off `TariffError` |
| `obscured-1` | the pricing algorithm inlined into one long function with abbreviated names, and nothing else: the module boundaries, the error hierarchy and the dispatch are the base's |
| `improved-1` | a rule contract and self-registering kind registry, dispatch on concrete type removed from pricing and persistence, the hardcoded kinds tuple replaced by the registry, a `__class__.__name__` ladder removed from a template, and two stray error classes folded into the package hierarchy |
| `improved-2` | `improved-1`, and the store maps a rule's own terms onto its columns with a codec per column, so no module dispatches on a kind |
| `improved-3` | `improved-2`, and each kind declares the fields it asks a form for, so the form-building code and the template are derived from the registry and no layer names a kind |

## Reading a result

A row is doing its job when it falls on the tree that damages what it
measures and rises on the tree that improves it. Anything else is a finding
about the instrument:

- a row that does not fall cannot detect damage
- a row that does not rise cannot detect improvement, so no arm can ever win
  on it
- a row that moves on neither is carrying no information at all

Which tree tests which row matters. `degraded-1` damages structure and leaves
every function body alone, so a flat `readability` there says nothing about
the row — that is what `obscured-1` is for. Read each row against the tree
built to move it, and treat the others as a check that it is not moving on
noise.

Re-run the control whenever the judge model, its effort, or the rubric prompt
changes. Each of those silently invalidates every reading below.

## What it found

### Before the primaries were anchored, 2026-09-18

Judge `gpt-6-astra` at effort `high`, evidence found 100 % on every judging.
Three trees; the rubric said only that 1 was poor and 5 excellent.

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

`design` and `maintainability` fell on damage and did not rise on improvement.
On the improved tree the evidence line the judge quoted *for* `design` was
`class Rule(ABC):` — it cited the improvement and scored it 3 anyway. The
component rows moved in both directions.

Six judgings of one byte-identical `base-1` bundle returned readability 4, 4,
4, 3, 4, 4 — mean 3.83, SD 0.41 — while eight of the eleven rows returned the
same integer every time. That is why a round judges each trial several times
and means them.

### After anchoring, 2026-09-19

Six trees, one judging each unless stated, evidence 100 % on every judging
counted. A bold cell differs from `base-1` in the same run.

#### gpt-6-astra at effort `high`, the judge the rounds use

| Dimension | base-1 | degraded-1 | obscured-1 | improved-1 | improved-2 | improved-3 |
|---|---|---|---|---|---|---|
| **design** | 3 | **2** | 3 | 3 | **3.5** | **4** |
| **readability** | 3 | 3 | **1** | 3 | 3 | 3 |
| **maintainability** | 3 | 3 | 3 | 3 | 3 | **4** |
| dip | 5 | **1** | 5 | 5 | 5 | 5 |
| srp | 3 | **2** | 3 | 3 | 3 | 3 |
| error_design | 2 | **1** | 2 | **3** | **3** | **3** |
| ocp | 2 | 2 | 2 | **3** | **3** | **3** |
| lsp | 3 | **2** | **2** | 3 | 3 | 3 |
| isp | 4 | 4 | 4 | 4 | 4 | 4 |
| naming_and_abstraction | 4 | **3** | **2** | 4 | 4 | 4 |
| test_quality | 3 | 3 | **4** | **4** | **4** | **4** |

`improved-2` holds two judgings, meaned. The top-up to three per tree stopped
on the judge plan's usage limit after one call; the next section completes it.

#### Opus 5 through the claude backend, a cross-check on the rubric

| Dimension | base-1 | degraded-1 | obscured-1 | improved-1 | improved-2 | improved-3 |
|---|---|---|---|---|---|---|
| **design** | 3 | **2** | 3 | **4** | **4** | **4** |
| **readability** | 4 | **3** | **2** | 4 | 4 | 4 |
| **maintainability** | 3 | **2** | 3 | **4** | **4** | **4** |
| dip | 4 | **1** | **5** | **5** | **5** | **5** |
| srp | 3 | 3 | 3 | **4** | **4** | **4** |
| error_design | 3 | **1** | 3 | **4** | 3 | **4** |
| ocp | 2 | 2 | 2 | **3** | **3** | **4** |
| lsp | 3 | **2** | 3 | **4** | **4** | **4** |
| isp | 4 | 4 | 4 | **3** | 4 | **3** |
| naming_and_abstraction | 4 | **3** | **2** | 4 | 4 | 4 |
| test_quality | 4 | **3** | 4 | 4 | 4 | 4 |

Opus 5 shares a vendor with the generator, so it cannot judge a round. It is
here to ask whether the rubric's behaviour belongs to the rubric or to one
model.

#### What the two say together

Under both judges, every primary falls on the tree built to damage it and
rises on a tree built to improve it:

- `design` falls to 2 on `degraded-1` and reaches 4 on the improved trees
- `readability` falls on `obscured-1`, to 1 under gpt-6-astra and to 2 under
  Opus 5
- `maintainability` reaches 4 once no layer names a kind, which is the tree
  `improved-3` was built to be

The judges differ in threshold, not in direction. Opus 5 credits the
improvement already at `improved-1`; gpt-6-astra waits for `improved-3`. An
arm has to improve more to register under the rounds' judge than under this
one.

Single judgings vary between runs of the same prompt. `design` on
`improved-1` read 4 in three earlier anchored runs and 3 in this one, and
`maintainability` on `degraded-1` read 2 in two earlier runs and 3 in this
one. Those are the flips repeat judging exists to average out, and why a row
is read against its target tree across more than one run before it is
trusted.

The repair is tracked in #1827.

### Three judgings per tree, 2026-09-25

gpt-6-astra at effort `high`, the same root as the single judgings above,
topped up with `--repeat 3`. Evidence found 100 % on every judging. Each
cell is the mean, followed by the three scores; a bold cell differs from
`base-1`.

| Dimension | base-1 | degraded-1 | obscured-1 | improved-1 | improved-2 | improved-3 |
|---|---|---|---|---|---|---|
| **design** | 3.00 (333) | **2.00** (222) | 3.00 (333) | **3.67** (344) | **3.67** (434) | **4.00** (444) |
| **readability** | 3.00 (333) | 3.00 (333) | **1.00** (111) | 3.00 (333) | 3.00 (333) | **3.33** (343) |
| **maintainability** | 3.00 (333) | **2.33** (223) | 3.00 (333) | 3.00 (333) | 3.00 (333) | **4.00** (444) |

Averaged over three, every primary falls on the tree built to damage it and
rises on a tree built to improve it. `design` and `maintainability` fall on
`degraded-1`, `readability` falls on `obscured-1`, and all three rise on
`improved-3`. The one-point flips of single judgings remain inside each
triple, which is what the mean is there to absorb.

## Why the base is a pinned archive

`base.zip` holds one trial's output: the application every tree is built
from. It is an input to this control, not an artifact of it:
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
