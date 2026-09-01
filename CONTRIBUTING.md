# Contributing

Contributions are welcome. This document covers what a change has to satisfy
before it can be merged. It does not repeat the orientation material —
[docs/ONBOARDING.md](docs/ONBOARDING.md) explains what the project is and how
the templates compose, and [docs/PLAYBOOK.md](docs/PLAYBOOK.md) carries the
step-by-step procedure for each kind of change.

Start there if you have not worked in this repository before. Come back here
for the rules your pull request is checked against.

## Before you open a pull request

Run the structural checks. They need Python and no other dependency, and
they take about a second:

```bash
py tests/run_smoke.py
```

If you edited anything under `templates/`, regenerate the derived files as
well, and commit the result with your change:

```bash
py tools/sync.py
```

A pull request whose `generated/` files do not match its templates fails CI.
`py tools/sync.py --check` reports the mismatch without writing anything.

## What a change has to carry

- **A manifest entry.** Every file under `templates/` has one in
  `templates/manifest.yaml`. A new template without an entry fails smoke
- **Resolvable references.** `[DEPENDS ON: ...]`, `[EXTEND: ...]` and
  `[OVERRIDE: ...]` must name things that exist and are reachable in the
  resolved chain
- **Updated documents.** If your change moves the composition model, update
  `docs/SPEC.md`; if it changes a command or the project structure, update
  `README.md`. `CLAUDE.md` section 2.9 lists which document owns what
- **A decision record** for a structural decision — a new layer, a change to
  the override model, a naming convention. See `docs/decisions/` and copy
  `docs/decisions/TEMPLATE.md`
- **The ceilings it raises.** Every root has a chain-size ceiling in
  `tests/chain-budget.txt`, frozen at what the tree measures. A rule added to
  a widely resolved file pushes every chain carrying it over, and SYS-12
  fails until the ceilings are raised in the same change. Raise them
  deliberately: the numbers state what the addition costs every project on
  those chains, which is the point of writing them down. A change that
  shrinks a chain passes without touching the file

## Writing rules

Template content is rules, not prose. The full authoring conventions are in
`CLAUDE.md` section 2.7; the ones contributors most often miss:

- Use RFC 2119 keywords — MUST, MUST NOT, SHOULD, MAY
- Write imperatively. "Use X", "Never Y" — no explanatory paragraphs
  between rules
- Keep lines under 88 characters. Table rows, fenced code and
  `[DEPENDS ON: ...]` lines are exempt
- A rule that can be checked mechanically MUST name the command that checks
  it and the condition that counts as passing. A rule that cannot stays
  declarative — do not invent a brittle check to satisfy this
- Markdown only, no HTML

## Branches, commits and pull requests

- `main` is protected. Work on a branch named `feat/<scope>`,
  `fix/<scope>`, `docs/<scope>` or `chore/<scope>`
- Commits are `<type>(<scope>): <summary>`, where type is one of `feat`,
  `fix`, `chore`, `docs`, `refactor`
- Pull request titles take the same form with the issue number appended:
  `fix(base-quality): exempt a comment that opens a block (#1245)`
- One concern per pull request. A change touching two unrelated rules is
  two pull requests, even when they are both small
- Never force-push, including with `--force-with-lease`. To bring a branch
  up to date, merge `main` into it or use `gh pr update-branch`

## Issues

Every issue carries exactly one type label (`bug`, `task`, `spike`, `epic`,
`incident`) and one priority label (`P0` to `P3`), applied when it is
created. Issue titles are sentence case with an imperative verb and no type
prefix — the label carries the type.

If you are reporting a problem with a rule, say which template file and
section, and what the rule made you do that was wrong. A rule that produced
a bad outcome in a real project is the most useful report this project
receives.

## Reporting a vulnerability

Do not open a public issue. See [SECURITY.md](SECURITY.md) for the private
disclosure route.

## Maintainership

This project has a single maintainer, so review latency varies. A pull
request that sits is not a rejection. `docs/ONBOARDING.md` records what
happens to the project if the maintainer becomes unavailable.
