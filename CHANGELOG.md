# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions up to and including `v2.63.0` predate this file. They are recorded
in the project's
[GitHub Releases](https://github.com/braboj/solid-ai-templates/releases) —
62 published versions from `v2.1.0` to `v2.63.0`. That set is closed and
does not grow; every version released after `v2.63.0` has its own section
below.

`v2.57.0` is tagged and has no Release. Its tag was cut 36 minutes before
`v2.58.0` was published, so publishing it now would sort it above `v2.58.0`
on the releases page. The tag holds the tree; the notes are not written.

The entries describe changes to the templates, which are what a consuming
project receives. A change to this repository's own tooling or tests that
alters no template carries no entry.

## [Unreleased]

### Changed

- The release proposal names every step of the pre-release sequence and
  its result, not only the unenforced one; a consuming runbook that
  renumbers or omits those steps inherits the record rather than a
  numbering scheme
- The interview's stack table carries each stack id beside its file path,
  so the resolver call and the pre-resolved file it instructs on both have
  the value they take

## [2.77.0] - 2026-09-03

### Added

- Where a rename spans parts of one call site, the parts are deprecated
  together or not at all; aliasing the outer name alone leaves a call that
  resolves and then fails on its own arguments
- A sentinel a caller compares against is public API and is a single-member
  enum: a type checker narrows a union on identity against an enum member,
  not against an instance of an ordinary class
- The deferred-import map is also where a renamed public symbol keeps its old
  spelling, with the removal version beside the entry and the deprecation
  warning raised in the resolver rather than at each call site
- A library attaches `logging.NullHandler()` to its own logger and installs
  no writing handler; the application tier of the same package is what
  constructs a writing one

### Changed

- A sentinel is also required where a field has no single correct default,
  because the right value varies by consumer — a condition independent of the
  ambiguity one, which alone would wrongly permit a plain default
- A program whose output is another program's input pins its line ending
  as well as its encoding; a trailing carriage return makes every
  downstream comparison miss and the consumer report a confident zero

### Fixed

- The committed-line-ending check matches any known-text path that is not
  `i/lf`, since a file carrying a stray carriage return is filed as binary
  and a check naming `i/crlf` passes over it

## [2.76.0] - 2026-09-03

### Changed

- The end-of-session dev-journal entry is written after flagging gaps, not
  before, since flagging one can produce a change the entry would then omit.
  Where the checklist runs twice, only the last pass writes it
- The milestone-coverage check resolves the issues a merged pull request
  closed, not every issue a commit subject names, and reports how many open
  issues it skipped
- A gate finding is cleared by changing the condition it describes, never the
  input the gate reads; a gate whose cheapest remedy is falsifying its input
  is treated as defective
- Scheduling has three states: milestoned, unmilestoned with a trigger, and
  unmilestoned without one, which means not yet judged. Readiness is not
  recorded, because an answer ages where a question does not
- A groom may close an issue whose premise a merged change has settled

## [2.75.0] - 2026-09-03

### Added

- A negative control must show the planted input reached the check rather
  than a layer in front of it, and must be confirmed in the artifact the
  check reads — git's index, not the working tree
- A check reading a per-item declaration must assert each item declares its
  own, since a permissive default makes an unaudited item read as compliant
- A suite's reporting contract is enforced by the invoker, not by each check
- A generator must verify its declared destination exists; substituting into
  a marker the file no longer carries reports the file in sync
- A gate scoped by an explicit path list must record why each candidate not
  on the list is off it
- An example that verifies something must exit non-zero when the verification
  fails, and be negative-controlled — a printed verdict is a green run

## [2.74.0] - 2026-09-03

### Fixed

- The no-build release step tags the release commit by name rather than
  whatever `main` points at, and both release variants carry
  `gh release create --verify-tag`, which refuses to create a lightweight tag

## [2.73.0] - 2026-09-03

### Changed

- Moving or splitting content between documents no longer requires an ADR.
  The trigger is now whether the decision had an alternative worth recording;
  creating a directory still qualifies, relocating a section does not

## [2.72.0] - 2026-09-01

### Fixed

- The model-limitations table is measured from the shipped chains rather
  than estimated. Every category was understated two to eight times over
  and both 32K minimums were unreachable; `sync.py --check` now fails
  when the figures drift.
- A check deriving its comparison baseline from a command refuses when the
  command produced none, instead of comparing against an empty value. The
  milestone-coverage and off-limits-path checks are corrected.
- Extras and platform templates resolve as their own roots, so a section
  one of them names is checked against the chain its reader actually
  receives. Three dangling references are stated inline instead.
- `base-typescript` states the type-gate and mutation-testing rules inline
  rather than naming two `quality-gates` sections that three of the five
  chains carrying it do not include.

## [2.71.0] - 2026-09-01

### Fixed

- `base-git`'s changelog-completeness check takes the release it prepares
  as a declared value, so an ordinary commit no longer reads as a failure,
  and its pass condition no longer contradicts itself over a commit that
  is deliberately not notable.

### Changed

- `base-git`'s no-build release step titles the GitHub Release with the
  bare version and names the annotated tag message as the artifact
  carrying the release theme, so a release list does not accumulate two
  title forms.
- `base-git` scopes the pre-release periodic review to minor and major
  releases and ships the check that decides it, so a patch owes neither
  the review nor a record declining it.
- `base-quality` reads a check's disposition from its stated pass
  condition rather than a sample of its output, and names the two
  directions a sample misleads in.
- `base-quality` lets a check carry a verdict and a reading together,
  requiring its prose to say which counts carry the verdict and which
  serve the reader the failure summons.
- `base-git`'s periodic-review check refuses a release whose previous tag
  cannot be read, instead of comparing every record against an empty
  string and passing a first release on a record of any age.

## [2.70.0] - 2026-09-01

### Added

- `base-git` requires a release currency gate over a dated artifact to
  compare non-strictly, so a record dated the release day passes and two
  releases can ship on one day.
- `base-quality-gates` requires a change that loosens a gate to add an
  assertion for the case the loosening admits, and to name the reason in
  the assertion's message.

### Changed

- `base-quality-gates` extends the test-edit-boundary check with the test
  root's added and removed line counts, the reading that shows whether a
  weakening shipped with its replacement.

## [2.69.0] - 2026-09-01

### Added

- `base-quality` bounds what a judgement verdict is. A threshold the
  check declares, counted against, reaches an automatic verdict; a
  judgement disposition records what takes a person; and a check's
  output is reported however its verdict was reached.
- `base-quality` reserves exit status 3 for a check reporting at run
  time that it does not apply, and requires a run's summary to count
  it apart from the checks awaiting a reading.
- `base-testing` adds `testing-control-corpus-moves`: a control run
  for a changed check MUST show the check's own corpus count moving,
  or a fixture that was never read reads as a check that correctly
  reported nothing.

### Changed

- `base-docs`, `base-git` and `base-quality-gates` exit 3 from the six
  checks that report a moment is not in progress, so a runner counts
  them apart from a reading rather than folding them into it.

## [2.68.0] - 2026-08-31

### Added

- `base-quality` separates two kinds of boolean flag. One selects what the
  code does and takes an enum; one selects how many rules to apply and
  takes an operation returning findings that name the rule broken.
- `base-quality` forbids a variadic parameter on an abstract or overridable
  operation, which states no contract a subtype can honour or break. A
  capability only a mid-hierarchy class offers gets its own name instead.
- `base-testing` adds `testing-guard-is-used`: where a guard exists so that
  other code takes it, the test asserts the taking. A recording wrapper
  makes the order visible, and one inert primitive is grounds to sweep for
  its siblings.

### Changed

- `base-git` and `base-quality-gates` apply the moment rule to the two
  checks that shipped without it. The changelog-completeness check reports
  that no release is in preparation; the test-visibility check reports
  that no change is under review.

## [2.67.0] - 2026-08-31

### Added

- `base-quality` requires a check whose question is tied to a moment — a
  release, an open branch — to detect that the moment is not in progress
  and report that it does not apply, rather than emitting a count.
- `base-docs` covers an observation stated as a command and its output. A
  command ranging over `HEAD` or the working tree is falsified when the
  record is committed; scope it to the commit the claim is about.

### Changed

- `base-quality-gates` and `platform-github` state the corpus beside the
  count in three checks that reported only a number. A range with no test
  changes now reads differently from a range the check never reached.
- `base-git` applies the moment rule to two checks. Release ordering
  reports that no release is in preparation when the tag is at HEAD; the
  off-limits check separates uncommitted work, no open branch, and a real
  branch.
- `base-docs`' register-identifier check asks whether the project declares
  a register before reporting drift. A register is opt-in, so zero
  identifiers means either never adopted or broken, and only the second is
  a finding.
- `base-quality-gates`' continuation-safety check scans only the languages
  a check is written in. Scanning every fenced block reported valid shell
  inside a documented workflow example. The narrowed corpus is reported as
  its own count.

## [2.66.0] - 2026-08-31

### Added

- `base-quality` states how a check with no automatic verdict is wired: it
  reports what it inspected, and a governance signal is reported rather
  than scored.
- `base-git` states that the squash subject is not replaced at merge
  time. The default appends the pull request number, and a check reading
  the log resolves it back to the work and the issues it closed.
- `base-testing` covers a check whose failure message names another check.
  The reference is a claim that decays: before narrowing what a check
  examines, search the suite for the module's own name.
- `base-ai-workflow` states the inverse of its working-directory rule: a
  probe returning a uniform positive across many inputs is validated
  against a control that must fail, before it is believed.

### Changed

- `base-docs` states the unbreakable-token width exemption as structural
  rather than configured. No Markdown linter expresses it, so listing it
  among the configured exemptions granted an excuse no check could apply.

### Fixed

- `base-docs`' width check applies the unbreakable-token exemption its own
  rule declares. A line is exempt where a URL or Markdown link plus its
  indentation cannot fit; a long line merely carrying a link is not.
- `base-git`'s milestone-coverage check resolves a reference naming an
  issue as well as one naming a pull request, and reports which it found.
  A reference it cannot read is now a finding rather than a silent skip.

## [2.65.0] - 2026-08-29

### Added

- `base-quality-gates` states the form a shipped check must take: the
  command sits in a fenced block, and prose carries the pass condition
  beside it. A command typed into a sentence cannot be extracted or run.
- `base-quality-gates` names the case the fence rule alone does not reach
  — a sentence that describes an action without naming a command states
  no check at all, and an author who wrote no command sees nothing to
  fence.
- `base-quality-gates` requires a tool reporting how many checks it ran to
  report how many it could not see, and gains a check that finds a
  command-plus-pass-condition stated outside a fence.
- `base-quality`'s line-ending rule and `base-examples`' smoke-job rule
  state their checks in the runnable form. The first was prose; the second
  named no command.

### Changed

- `base-git`'s delete-branch check asserts the configuration instead of
  printing it. A repository where nothing deletes a merged head branch
  now fails it, and so does a command that returns nothing.
- `base-git` states that the setting licenses nothing: a delete-branch
  flag takes the manual path whatever the setting says, and deletes a head
  branch a dependent pull request still needs.
- `base-docs` makes `CODE_OF_CONDUCT.md` optional. It was recommended,
  which obliged a project declining it to record a justification. A
  project adopting it now names who enforces it.

## [2.64.0] - 2026-08-29

### Added

- `base-quality` names the failure where a check matches its own source.
  The test: run it from a tree holding that source and from one without,
  and confirm the input count rises while the findings stay identical.
- `base-git` gains a changelog-completeness check, run before the release
  cuts the `Unreleased` section, that reconciles the entries against the
  commits the release carries.

### Changed

- `base-docs` states that generated release notes do not discharge the
  `CHANGELOG.md` requirement, and that a project adopting the file late
  records earlier versions by reference rather than reconstructing them.
- `base-docs` requires the `Unreleased` section to be maintained by the
  change that causes it, and a change needing no entry to say so in its
  pull request.
- The release procedure in `base-git` names the changelog: the cut rides
  in the version-bump commit where a manifest exists, and is its own
  release commit where none does.

### Fixed

- The comment-layout check in `base-quality` no longer reports a comment
  placed first inside a block or a bracketed literal. It exempts a line
  ending in `:`, `(`, `[` or `{`.
- The changelog check in `base-docs` distinguishes a project that has
  published no versions from one that has published versions and carries
  no changelog. Both previously printed the same skip and exited clean.
