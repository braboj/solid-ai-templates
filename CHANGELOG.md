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

- `base-quality-gates` states the form a shipped check must take: the
  command sits in a fenced block, and prose carries the pass condition
  beside it. A command typed into a sentence cannot be extracted, counted
  or run, so the rule that names it is unenforceable by any tool.
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
  printing it. The old pass condition was "the command prints the
  setting", which both values satisfy, so no configuration was a finding;
  a repository where nothing deletes a merged head branch now fails it,
  and so does a command that returns nothing.
- `base-git` states that the setting licenses nothing. `true` describes
  what an automatic deletion does, and passing a delete-branch flag takes
  the manual path either way — a maintainer who reads the setting, sees
  `true` and types the flag loses the dependent pull request.
- `base-docs` makes `CODE_OF_CONDUCT.md` optional. It was recommended,
  which obliged a project declining it to record a justification; the
  file governs conduct rather than safety, and a project without it
  still has a disclosure route and a contribution path. A project
  adopting it now names who enforces it.

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
