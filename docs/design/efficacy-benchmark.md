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

Verdict rule, fixed before any run: per metric, a paired delta with a
bootstrap interval. **Better** if the interval excludes zero on the right
side; **no improvement shown** if it crosses zero; **worse** if it excludes
zero on the left. Task success must be non-inferior for any "better" claim
on adherence to count. The whole vector is reported; no single headline
number.

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
| Task success | hidden acceptance suite pass rate (≈80 tests): Python API — rule precedence, stacking, tier boundaries, rounding to the cent, jurisdiction tables, invalid rules refused; HTTP — every spec route via the Flask test client, HTMX fragments re-price correctly, JSON/CSV export byte-exact against the seed; browser — 3–5 Playwright flows; forms work with JavaScript disabled | the private hidden-suite repository (§10), cloned by the harness at scoring time and never into the workspace |
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

| Tool | Reports | Delta metric |
|---|---|---|
| `ruff check --select ALL` (fixed ignore list) | violations by category (E/W, F, B, S, D, N, C90, PL, RUF…) | total and per-category count |
| `ruff format --check` | files needing reformat | count |
| `mypy --strict` | errors | count |
| `bandit -r src -f json` | findings by severity and confidence | high+medium count |
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
| Extension points present: custom format and output renderer reachable without editing existing code (Protocol/ABC or registry) | harness AST probe | present / absent |
| Public surface: names exported vs names the spec requires | harness diff of `__all__` and module-level names | extra + missing |
| IO isolation: parse/aggregate accept file objects or iterables, not only paths | harness signature probe | fraction |

### Design (change task) — the OCP measure

After the build trial is frozen, a second short run in a copy of each
workspace, same model and isolation, one fixed prompt: *"Add a
buy-one-get-one discount rule and a jurisdiction with a reduced rate for
one product category. Both must appear in the rules and jurisdictions
pages and take effect in the invoice builder. Keep all tests passing."*
Measured: files touched, lines changed, hidden suite still green, the new
rule reachable through the same API and UI. A design that needs one
strategy class and one registry entry per addition scores low churn; one
that edits the pricing function, three routes and two templates scores
high. Nine extra runs of ~15 minutes.

### Pattern use (judge with evidence, per trial)

For each GoF pattern found (Strategy for formats, registry/Factory for
lookup, Template Method for parsing steps, Command for CLI subcommands,
Builder for the pipeline, Adapter for output), the judge records: where,
what it removes (a duplication, a conditional ladder) or opens (an
extension point), and whether it has more than one implementor. A pattern
with one implementor and nothing removed is scored as over-engineering,
per `oop.md`'s own rule; a conditional ladder over formats where a
Strategy was warranted is scored as a missed pattern. Reported as
warranted / missed / over-engineered counts.

### Subjective (calibrated model judge)

Rubric, 1–5 each with a quoted evidence line per score: SRP (one reason
to change per module), OCP (formats and renderers are extension points),
LSP (subtypes honour the parser/renderer contract), ISP (public API no
larger than the spec), DIP (domain independent of CLI and IO), naming and
abstraction level, error design, readability (function length, nesting,
names that carry the intent), maintainability (how a reader finds where a
change goes), test quality.

**Primary dimensions, owner-declared:** design (SOLID and pattern use),
readability, maintainability. The report leads with these; task success
and cost follow. Judged by a different model family from the generator, blind to
arm, order shuffled, condition markers stripped. Judge model ID recorded.

### Human holdout

You score three outputs blind (one per arm, chosen by the harness) on the
same rubric. Judge agreement with the holdout is reported beside the
headline; below 0.7 the subjective row is reported as unvalidated.

## 6. Aggregation and report

Per metric: mean per arm, paired delta B−A and C−A, 1,000-sample bootstrap
interval, verdict per §1. Report file: `docs/audits/YYYY-MM-DD-efficacy.md`
with the model IDs, template revision, K, every trial's raw numbers, the
judge agreement, and the verdict vector. A crossing interval is written as
"no improvement shown".

### In plain terms

The agent is run three times without templates and three times with.
Every run is scored on each metric. For one metric, that gives three
numbers per side.

Compare the two sides the way you would compare two runners timed three
times each: look at the averages, but also at how spread out each
runner's three times are. If the slowest "with" run still beats the
fastest "without" run, the difference is real. If the two sets of times
overlap, the difference could be luck, and the report says so.

| | run 1 | run 2 | run 3 | verdict |
|---|---|---|---|---|
| without templates | 0.42 | 0.50 | 0.58 | |
| with templates | 0.75 | 0.83 | 0.92 | **better** — no overlap |
| with templates (a different metric) | 0.45 | 0.60 | 0.70 | **not shown** — overlaps 0.42–0.58 |

The "interval" in the tables above is the mathematical form of "how much
do the runs overlap"; the harness computes it and prints the verdict, so
nobody decides by eye.

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
| Judge prefers its own family or the longer output | different family, blind, shuffled, length reported |
| Bar moved after seeing results | §1 verdict rule and this document are committed before the first trial |
| One task measures one task | stated limitation; a second app is the follow-up, not this run |

## 8. Budget

9 build trials at roughly 60–90 minutes each plus 9 change-task runs of
~15 minutes; on the Max plan this is quota, not invoice. 9 judge calls
and 3 human reviews. Hidden-suite and
harness authoring: one session. Total: about three sessions plus wall time.

## 9. Reuse as the template benchmark

The same harness measures a template change: control = current templates,
candidate = the trimmed or rewritten version, same paired design, same
verdict rule. That is how "downgrade unjustified MUSTs" (design-notes §19)
stops being an opinion — a trim that leaves every quality row at "not
shown" and lowers tokens is a free win; one that turns a design row to
"worse" is rejected by the run.

Two limits. Each iteration costs a full set of trials, so trims are
batched per file, not per rule. And tuning against one app overfits to
it: `tariff` is the dev set, and a second app (`ledger`, §2 runner-up)
stays sealed for the final v3.0 claim, per the method's dev/test split.

## 10. Decisions

Every question the harness depended on is decided, 2026-09-12:

1. The app: `tariff` with a Flask + HTMX UI (§2).
2. Arm C runs. It is the only arm that separates the templates' effect
   from the effect of having any file, and the first question an adopter
   asks.
3. K = 3. It is the smallest set §1's interval can be computed on. A
   crossing interval on a primary dimension is answered by raising K for
   that run and reporting both, never by lowering the bar.
4. Generator: Claude, pinned by exact model ID. Judge: Gemini, a different
   family per §7. Both IDs go in the report.
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
