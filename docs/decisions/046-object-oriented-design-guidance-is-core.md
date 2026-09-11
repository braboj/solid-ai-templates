---
id: "046"
status: Accepted
date: 2026-09-11
category: composition
supersedes: []
superseded_by: []
---

# ADR-046: Object-oriented design guidance is core

## Context

`templates/base/core/oop.md` (`base-oop`) holds the SOLID, GoF and AOP
guidance. Before this decision it was reached only through
`backend-quality`, whose `depends_on` lists it. It therefore resolved
into the eight service chains and into none of the other nine: the three
library chains, both gRPC chains, the hypermedia and static chains, and
embedded C. Measured on 2026-09-11 with `py tools/resolve.py` per stack.

The gap was widest where API and type design matter most. A library's
public surface is the contract its callers depend on, and the chain that
generates a library's context file carried no rule on interface
segregation, dependency inversion or the shape of an abstraction. The
exclusion was never decided; the dependency graph produced it.

The file is 4,113 characters. The rule family it belongs with —
architecture, readability, maintainability in `base-quality` — is core
already, and `oop.md` reads as that file's continuation for
object-oriented code.

## Decision

1. **`base-oop` is a member of the core tier** — it is listed in the
   manifest's `core:` entry and resolves into every stack chain and every
   opt-in root, alongside `base-quality`, `base-git`, `base-docs`,
   `base-readme`, `base-testing` and `base-review`.

2. **Its rules apply where the paradigm applies** — the file governs
   object-oriented code. A chain whose language or style has no classes
   to design (procedural embedded C, a static site) carries the file and
   applies nothing from it. That is the position every core file takes
   for a rule whose trigger does not occur.

3. **The context tiers hold** — the two chains recorded at the 128K tier
   grow by the file and stay inside it. Measured on the generated chains
   before and after the change: `stack-htmx` from 374,121 to 378,272
   characters and `stack-c-embedded` from 350,465 to 354,616.

## Alternatives considered

- **Add `base-oop` to the three library stacks' `depends_on`** —
  rejected; reaches 13 of 17, because the two gRPC chains inherit from
  the library stacks, and leaves the hypermedia, static and embedded
  chains to discover the file by reading the manifest. A file every
  chain but four carries is a core file with four exemptions and no
  stated reason for them.
- **Leave it as an extra behind `backend-quality`** — rejected; the
  chains it excluded are the ones whose public surface is the product.

## Consequences

- `templates/manifest.yaml` `core:` gains `base-oop`; `backend-quality`
  keeps its explicit `depends_on` entry, which is redundant and permitted
- Every generated chain, the README size table and the SPEC core-tier
  listing are regenerated from the manifest
- The nine chains that lacked the file gain about 4K characters; no
  stack category crosses a context tier
- A rule about object-oriented design goes in `oop.md` with core reach
  and needs no per-stack wiring
