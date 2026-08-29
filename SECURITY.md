# Security policy

## Disclosure route

Report a vulnerability privately through GitHub's
[private vulnerability reporting](https://github.com/braboj/solid-ai-templates/security/advisories/new)
for this repository. The report is visible only to the maintainers until an
advisory is published.

Do not open a public issue. The tracker is not a disclosure route — filing
there is the disclosure, and the report is world-readable from the moment it
is submitted.

If private reporting is unavailable to you, open a public issue containing
only a request for a private channel, with no detail about the finding.

## Supported versions

The most recent released version receives fixes. It is the version the
`main` branch is tagged at, listed on the
[releases page](https://github.com/braboj/solid-ai-templates/releases).

Older versions do not receive fixes. This project ships text — templates
resolved into a context file — so upgrading is replacing files, and there is
no runtime to migrate. A reader on an older version applies the rule by
checking whether their version is the latest one, not by consulting a table
that goes stale.

## Scope

This repository contains Markdown templates, a small Python toolchain
(`tools/`, `tests/`) and GitHub Actions workflows. Reports are in scope for:

- The toolchain and the workflows — anything executable in this repository
- Template content that instructs a consuming project to do something
  unsafe. A rule that tells a reader to weaken a security control, disable a
  gate, or handle a credential badly is a defect in this project even though
  the harm lands downstream
- The published templates' embedded checks, where running one as documented
  would damage a consuming repository

Out of scope:

- Vulnerabilities in a project generated from these templates, unless they
  trace to a rule this repository ships
- Example commands quoted in a template to illustrate a practice the
  template rejects. These are labelled as counter-examples, and reporting
  one as a finding will be declined with a pointer to the label
- Findings in a dependency of a consuming project, which belong to that
  dependency

## Acknowledgement

A report will be acknowledged within **5 business days**. The
acknowledgement confirms receipt and gives a next step; it is not a fix or
an assessment.

This project has a single maintainer. If you have heard nothing after 5
business days, treat the channel as unreliable rather than the report as
declined, and escalate publicly if your own disclosure policy requires it.

## What a report should contain

- The version or commit the finding is against
- Steps to reproduce, or the file and line where the unsafe instruction is
- The impact you believe it has, and on whom — this project's own
  repository, or a project generated from it

A report without reproduction steps is still worth sending. It costs a round
trip, not a rejection.
