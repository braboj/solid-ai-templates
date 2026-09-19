# The rubric control

The benchmark's primary dimensions are a model's opinion. An opinion that does
not change when the code changes measures nothing, and nothing in a normal run
would show that: an arm that moves no row looks like an arm that changed
nothing.

This control settles it. Five trees are built from one pinned application and
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

## What each tree does

| Tree | What it is |
|---|---|
| `base-1` | the application as one trial generated it, unaltered |
| `degraded-1` | the domain merged into one module, `from flask import current_app` used inside `price`, and the package's exceptions reparented off `TariffError` |
| `obscured-1` | the pricing algorithm inlined into one long function with abbreviated names, and nothing else: the module boundaries, the error hierarchy and the dispatch are the base's |
| `improved-1` | a rule contract and self-registering kind registry, dispatch on concrete type removed from pricing and persistence, the hardcoded kinds tuple replaced by the registry, a `__class__.__name__` ladder removed from a template, and two stray error classes folded into the package hierarchy |
| `improved-2` | `improved-1`, and the store maps a rule's own terms onto its columns with a codec per column, so no module dispatches on a kind |

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

Same judge and effort, five trees, one run, evidence 100 % throughout.

| Dimension | base-1 | degraded-1 | obscured-1 | improved-1 | improved-2 |
|---|---|---|---|---|---|
| design | 3 | **2** | 3 | **4** | 3 |
| readability | 3 | 3 | **1** | 3 | 3 |
| maintainability | 3 | **2** | 3 | 3 | 3 |
| dip | 5 | **1** | 5 | 5 | 5 |
| srp | 3 | **2** | 3 | 3 | 3 |
| error_design | 2 | 2 | 2 | **3** | **3** |
| ocp | 2 | 2 | 2 | **3** | **3** |
| lsp | 2 | **3** | 2 | **3** | **3** |
| isp | 4 | 4 | 4 | 4 | 4 |
| naming_and_abstraction | 3 | 3 | **2** | **4** | **4** |
| test_quality | 4 | 3 | 4 | 4 | 4 |

`design` falls to 2 and rises to 4, and `improved-1` returned 4 in three
separate anchored runs. `readability` falls two points on the tree that
actually damages it, having been flat against a degradation that changes no
function body.

`maintainability` still only falls. `improved-2` was built to clear its
anchor — no module dispatches on a kind — and the judge answered 3, quoting
`<label for="percent">Percent (percentage / coupon)</label>`: the rules form
template names kinds, and neither improved tree rebuilds the form. The anchor
is being applied as written; the fixture cannot reach its 5. **That row's
upward range is untested, not disproved.**

`improved-2` also scored `design` 3 where `improved-1` scored 4. It buys its
decoupling with reflection over dataclass fields and a codec table, which a
reader may fairly call worse design than an explicit mapping. Take it as a
reading of the code, not as a fault in the row.

The repair is tracked in #1827.

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
