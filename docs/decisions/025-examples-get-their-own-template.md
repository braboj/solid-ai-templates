---
id: "025"
status: Accepted
date: 2026-08-05
category: templates
supersedes: []
superseded_by: []
---

# ADR-025: Examples get their own template

## Context

Governance of an `examples/` directory is split across two templates,
and neither half knows about the other.

`stack/python-lib.md` (`[ID: python-lib-structure]`) prescribes the
directory: one file per pattern, smoke-tested in CI, excluded from the
wheel, distinct from `scripts/`. `base/core/readme.md` prescribes its
contents: the index, the offline rule, output that is real and never
fabricated. The bridge between them is a single conditional bullet
under the README's Project structure section — a rule about how example
code *runs*, reached through the template that governs README prose,
because the index happens to be a README.

Three consequences follow from that split.

`base/core/readme.md` carries one file-level `[ID: base-readme]` and no
section IDs. The offline rule is therefore not addressable: a project
that needs to extend or override it has to replace the entire README
contract to reach it.

`base-readme` is in the core tier, so every project inherits the index
and offline rules. `python-lib` is the only one of seventeen stacks
that prescribes the directory. A Go or Node library shipping
`examples/` is governed on content and ungoverned on structure, layout,
and CI.

Two gaps sat in the seam between the halves and were found downstream
in `braboj/page-fetcher`. "Smoke-tested in CI" never says how the
package is installed for that job, and the cheapest reading — reuse the
test job — proves the examples run beside the test tooling rather than
against the published surface (#988). And the index is the one document
whose body is machine-generated program output, which the secret
scanner reads like source; a printed cache key matched
`generic-api-key` and failed the scan on a file containing no secret
(#987). Both are template gaps, not project mistakes, and neither owner
was the obvious place to fix them.

## Decision

1. **A dedicated template** — `templates/base/core/examples.md`
   (`[ID: base-examples]`) holds every rule governing an `examples/`
   directory: contents, index, offline execution, smoke job. Sections
   carry their own IDs so a project can extend one rule without
   replacing a neighbouring contract.

2. **Reached by `depends_on`, not the core tier** — a stack that
   prescribes an examples directory declares `base-examples`. The core
   tier is the set that applies to every project, and most projects
   ship no examples directory; a conditional concern does not belong
   there.

3. **README keeps the pointer only** — `base-readme` MUST state that
   the directory carries its own `README.md`, because the index is a
   README and that template owns READMEs. It MUST NOT restate what the
   index contains.

4. **Stack templates keep only what is language-specific** —
   packaging exclusion, install command, file extension, position
   relative to the source layout. Everything a second language would
   copy verbatim belongs in `base-examples`.

5. **The new template holds what neither owner did** — the smoke job
   MUST install the project the way a consumer does and MUST glob the
   directory rather than list files; the index MUST label a printed
   derived identifier with a word the secret scanner does not treat as
   a credential keyword, and MUST fix the label rather than the
   scanner.

## Alternatives considered

- **Patch the two gaps in place** — rejected; it leaves the rules
  unaddressable behind a single file-level ID and leaves every
  non-Python library governed on content but not structure.
- **Move the index rules into `stack/python-lib.md`** — rejected; the
  rules are language-agnostic, so every library stack that later adopts
  an examples directory copies them, and the copies drift.
- **Add `base-examples` to the core tier** — rejected; it would apply
  a conditional concern to every project and grow the core six for a
  directory most projects do not have.
- **Make it an orthogonal extra, like the platform templates** —
  rejected; an examples directory is a property of the stack, not a
  project-level choice made independently of it.
- **Leave the offline rule as guidance rather than a named ban** —
  rejected; "avoid the network" is satisfiable by an example that
  constructs the real client against a host that obviously resolves,
  which is offline until the day it is not.

## Consequences

- `base/core/readme.md` §5 reduces to one pointer bullet; the index,
  offline and fabricated-output rules move out.
- `stack/python-lib.md` keeps the wheel exclusion, the flat-layout
  caveat and the install command, and gains `base-examples` in its
  `[DEPENDS ON: ...]` header and manifest `depends_on` — both, since
  headers MUST match the manifest (SYS-04).
- `templates/manifest.yaml` gains the `base-examples` entry;
  `py tools/sync.py` regenerates SPEC.md, README.md, INTERVIEW.md and
  `generated/`.
- #987 and #988 are answered by `base-examples-index` and
  `base-examples-smoke`. #987's second request — repeating the
  commit-history point wherever the secret scan is described — is
  platform-template scope and stays open there.
- `go-lib` and `nodejs-lib` prescribe no examples directory today.
  Adopting one is a `depends_on` line plus a structure entry, and is
  not done here.
- The redundancy audit stays clean: the rules move, they do not
  duplicate.

## Related

- `templates/base/core/examples.md` — the new template
- `templates/base/core/readme.md` — the pointer that remains
- `templates/stack/python-lib.md` — the first consumer
