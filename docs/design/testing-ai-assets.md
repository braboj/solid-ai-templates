# Testing AI templates and skills — the generic method

## Abstract

A team working through agents keeps a growing set of AI assets (prompt
templates, agent skills, convention files), and every change to one is
defended with the same sentence, that it delivers better results. That
sentence is asserted, not shown, so the change is unfalsifiable. This document
defines a repeatable method to measure whether a change to a template or
skill actually improves the output. The method fixes a representative task
set, runs the old and new asset as the only difference, repeats each run to
separate the asset's effect from the model's run-to-run noise, and scores
the outputs with a layered judge that stays honest by calibrating against
human readings. The conclusion is a checklist any asset change can run, plus
a hand-off to this library's own measurement, `efficacy-benchmark.md`.


## Question

How do we measure whether a change to an AI template, skill, or prompt
delivers better results, so that the claim rests on evidence rather than
intuition? The method must be generic enough to apply to any prompt-shaped
asset and cheap enough for a solo shop to actually run.


## Context

An AI asset is anything that shapes a model's behaviour without being the
model itself (a prompt template, an agent skill, a convention file such as
CLAUDE.md). Its whole purpose is to make the output better than the model
would produce unaided. The problem is that "better" is claimed on the
strength of a single before-and-after look, and a single look proves
nothing here for four reasons.

The output is not deterministic. Run the same prompt twice and the two
outputs differ, so one before-and-after pair measures run-to-run noise as
much as it measures the change. A change can look like an improvement
purely because the second roll of the dice came up higher.

"Better" is not one number. It can mean more correct, more compliant with
the rules the asset injects, cheaper, faster, or more consistent. A change
usually trades some of these against others. A longer template that raises
rule-following also raises token cost, and reporting only the dimension
that improved hides the one that regressed.

The grader is often biased toward the thing it is grading. When a model
scores output produced by a model of its own family, it tends to prefer
it, and it also tends to prefer the longer answer and the one shown first.
A grader with these leanings, used raw, manufactures the result the author
was hoping for.

The asset can be tuned to the test rather than to the world. If the same
handful of tasks is used both to iterate the asset and to judge it, the
asset learns those tasks and the score climbs while real performance does
not. This is overfitting, and it is easy to do by accident.

A method that answers the question has to defeat all four.


## The measurement method

### Fix a representative task set, then split it

A task is one concrete job the asset is meant to help with. For a template
that generates a context file, a task is "generate the CLAUDE.md for stack
X". For a skill, a task is a prompt that should trigger the skill and use
it. For a convention file, a task is "apply this convention to a sample
repository".

The task set must be drawn from real use, not invented to flatter the
asset, and it must be frozen and versioned so results stay comparable
across asset versions. Split it in two. A dev set is where the asset is
iterated and the score is watched. A test set is touched only to report
the final number. Iterating against the test set is how overfitting sneaks
in, so it stays sealed until the report.

### Change one thing

Define exactly two conditions that differ only in the asset under test.

- The control is the baseline, either no asset at all or the prior version
  of it.
- The candidate is the changed asset.

Everything else is held constant. Same base model and model version, same
task set, same generation settings, same harness. The asset is the only
moving part, so any measured difference is attributable to it and to
nothing else.

### Repeat, and pair

Because the output is stochastic, run each task under each condition K
times. The repeats are what separate the asset's real effect from the
model's noise. Without them a difference of one point is indistinguishable
from luck.

Prefer a paired design. Run the same task set on both sides and compare the
per-task delta, rather than comparing two independent group averages.
Pairing removes task-difficulty variance, which is usually the largest
source of noise, because an easy task is easy under both conditions and its
difficulty cancels out of the delta. A paired design detects the same
effect with far fewer runs than an unpaired one, which is what makes the
method affordable.

### Score, then aggregate as a delta with an interval

Each output gets scored on every metric, by the layered judge defined
below. The scores are then aggregated across the K runs into a per-metric
delta between candidate and control, reported with a spread around it, such
as a bootstrap interval or a mean plus or minus a standard deviation.

The headline is never a bare "candidate scored 8.1, control scored 7.4".
It is a delta with an interval, for example "candidate raised adherence by
0.7 points, interval 0.3 to 1.1, at 12 percent higher token cost". An
interval that crosses zero means the change is not yet shown to help. That
is the falsification working. Reporting it honestly is the point of the
method.


## Metrics

Measure the whole vector, never a single number, because a change usually
moves several of these at once and in opposite directions.

| Metric | What it captures | How it is measured |
|---|---|---|
| Task success | Did the output do the job it was for? | Task-outcome check where one exists (tests pass, page builds, links resolve), otherwise a graded rubric |
| Adherence | Did the output follow the rules the asset injects? | A checklist with one item per rule, checked mechanically wherever the rule is mechanical |
| Cost | Tokens, money, latency, and turns spent | Metered directly by the harness |
| Consistency | How little the output varies across the K repeats | The spread of the metrics above across runs, where smaller is better |

Adherence and task success are not the same signal, and for a template or
skill the distinction matters. Adherence is the direct signal, because the
asset's mechanical job is to make the model follow rules it would otherwise
miss, and adherence measures exactly that. Task success is the ultimate
signal, but it is noisier and confounded by the base model's own ability,
since a strong model succeeds at easy tasks with or without the asset.
Measuring both tells two things. Adherence tells you the asset is doing its
job, and task success tells you that job translates into a better outcome.

### Sizing the runs

There is no clean formula for K and the task-set size, so use a rule of
thumb and report honestly. Run enough that the interval on the delta is
narrow relative to the delta itself. If the interval still straddles zero
after a reasonable budget, either the effect is genuinely small or the run
count is too low, and the report must say which rather than rounding the
result up to "improved". With a small sample, report the effect size and
its interval rather than a binary verdict, because a solo shop's budget
rarely reaches textbook statistical power and pretending otherwise is
dishonest.


## The judge - alternatives considered

Scoring an output is the hard part, because most of what an asset improves
has no obvious numeric answer. There are three ways to score, and each is
good at something the others are not.

### Task-outcome, deterministic where possible

Run the thing the output was for and see whether it works. Generated code
runs its tests. A generated context file runs the project's structural
checks. A generated config parses and lints. This is the most trustworthy
scorer where it exists, because it is objective and cheap to repeat as
often as the run count demands. Its limit is coverage. It only reaches
what has a mechanical outcome. Much of what a good template does has no such
test, like giving the output a sensible structure or a sound judgement
call.

### Human rubric

A person scores each output against a written rubric. This is the gold
standard for the subjective dimensions that task-outcome cannot reach. Its
limit is scale. It is slow and expensive, it does not stretch to hundreds
of runs, and a tired rater drifts. Its real role is not to score the whole
set. It is to produce the small, trusted reference set that the model judge
is calibrated against.

### LLM-as-judge

A model scores the outputs against the rubric. This scales to any number of
runs, cheaply and quickly, which is the only way the subjective dimensions
get measured at the run counts the method needs. Its limit is bias. A model
judge leans toward output from its own family, toward the longer answer,
and toward whichever option it sees first. Used raw it is untrustworthy. It
becomes trustworthy only after it is calibrated against the human rubric
and its biases are controlled.

### Decision - a layered judge

No single scorer covers the field, so use all three in layers, each doing
the part it is good at.

- Task-outcome and deterministic checks are the backbone. They score
  everything with a mechanical answer, meaning checkable rules, build and
  test and lint outcomes, and cost. They are objective and free to repeat.
- A calibrated model judge scores the subjective dimensions the backbone
  cannot reach. It runs blind to the condition and is calibrated against a
  human-scored holdout, with its agreement against that holdout reported
  next to the headline.
- The human rubric builds the holdout and spot-audits the model judge. It
  never scores the full set.

This mirrors the calibration discipline the knowledge base already applies
elsewhere. Ground truth comes from raw artifacts rather than from a suspect
earlier pass, reference values carry a source and a verified flag, and a
measuring tool is verified before its output is trusted.


## Keeping the judge honest

The judge is the load-bearing part of the method, and it fails quietly.

Blind the judge to the condition. The judge must not know whether it is
scoring the control or the candidate, or expectation leaks into the score.
Strip any marker that reveals the source and randomise the order the judge
sees the outputs in.

Do not let the producer grade its own work unqualified. A model judge from
the same family as the generator carries self-preference bias. Either judge
with a different model family, or, if the same family is unavoidable,
calibrate the judge against human labels and report the residual bias.
Reference values produced by the same actor that runs the tool are suspect,
and this is that rule applied to grading.

Calibrate against human ground truth. Score a holdout with the human
rubric, then measure how well the model judge agrees with it, by
correlation or exact-match rate. Report that agreement beside the headline,
for example "judge validated against 20 human-scored outputs, agreement
0.82", so an unverified judge cannot silently dominate the metric.

Move the threshold, not the measurement. When the number and your intuition
disagree, verify the measurement against an independent check first, and
only then tune the pass bar. Quietly changing what you measure until the
result matches what you hoped for is how a calibration turns into a rubber
stamp.

Compression-check the verdict. The final "candidate is better" line is a
compression of many runs down to one claim, and compression is where a
qualifier gets dropped and a hedged result becomes a confident one. Re-read
the verdict against the raw runs. An interval that crosses zero must reach
the report as "no improvement shown", never as "improved".


## The eval harness

The method is a pipeline, and running it by hand every time is how steps
get skipped. The durable form is a small harness that takes the two assets
and the task set and emits the report.

```
        frozen task set (dev / test split)
                     |
                     v
        +------------------------+    control asset (none / prior version)
        |   generate  x K runs   |<---+
        |   per task, per cond.  |<---+ candidate asset (the change)
        +------------------------+
                     |  outputs, condition stripped and order shuffled
                     v
        +------------------------+  deterministic + task-outcome  (backbone)
        |         score          |  calibrated model judge        (subjective)
        +------------------------+  human rubric  (holdout + audit only)
                     |  per-run scores
                     v
        +------------------------+  per-metric paired delta + interval
        |       aggregate        |  judge agreement vs human holdout
        +------------------------+
                     |
                     v
        verdict per metric:  better / no improvement shown / worse,
        each with its cost, reported on the sealed test set
```

The harness does the parts a human does badly. It holds the conditions
identical, it repeats without getting bored, it strips the condition label
before the judge sees the output, and it reports the spread rather than a
tidy point estimate.


## Recommendation

Any change to a template, skill, or prompt is measured by running
this checklist. The claim of improvement is not made until the checklist
produces it.

1. Freeze a representative task set and split it into a dev half and a
   sealed test half.
2. Define exactly two conditions that differ only in the asset under test,
   with the base model, task set, and settings held constant.
3. Run each task under each condition K times, paired, so the per-task
   delta cancels task difficulty.
4. Score with the layered judge, deterministic and task-outcome checks
   first, then a calibrated model judge for the rest.
5. Blind the judge to the condition, calibrate it against a human-scored
   holdout, and report its agreement with that holdout.
6. Aggregate as a paired delta per metric with an interval. A delta whose
   interval crosses zero is "no improvement shown", not "improved".
7. Report the whole vector of adherence, task success, cost, and
   consistency, never one number, because a change usually trades them
   against each other.
8. Iterate on the dev set, report on the sealed test set.

This document defines the method, not any one measurement. Its output is the
checklist above and the calibration rules that keep it honest.


## Hand-off - the solid-ai-templates measurement

The concrete application of this method to the template library itself is
`efficacy-benchmark.md` in this directory, the experiment
that was blocked until this generic method concluded. This document hands
it the design, and the benchmark supplies the parts this one leaves
generic.

- Task set. Pick a few representative stacks, for example a pure library, a
  service, and a static site, and set the tasks to "generate the context
  file for stack X" and "apply convention Y to a sample repository".
- Conditions. Control is generation without the template, or the prior
  template version. Candidate is the current template.
- Scorer. Reuse the existing smoke and end-to-end runners as the
  deterministic backbone rather than building a new probe, since they
  already emit per-case verdicts. Add a calibrated model judge only for the
  dimensions those runners do not cover.
- Report. The adherence, task-success, and cost delta on at least two
  stacks, with the verdict on whether and where the template measurably
  helps.

The generic method here owns the design and the honesty rules. The
downstream spike owns the stacks, the task set, and the numbers.


## Open questions

- [ ] What run count K and task-set size are the practical floor for a solo
  shop's budget, where the interval is narrow enough to trust without
  spending more than the change is worth?
- [ ] Should the model judge be pinned to a recorded model version per
  eval, so that judge drift between evals cannot masquerade as an asset
  improvement?
- [ ] Is a shared, versioned task set and harness worth building once for
  all of a team's assets, or does each asset carry its own?
- [ ] Where does this graduate? A base-layer template rule once the
  benchmark validates it on real numbers, or a design document until
  then?
