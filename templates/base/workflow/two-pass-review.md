# Two-Pass Convention Review
[ID: base-two-pass-review]
[DEPENDS ON: templates/base/workflow/quality-gates.md, templates/base/core/review.md]

Convention checking where some rules are mechanical and others need
judgment. One linter cannot serve both: strict enough to catch the
contextual violations and it fires on legitimate uses; loose enough to
stay quiet and it misses them. Run two passes with opposite tolerances
over one catalogue of examples.

## Principle

[ID: two-pass-principle]

Conventions split into two kinds. A **mechanical** rule matches only
violations — no context makes a match correct. A **contextual** rule
matches *candidates* — whether each is a violation depends on meaning a
scanner cannot see.

```
Artifact
  ├── Pass 1  Mechanical  → zero false positives → auto-fix / block
  └── Pass 2  Contextual  → over-flags → reviewer adjudicates in context
```

## Pass 1 — Mechanical

[ID: two-pass-mechanical]

- Put a rule here only if every possible match is a real violation; if
  one legitimate match exists, move it to Pass 2
- Keep this pass at zero false positives — it is safe to auto-fix or
  block a commit on
- Run it in the cheapest layer that hosts it (see
  `quality-gates.md`); require no human

## Pass 2 — Contextual

[ID: two-pass-contextual]

- Over-flag on purpose — a missed candidate ships, a false one is
  discarded in seconds
- Emit a worklist of candidates, never an auto-fix; a human or a
  reviewing agent adjudicates each against the catalogue
- Tell the reviewer this pass over-flags, so a match inside a legitimate
  exception is dismissed, not "corrected"

## Exceptions are first-class

[ID: two-pass-exceptions]

- Enumerate the legitimate matches of every contextual rule as **not a
  violation**, with examples — quotations, code, verbatim external text,
  deliberate factual uses
- Treat a missing exception list as a defect: without one, a reviewing
  agent edits correct content to satisfy the flag

## The catalogue is the source of truth

[ID: two-pass-catalogue]

- Keep the rule in a versioned catalogue, one entry per pattern: name,
  why it is a violation, a wrong example, its fix, and the matches to
  leave alone
- Treat the scanner as a thin pre-filter that points at the catalogue,
  not as the rule itself
- Add a new pattern to the catalogue first; give it a scanner line only
  when it pre-filters usefully — a pure-judgment pattern has a catalogue
  entry and no scanner line

## Reference scanner shape

[ID: two-pass-scanner]

Language and tooling are project-specific; the two-bucket structure is
not. The bucket headers are load-bearing — they tell the reviewer which
matches are settled and which are candidates.

```bash
#!/usr/bin/env bash
set -uo pipefail
FILE="${1:?usage: scan <artifact>}"

flag() {                        # label + one or more regexes
  local label="$1"; shift
  local out; out="$(grep -nEi "$@" "$FILE" || true)"
  [ -n "$out" ] && printf '\n-- %s --\n%s\n' "$label" "$out"
}

echo "== MECHANICAL (always fix) =="
flag "banned token"   '<deterministic pattern>'

echo "== CONTEXTUAL (judge; quotes/code/factual uses are fine) =="
flag "overclaim"      '<over-flagging pattern>'
```

## Rules

[ID: two-pass-rules]

- A mechanical-pass rule MUST have zero legitimate matches; otherwise it
  belongs in the contextual pass
- The contextual pass MUST emit candidates only — never auto-fix
- Every contextual rule MUST list its legitimate exceptions in the
  catalogue
- Reviewer-facing output MUST separate the two buckets and MUST state
  that the contextual bucket over-flags
- The catalogue SHOULD carry a rationale and a wrong/fixed example pair
  per pattern; the scanner SHOULD stay a thin pre-filter that references
  it
