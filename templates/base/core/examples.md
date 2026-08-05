# Base — Examples
[ID: base-examples]

Rules for a project that ships an `examples/` directory. An examples
directory is a try-it-now surface, not a folder of sample inputs: every
file in it is runnable, maintained, and executed by CI against the
project it documents.

Applies only where the directory exists. A project without one inherits
nothing from this template.

---

## Contents
[ID: base-examples-scope]

- One file per pattern or user journey — not one per API surface, and
  not one per feature listed in the README. Split on the seams a
  consumer meets, not on the table of contents
- `examples/` is maintained; `scripts/` is throwaway probes and
  benchmarks and is not shipped. A file nobody would run twice belongs
  in `scripts/`
- Examples MUST be excluded from the built artifact, the same way tests
  are
- A design document references an example rather than duplicating its
  code — two copies of a snippet drift, and the copy in prose is the
  one nothing executes

---

## The index
[ID: base-examples-index]

- The directory MUST carry its own `README.md` indexing every example
  as an exact command paired with the output it produces. A bare folder
  of sample inputs under-delivers and reads as broken data
- Output MUST be real or a reproducible dry run — never fabricated
  numbers. Where the true output needs an engine or service the reader
  may not have, show the dry run, which conveys the shape and runs
  anywhere
- A sample input that is incomplete on purpose (an optional field left
  blank) MUST say so next to the command, not leave the reader to
  reverse-engineer the intent
- The index is the one document whose body is machine-generated prose,
  and the secret scanner reads it like source. Where an example prints
  a derived identifier — a hash, a cache key, a request id — label it
  with a word the scanner does not treat as a credential keyword. A
  keyword followed by a high-entropy token is a generic-api-key match
- Fix the label, never the scanner. A fingerprint-scoped allowlist
  entry dies at squash-merge and leaves dead config behind; a
  path-scoped one permanently exempts the one file whose whole purpose
  is pasting program output
- The scan reads commit history, not the working tree — a follow-up
  commit does not clear a finding, the branch has to stop containing it

---

## Offline
[ID: base-examples-offline]

- Examples MUST run offline against data the project already bundles
- Where the behaviour being demonstrated inherently needs a network, a
  service, or a device, the example drives the project's own seam — the
  fake, the fixture, the recorded capture — never the live client
- The rule MUST name the concrete type an example may not construct.
  A soft "avoid the network" invites an example that builds the real
  client and points it at a host that obviously resolves, which is
  offline until the day it is not; a named constructor is a line the
  reader can check and CI can enforce
- A project whose subject matter is I/O MUST accept that its central
  capability may not be demonstrable by any example, and MUST carry it
  where that capability is documented rather than reaching for the
  network to cover it

---

## The smoke job
[ID: base-examples-smoke]

- Every example MUST be executed by CI against the project, so it
  cannot rot
- The job MUST install the project the way a consumer does — no dev,
  test, or optional extras. Reusing the test job proves only that the
  examples run beside the test tooling, which no reader has
- The job MUST glob the directory rather than listing files, so a new
  example is covered without editing CI. A listed job silently stops
  covering the file someone forgot to register
- The job MUST run on the lowest runtime version the project claims to
  support, so an example cannot depend on syntax that version lacks
- Check: install the project alone, then execute every file under
  `examples/`. Pass condition — the run covers at least one file and
  every file exits zero
