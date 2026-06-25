# Base — Peer Review

[ID: base-review]

## Principle

- All code MUST undergo a peer review before merging
- The reviewer is accountable for what gets merged
- The developer is responsible for the code they write
- Reviews have priority over your own development — a blocked reviewer
  blocks the team

## Priority order

Apply the following order when reviewing, from most to least critical.
Use `templates/base/core/quality.md` (and any language-specific quality template such as
`templates/base/language/typescript.md`) as the standard for items 2–4.

1. **Security exposure** — anything that could be exploited, any credential
   or license problem
2. **Functional correctness** — paths that produce wrong results, unhandled
   failures, or race conditions
3. **Clarity** — obscure names, deep nesting, high cognitive complexity,
   boolean flag parameters
4. **Convention compliance** — code that deviates from agreed project patterns

## MUST checklist

- [ ] No credentials, tokens, or sensitive values appear anywhere in the
      committed files
- [ ] Every failure path is explicitly handled — no silent catches, no
      swallowed exceptions
- [ ] Any new dependency carries a license compatible with the project policy
- [ ] Significant logic or architectural decisions are captured in documentation
- [ ] Existing documentation reflects the state of the code after this change

## MUST checklist — state and boundaries

- [ ] If the change touches shared browser or framework state (history,
      URL, localStorage, global context), verify what else depends on that
      state — review the change in the context of the framework contract,
      not in isolation
- [ ] URL parameters and query strings are treated as untrusted external
      input — validate before destructuring, indexing, or using as keys
- [ ] Refactoring preserves behavior for ALL code paths — if a function
      handles N cases, verify N × directions/modes; extracting a helper
      must not silently change edge-case behavior (null handling, sort
      direction, boundary values)

## CI signals

- [ ] When CI fails, separate **infra failures** (the action could not
      run — network, missing release, broken pinning, runner OOM) from
      **diff failures** (the check ran and produced a negative signal on
      the diff). An infra failure is a signal about the workflow, not
      the PR — surface it honestly in the merge decision rather than
      retrying or ignoring it

Practical guidance:

- On a red check, read the log before calling the PR green or red
- If the failure is infra (`curl 404`, `docker pull` timeout, package
  not found), file a separate task to fix the workflow and note it in
  the merge call
- Do NOT retry-until-green silently — that masks the infra problem
- Do NOT push past it with `--no-verify` or an admin merge unless the
  maintainer explicitly accepts the risk

## SHOULD checklist

- [ ] Non-trivial functions have a unit test for each relevant variant
- [ ] Code coverage does not decrease
- [ ] Lint errors/warnings do not increase
- [ ] Third-party dependencies are necessary, understood, and well-maintained
- [ ] Code is simple — no new abstraction without two or more call sites,
      no new dependency without a documented reason
- [ ] Numerical comparison gates (render-match scoring, calibration
      tolerances, visual-regression diffs) lock the values they sample,
      not the shape between samples — on render-producing pipelines
      (charts, diagrams, illustrations) pair them with manual visual
      review; a passing numerical gate is necessary, not sufficient

## Structure audit

A code review checks changed files. A structure audit checks project
completeness. Run a structure audit after:

- New project setup
- Framework or stack migration
- Adding a major layer (backend, CI/CD, infrastructure)
- Before a release milestone

Verify every MUST from:

- `templates/base/core/docs.md` — standard documents (README, ONBOARDING, PLAYBOOK, ADRs)
- `templates/base/core/readme.md` — README has all 8 required sections
- `templates/base/core/git.md` — .gitignore, README exist
- The relevant frontend or backend layer template — required assets,
  config files, SEO files
- The relevant stack template — framework-specific files and conventions

When a section contains multiple MUST sub-clauses, verify each sub-clause
independently — do not pass the section as a whole. For example,
`templates/base/core/readme.md` Usage requires both usage examples AND expected output
per example — these are two separate checks.

SHOULD also check:

- No substantial duplication across sibling components — if two or more
  components share the same code, extract a shared module

## Deviations

- Deviating from a SHOULD rule requires a written explanation in the pull
  request
- Deviating from a MUST rule requires explicit sign-off from a designated
  approver before the change can land
