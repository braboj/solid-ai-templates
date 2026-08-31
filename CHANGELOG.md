# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions up to and including `v2.63.0` predate this file. They are recorded
in the project's
[GitHub Releases](https://github.com/braboj/solid-ai-templates/releases) —
64 published versions from `v2.1.0` to `v2.63.0`. That set is closed and
does not grow; every version released after `v2.63.0` has its own section
below.

The entries describe changes to the templates, which are what a consuming
project receives. A change to this repository's own tooling or tests that
alters no template carries no entry.

## [Unreleased]

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
