# Efficacy benchmark — does a generated context file improve the result?

**Status:** design, pre-registered; no trial has run.
**Date:** 2026-09-12
**Owning issue:** #1184, applying the generic method in
`Imbra-Ltd/imbra-explore`, `cross-cutting/SPIKE-TESTING-AI-ASSETS.md`.
**Artifacts to follow:** the spec and runner under `tests/efficacy/`; the
hidden suite in a private repository (§10); each report as a dated file
under `docs/audits/`.

## 1. Question, pre-registered

> Given the same spec, model and tools, does an agent with a
> `solid-ai-templates`-generated `CLAUDE.md` produce a better application
> than the same agent with no context file — and at what cost?

### 1.1 The verdict rule, fixed before any run

**Unit of analysis.** The paired difference at trial index *k*. Trials run
interleaved as blocks — A₁ B₁ C₁, then A₂ B₂ C₂ — so the arms within a
block meet the same model on the same day. That block is what makes the
pairing real; without it these would be independent runs and the pairing
would be a convenient fiction.

**Statistic.** The mean of the K paired differences, per metric, per
contrast.

**Interval.** A bias-corrected and accelerated bootstrap over those K
differences, 10,000 resamples, 95 %, seed recorded.

**Direction.** Declared per metric in §6 before the run, because half of
them improve downward. An interval is read against its metric's declared
direction, never against "bigger is better".

**Verdicts.** **Better** where the interval lies wholly on the improving
side of zero; **worse** where it lies wholly on the other; **no
improvement shown** where it contains zero. "No improvement shown" is not
a claim that the arms are equal — for that, see the non-inferiority rule
in §1.2.

**What K = 3 can and cannot support.** Three paired differences give a
bootstrap 27 distinct resamples and an exact sign test a minimum two-sided
p of 0.25. No arrangement of three trials reaches conventional
significance, so every interval in the primary run is **descriptive**: it
reports where the effect sits and how unstable it is, and the report says
so beside every row rather than in a footnote. A benchmark that presented
an n = 3 interval as an inferential result would be doing the thing this
document exists to stop.

**Escalation, pre-set and bounded.** One escalation is permitted, once,
and only where a *primary* dimension's interval contains zero while its
observed effect exceeds that metric's practical threshold in §1.2: run one
further block to K = 5 and report both the K = 3 and the K = 5 vectors.
K never exceeds 5, no metric outside the primary dimensions triggers it,
and a second inconclusive result is reported as inconclusive. Sampling
until an interval clears zero is the failure this bound exists to prevent.

**Failure handling.** A trial whose agent produced no installable workspace
scores zero on task success, records its quality metrics as missing rather
than imputed, and is **not** re-run: re-running the failures of one arm is
how a control arm is quietly improved. A trial lost to harness or provider
error, with no agent output to judge, is re-run once and the substitution
recorded in the report.

### 1.2 Non-inferiority, where the claim is that nothing got worse

An interval containing zero is absence of evidence. To claim a metric was
*preserved* — which §9 needs for every template trim — the whole
degradation interval must sit inside a margin fixed here:

| Metric | Margin | Practical threshold for §1.1 escalation |
|---|---|---|
| Task success, hidden suite pass rate | 2 percentage points | 5 pp |
| Adherence checklist fraction | 5 percentage points | 10 pp |
| Primary subjective dimensions, 1–5 | 0.3 points | 0.5 points |
| Static-analysis counts per KLOC | 10 % relative | 25 % relative |
| Change-task churn, files and lines | 15 % relative | 30 % relative |

A "better" claim on adherence counts only where task success is
non-inferior by this table, and a trim is a free win only where every
quality metric is non-inferior by it — not merely where each interval
happens to contain zero.

The whole vector is reported; no single headline number.

## 2. The app — `tariff`

A pricing and invoicing engine with a server-rendered web UI. Decided
2026-09-12 over `logsift`, `flowkit`, `ledger` and `convert`: a domain
model where OOP is the natural shape, two orthogonal extension axes so a
missed Strategy is visible, Decimal arithmetic for sharp hidden tests.
Offline, deterministic, ~1,500–2,000 LOC.

| Concern | What the spec fixes |
|---|---|
| Domain | products with unit prices; discount rules — percentage, bulk (n-for-m), tiered by quantity, coupon code — with declared precedence and stacking; tax jurisdictions with rate tables and rounding mode; an invoice is lines + applied rules + tax + totals |
| Money | `Decimal` throughout, currency fixed to one per invoice, rounding half-even at line level, totals reproducible to the cent — the hidden suite's sharpest edge |
| Public API (Python) | `tariff.Catalog`, `tariff.Invoice`, `tariff.price(invoice, rules, jurisdiction) -> PricedInvoice`; error base `TariffError`; importable without the web app |
| Web UI | Flask + Jinja + HTMX: pages for products, rules, jurisdictions; an invoice builder that re-prices on every change via HTMX partials; invoice preview and export (JSON, CSV, printable HTML) |
| HTTP | routes named in the spec so the hidden suite can drive them with the Flask test client; JSON export endpoint; form posts with server-side validation and CSRF |
| Persistence | SQLite, single file, schema owned by the app; seed fixture in the spec |
| Constraints | no network, Python 3.12, Flask + Jinja + one HTMX script tag; HTML must validate; forms usable without JavaScript |

The spec names the API, the routes and the rule semantics so the hidden
suite can drive them. It does not name a layout, linter, type checker,
error hierarchy shape, logging policy, test convention, template
organisation or accessibility bar — those are what the templates add, so
they stay out of the spec.

## 3. Arms

| Arm | Workspace at start | Purpose |
|---|---|---|
| A control | `SPEC.md`, empty git repo | the bare agent |
| B candidate | A + `CLAUDE.md` generated once via the interview at `v2.90.0` from `Stack: python-flask`, `Extras: stack-htmx, frontend-ux, frontend-quality` (~450 lines, ~21 KB — the same shape as `examples/`) | the product as shipped; no Python web chain carries the frontend rules on its own, so the extras are how a real project would get them |
| C reference | A + a hand-written `CLAUDE.md` of ≤40 lines: layout, `ruff`+`mypy --strict`, tests, one-hierarchy errors, domain free of Flask, escape everything, CSRF on every form | whether the effect is the templates or merely *having* a file |

Arm C is the one that can hurt and the one an adopter will ask about;
running it is recommended.

## 4. Protocol

Per trial (arm × k, K = 3 → 9 trials):

1. Fresh directory, `git init`, copy the arm's starting files.
2. Isolated agent config: scratch `HOME`/`USERPROFILE` and `--settings`
   pointing at a minimal file — no global `CLAUDE.md`, no hooks, no
   auto-memory, no MCP. Model pinned by exact ID and recorded. `--effort`
   fixed. Web tools disallowed. The templates repository is not mounted.
3. One prompt, identical for every arm:
   > Implement the application described in SPEC.md. Done means:
   > `pip install .` succeeds in a clean virtualenv, your own tests pass,
   > and every page and route in the spec works end to end against the
   > seed fixture. Commit when done.
4. `claude -p … --output-format json`, bounded per trial by
   `--max-budget-usd` and a wall-clock timeout, both fixed; transcript,
   token usage, turns and wall time captured, and the record states which
   bound ended a trial. This replaces the `--max-turns N` named when the
   design was drafted: the installed CLI, 2.1.153, carries no such flag.
   Corrected before the first trial, which is when §7's rule allows the
   protocol to move at all.
5. The workspace is frozen (tarball + commit hash) before scoring.

Trials run interleaved (A1, B1, C1, A2, …) so a model-side change mid-run
does not land on one arm.

## 5. Scoring — the layered judge

### Backbone (deterministic, per trial, run by the harness)

| Metric | Measure | Source |
|---|---|---|
| Task success | hidden acceptance suite pass rate, 377 checks across 16 modules: Python API — rule precedence, stacking, tier boundaries, rounding to the cent, jurisdiction tables, invalid rules refused; HTTP — every spec route via the Flask test client, HTMX fragments re-price correctly, JSON/CSV export byte-exact against the seed; browser — 4 Playwright flows; forms work with JavaScript disabled | the private hidden-suite repository (§10), cloned by the harness at scoring time and never into the workspace |
| Install | `pip install .` in a clean venv, `python -c "import tariff"`, app boots and serves `/` | harness |
| Web quality | axe-core WCAG 2.1 AA violations; HTML validity (`html5validator`); XSS probe — a payload in a product name renders inert on every page; CSRF — a form post without a token is refused; response size and request count of the invoice builder | harness, per arm |
| Adherence | fraction of a fixed checklist: `ruff` clean, `mypy --strict` clean, coverage ≥ 80 %, cognitive complexity ≤ 15, `src/` layout, error-contract AST test, NullHandler check, no `print` in library code, citation ban, pyproject metadata complete, README with install+usage, tests discoverable | the python-lib chain's own fenced checks where one exists, else a standard tool |
| Cost | input/output tokens, turns, wall time, API-equivalent $ | harness |
| Scope | files and LOC; count of artifacts nobody asked for (ADR, journal, CHANGELOG, PLAYBOOK) | harness |
| Consistency | spread of every metric above across the three trials of an arm | aggregate |

Adherence runs on **every arm**: it is a quality checklist, not a
template checklist, so the control can score on it.

### Code quality (static, per trial)

Run with the harness's own pinned tool versions and configuration
(`--isolated` / `--config` pointing at the harness file), never the
configuration the agent wrote, so every arm is measured by the same ruler.
Reported as absolute counts and per KLOC.

**Source discovery is layout-independent, and it has to be.** The arms are
free to choose their layout, and `src/` is one of the things a context
file might introduce, so a tool pointed at a hard-coded `src` reads an
empty directory for a valid flat-layout control and reports no findings.
Zero findings and nothing scanned are the same number and opposite facts.
The harness therefore resolves the roots by importing the installed
package and taking its directory, plus every top-level package directory
in the workspace, and passes those paths explicitly.

**A tool that scanned nothing, errored, or timed out records the metric as
missing and flags the trial.** It never records zero. Every table below
also reports the file and line count each tool actually saw, so a
suspiciously clean arm can be told from an unmeasured one by reading the
report rather than by rerunning it.

| Tool | Reports | Delta metric |
|---|---|---|
| `ruff check --select ALL` (fixed ignore list) | violations by category (E/W, F, B, S, D, N, C90, PL, RUF…) | total and per-category count |
| `ruff format --check` | files needing reformat | count |
| `mypy --strict` | errors | count |
| `bandit -r <discovered roots> -f json` | findings by severity and confidence | high+medium count |
| `complexipy` | cognitive complexity per function | max, mean, functions > 15 |
| `radon cc` / `radon mi` | cyclomatic complexity, maintainability index per module | mean CC, min MI |
| `interrogate` | docstring coverage % (modules, classes, functions) | coverage |
| `ruff --select D` (pydocstyle) | docstring convention violations | count |
| `vulture` | unused code | count |
| `pytest --cov` | line and branch coverage | % |
| `mutmut` (optional, expensive) | mutation score | % killed |

The adherence checklist above takes its pass/fail from these where the
same tool answers both; the counts here are the graded view.

### Design (structural, per trial)

| Measure | Tool | Delta metric |
|---|---|---|
| Layering: domain imports neither `flask` nor the persistence module; routes hold no pricing logic; templates receive view models, not ORM rows | `import-linter` contracts written by the harness against the spec's roles (domain, persistence, web), mapped to the trial's module names; an AST probe for `Decimal` arithmetic inside route functions | violations |
| Import cycles, fan-in/fan-out, instability and abstractness per module (Martin) | `grimp` | cycles; mean instability of domain modules |
| Size and shape smells: too many arguments/branches/attributes, god class, boolean-flag parameters, inheritance depth | `pylint --disable=all --enable=R` plus a harness AST walk for `bool` parameters | count |
| Class cohesion | `cohesion` | mean |
| Extension points present: a new discount rule kind and a new jurisdiction reachable without editing existing code (Protocol/ABC or registry), and a new export format likewise | harness AST probe | present / absent, per axis |
| Public surface: names exported vs names the spec requires | harness diff of `__all__` and module-level names | extra + missing |
| IO isolation: pricing accepts catalog, rule and jurisdiction values, not database rows or a live connection; export accepts a `PricedInvoice`, not a request | harness signature probe | fraction |

### Design (change task) — the OCP measure

The task must lie **outside** the semantics `SPEC.md` already fixes, or it
measures data entry rather than design. The first draft asked for a
buy-one-get-one rule and a jurisdiction with a reduced category rate, and
both are already expressible: buy-one-get-one is the existing bulk rule
with `buy` 2 and `pay` 1, and a reduced category rate is a key in a
jurisdiction's existing `rates` table. Every arm would have scored zero
churn by typing two rows into a form, and the measure would have reported
that all three designs were equally extensible.

The task, fixed here:

> Add a **spend-threshold** discount: 5 % off the invoice once the
> subtotal before any invoice-scoped discount reaches 200.00, applied
> before coupons and never alongside another invoice percentage. And add a
> **capped reduced rate**: in a new jurisdiction, one tax category is taxed
> at the reduced rate on the first 50.00 of each line's taxable amount and
> at the standard rate on the excess. Both must appear on the rules and
> jurisdictions pages and take effect in the invoice builder. Keep the
> existing behaviour and your tests passing.

Neither is reachable by configuration. The threshold rule is the first
invoice-scoped rule whose application depends on a *predicate over the
invoice*, where every existing kind is either unconditional or gated only
by a coupon code being present. The capped rate is the first tax that is
not one rate times one taxable amount, so it changes the shape of §4.3
step 12 rather than its inputs.

Measured: files touched, lines changed, whether the build suite is still
green, whether the change-task acceptance module passes, and whether the
new rule and rate are reachable through the same API and UI. A design that
adds one rule class plus one registry entry, and one rate strategy plus one
entry, scores low churn; one that edits the pricing function, the tax step,
three routes and two templates scores high.

**Its acceptance module is owed before any change-task run.** Churn is only
interpretable beside a pass: an arm that touched four lines and broke the
extension has not scored well. The module lives with the hidden suite,
tests the two new behaviours against worked figures fixed the same way §9
fixes the build example, and is written before the first change-task run
for the reason §10 item 8 gives.

Nine extra runs of ~15 minutes.

### Pattern use (judge with evidence, per trial)

For each GoF pattern found, the judge records: where, what it removes (a
duplication, a conditional ladder) or opens (an extension point), and
whether it has more than one implementor. The patterns the app's two
extension axes invite are Strategy for the discount rule kinds,
registry/Factory for resolving a rule or a jurisdiction by name,
Composite or a precedence chain for stacking rules, Adapter for the JSON,
CSV and printable exports, and Builder for assembling an invoice. The list
is what the judge looks for, not what it must find: a design that reaches
the same extension points another way is scored on the property, not the
name.

A pattern with one implementor and nothing removed is scored as
over-engineering, per `oop.md`'s own rule; a conditional ladder over rule
kinds where a Strategy was warranted is scored as a missed pattern.
Reported as warranted / missed / over-engineered counts.

### Subjective (calibrated model judge)

Rubric, 1–5 each with a quoted evidence line per score: SRP (one reason
to change per module), OCP (rule kinds, jurisdictions and export formats
are extension points), LSP (every rule kind honours the rule contract, and
every export the renderer contract), ISP (public API no larger than the
spec), DIP (domain independent of Flask, SQLite and the request cycle),
naming and abstraction level, error design, readability (function length,
nesting, names that carry the intent), maintainability (how a reader finds
where a change goes), test quality.

**Primary dimensions, owner-declared:** design (SOLID and pattern use),
readability, maintainability. The report leads with these; task success
and cost follow. Judged by a different vendor from the generator, blind to
arm, order shuffled, condition markers stripped. Judge model ID recorded.

### Human holdout

The owner scores three outputs blind, one per arm, chosen by the harness.
Scoring is on the three primary dimensions above rather than the full
rubric: those are what the report leads with, and they are the only rows
that rest on the model judge alone. Three outputs on three dimensions give
nine paired scores where the full rubric would give the reader thirty
readings and the statistic three.

Agreement is reported as the share of scores where the judge lands on the
human's number or within one point of it, not as a correlation. Nine
non-independent points do not support a coefficient, and a threshold
applied to one would be a statistic doing the work of a judgement. The
share and the disagreements themselves are printed, and where the judge
differs by two or more on any primary dimension the subjective row is
reported as unvalidated.

## 6. Aggregation and report

Per metric: mean per arm, and three paired contrasts with the bootstrap
interval and verdict §1.1 fixes.

| Contrast | The question it answers |
|---|---|
| B − A | do the templates beat no context file at all |
| C − A | does *any* context file beat none, which is how much of B − A is not the templates |
| **B − C** | do the generated templates beat forty hand-written lines |

B − C is the one an adopter actually asks and the first draft omitted it,
reporting only each arm against the control. A large B − A beside an
equally large C − A is not a result for the templates, and only B − C
separates them.

**Metric direction, declared before the run.** Improving upward: task
success, adherence, coverage, docstring coverage, mutation score,
extension points present, every subjective rubric score. Improving
downward: every static-analysis count, cognitive and cyclomatic
complexity, tokens, turns, wall time, cost, files, lines, artifacts nobody
asked for, change-task churn, axe violations, HTML invalidity. Neutral,
reported without a verdict: maintainability index, instability.

Report file: `docs/audits/YYYY-MM-DD-efficacy.md` with the model IDs, the
CLI versions, the template revision, the arm B brief and its token scan,
K, the bootstrap seed, every trial's raw numbers, every trial that failed
or was re-run and why, the judge agreement, and the verdict vector. A
crossing interval is written as "no improvement shown", and every interval
carries the reminder from §1.1 that at K = 3 it is descriptive.

### In plain terms

The agent is run three times without templates and three times with.
Every run is scored on each metric. For one metric, that gives three
numbers per side.

The comparison is **run against its own partner**, not side against side.
The first run of the bare arm is compared with the first run of the
templated one, because the two went out the same day against the same
model; then the second against the second, and the third against the
third. What gets averaged is those differences.

| | run 1 | run 2 | run 3 | difference | verdict |
|---|---|---|---|---|---|
| without templates | 0.42 | 0.50 | 0.58 | | |
| with templates | 0.75 | 0.83 | 0.92 | +0.33, +0.33, +0.34 | **better** — every pairing improved, and by nearly the same amount |
| with templates, a metric that moved less | 0.45 | 0.60 | 0.70 | +0.03, +0.10, +0.12 | **better** — every pairing improved, but the size is unstable |
| with templates, a metric that did not move | 0.55 | 0.44 | 0.62 | +0.13, −0.06, +0.04 | **not shown** — two runs improved and one got worse |

An earlier draft of this table read the middle row as "not shown" because
the two rows of raw numbers overlap. That is the wrong test, and it is
worth naming: those three pairings improved by 0.03, 0.10 and 0.12, so
every resampling of them averages to something positive and the interval
cannot contain zero. Overlapping columns say nothing when each pairing
moved the same way. Only the bottom row, where the differences change
sign, is genuinely undecided.

The "interval" is the mathematical form of "how consistent are the three
differences"; the harness computes it and prints the verdict, so nobody
decides by eye. With only three of them it is a coarse instrument, which
is why §1.1 has the report call it descriptive.

The report has one such row per metric. Some rows will say better, some
not shown, some worse (tokens, files nobody asked for); all of them are
printed, the primary dimensions first.

## 7. Confounds and their controls

| Confound | Control |
|---|---|
| Your global `CLAUDE.md` and hooks reach the "bare" arm | scratch profile (§4.2); asserted by a dry run that prints the loaded context |
| Agent reads the templates or the web | no mount, web tools disallowed, transcript grepped for URLs |
| Model changes between trials | exact ID pinned, trials interleaved |
| Agent sees the acceptance tests | hidden suite lives outside the workspace; harness copies it in only for scoring |
| Judge prefers its own family or the longer output | different vendor, blind, shuffled, length reported |
| The judge reads the workspace and sees which arm it is | the judge runs against a copy with every context file removed — arm B's `CLAUDE.md` names the arm outright, and arm C's does too. The harness asserts the copy carries no `CLAUDE.md` before the judge is called, and the assertion is a refusal, not a warning |
| Bar moved after seeing results | §1.1's verdict rule, §1.2's margins and this document are committed before the first trial, and the escalation to K = 5 is bounded there rather than decided on seeing a result |
| One task measures one task | stated limitation; a second app is the follow-up, not this run |

## 8. Budget

9 build trials at roughly 60–90 minutes each plus 9 change-task runs of
~15 minutes, and 6 more of each if §1.1's single escalation to K = 5
fires; on the Max plan this is quota, not invoice. 9 judge calls and 3
human reviews. Hidden-suite and harness authoring: one session, plus
a reference implementation of the specification, which is what proves the
suite can grade anything at all — a grader that has never graded is a
control that has never been exercised. The change task's acceptance module
is a further part-session, owed before the first change-task run.
Total: about three sessions plus wall time.

## 9. Reuse as the template benchmark

The same harness measures a template change: control = current templates,
candidate = the trimmed or rewritten version, same paired design, same
verdict rule. That is how "downgrade unjustified MUSTs" (design-notes §19)
stops being an opinion.

A trim is a **free win** only where every quality metric is non-inferior
by §1.2's margins and tokens fall. It is not enough that each quality row
reads "no improvement shown": three trials are far too few to detect a
real regression, so a crossing interval is the expected result of a trim
that genuinely broke something, and accepting on that basis would let the
benchmark launder damage as evidence of safety. The test is that the
degradation interval sits inside the margin, which is a claim the data can
fail to support — and where K = 3 cannot support it for a given metric,
the honest reading is that the trim is unproven, not that it is safe.

A trim that turns any design row to "worse" is rejected by the run.

Two limits. Each iteration costs a full set of trials, so trims are
batched per file, not per rule. And tuning against one app overfits to
it: `tariff` is the dev set, and a second app (`ledger`, §2 runner-up)
stays sealed for the final v3.0 claim, per the method's dev/test split.

## 10. Decisions

Every question the harness depends on is decided, 2026-09-12. §11 pins
arm B's project brief, which is the last of them and long enough to own a
section.

1. The app: `tariff` with a Flask + HTMX UI (§2).
2. Arm C runs. It is the only arm that separates the templates' effect
   from the effect of having any file, and the first question an adopter
   asks.
3. K = 3, escalating once to 5 under §1.1's bounded rule and never
   further. Three is the smallest set an interval can be computed on at
   all, and §1.1 states plainly what it cannot support: no arrangement of
   three trials reaches conventional significance, so the primary run's
   intervals are descriptive and the report says so on every row. The
   alternative, sampling until an interval clears zero, is the failure the
   bound exists to prevent; the honest cost of K = 3 is that a real effect
   can go unshown, and that is reported rather than sampled away.
4. Generator: `claude-sonnet-5` through the `claude` CLI at effort `high`.
   Judge: `gpt-6-astra` through `codex exec`, a different vendor and not
   merely a different family, which is the stronger form of §7's control.
   Both strings are the ones their tools accept, taken from the CLI and
   from the Codex model cache rather than from memory, and both go in the
   report with the CLI versions.

   Sonnet rather than the strongest available generator: 18 runs is a lot
   of quota, it is what a typical adopter runs, and a ceiling effect on a
   stronger model would hide the very contribution being measured.

   Both tools bill against a subscription rather than an API account, so
   §8's "quota, not invoice" covers the judging too. The judge does not
   inherit this machine's Codex configuration: `model_reasoning_effort` is
   set explicitly on the command and recorded, because the local default
   is `low` and the rubric is a reasoning task over long code.
5. The hidden suite lives in a private repository. This repository is
   public, so a suite under `tests/efficacy/` is one search away from any
   future trial with web access, and §7's web ban protects only this
   run's arms. The harness clones it at scoring time; the spec, runner
   and reports stay here.
6. Flask stays. Server-rendered Jinja pages with HTMX partials are its
   home ground, and `python-flask` is the chain arm B names.
7. Timing: the baseline runs against `v2.90.0` before the v3.0 split
   moves any template, so §9's comparison has a control that predates
   the move. The v3.0 plan carries the ordering.
8. The hidden suite is written before any trial runs, against `SPEC.md`
   alone, and committed to its repository before the first arm starts.
   Written afterwards it would be shaped, consciously or not, by what the
   first outputs happened to do, and the bar §1.1 fixes would move with the
   results it grades. The cost is a session that produces no result.

   <!-- measured: 2026-09-12 -->
   Done: 377 checks in `braboj/tariff-hidden-suite`, validated
   two ways before any arm exists.
   <!-- /measured --> A reference implementation written from
   the specification alone passes all of them, so a correct implementation
   is not marked wrong; a mutation control plants five specification
   violations one at a time and the suite catches five. Both live in that
   repository and neither reaches a workspace.
9. The human holdout stays, reshaped: three outputs, three primary
   dimensions, agreement reported as an exact-or-adjacent share rather
   than a correlation (§5). It stays because the report leads with design,
   readability and maintainability, and those rows come from the model
   judge and nowhere else. A benchmark built to stop opinion passing as
   evidence cannot rest its headline on a judge nobody checked, and §9
   hands that same judge a say in which template trims ship.

## 11. Arm B's project brief

Decided by the owner, 2026-09-12. The brief names the domain's two
extension axes. It is what an adopter would actually type: someone
building this application tells the interview that there are discount
rules and tax jurisdictions, because that is what the application is.
A brief withholding them would measure a version of the product nobody
uses.

Pinned here rather than written on the day, because a brief composed
after the spec is fresh in mind drifts toward it:

> `tariff` — Imbra Ltd — a pricing and invoicing web application:
> a product catalog, discount rules of several kinds, tax jurisdictions,
> and invoices assembled from them — Python 3.12 / Flask 3 / Jinja /
> HTMX / SQLite — uv, ruff, mypy strict, pytest — runs locally, no
> deployment target

The stack is named because the spec fixes it for every arm; an interview
left to choose might pick FastAPI, and arm B would then build a different
application from arms A and C.

### What the disclosure costs, and where it does not reach

Naming the axes tells arm B's interview the shape the open-closed measure
scores. The report states this beside the affected rows rather than
leaving a reader to find it:

| Measure | Affected |
|---|---|
| Extension points for rule kinds and jurisdictions; the OCP rubric row for those two axes; the change task, whose fixed prompt adds one of each | Yes. Arm B was told these axes exist. Arms A and C read the same axes in `SPEC.md`, so no arm is ignorant of them, but only arm B had them in front of the interview |
| Extension point for a new export format | **No.** Exports are named nowhere in the brief, so this is the one extension axis every arm meets only through the spec |
| Task success, cost, scope, code quality counts, layering, cohesion, complexity, SRP, LSP, ISP, DIP, error design, naming, readability, maintainability, test quality | No. None of them turns on knowing the axes |

The export axis is therefore the uncontaminated open-closed probe, and the
report leads the OCP finding with it.

### Still out of bounds

The brief stops at the domain's shape. It states no rule semantics, no
rounding mode, no precedence or stacking order, no route paths, no API
names, no error hierarchy and no fixture. Control, run before the first
trial: the generated context file is scanned for the spec's distinctive
requirement tokens, and a hit refuses the run rather than warning. The
token list is drawn when the brief is pinned, which is now, because
drawing it after seeing the generated file is the drift §10 item 8 exists
to prevent.

The brief and the scan's result are committed beside the report.
