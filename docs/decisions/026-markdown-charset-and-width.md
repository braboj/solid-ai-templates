---
id: "026"
status: Accepted
date: 2026-08-25
category: templates
supersedes: []
superseded_by: []
---

# ADR-026: Markdown gets its own charset and width rules

## Context

Two constraints on document form are stated for source code, silently do
not reach Markdown, and are checked nowhere. They are the same defect
twice, so they are settled together.

**Charset.** `base-quality` Code style states:

> Encode all source files in UTF-8; content MUST be restricted to ASCII
> characters

It names no check, which `quality-gates-pair-check` calls the defect.
Measured over tracked Markdown at the time of writing: 155 of 171 source
files carry non-ASCII, 5,593 characters in all; counting the generated
chains, 172 of 188 files and 17,571 characters. The rule has never held.

The inventory is 32 distinct characters, and what it does *not* contain
decides this ADR. There are no smart quotes, no non-breaking spaces, no
zero-width characters, no byte-order marks, no soft hyphens — none of
the characters that break a diff, a grep, or a copy-paste. What is
present is deliberate typography (an em dash 3,906 times, a section
sign, arrows, en dashes, a handful of mathematical signs), diagram
glyphs, and one Latin letter with an acute accent inside a cited
author name.

The rule therefore bans 5,593 characters, essentially none of which
causes the harm an ASCII restriction exists to prevent.

It also missed the harm that *was* present. Five occurrences of U+FFFD,
the replacement character, sat in two source files — not a typographic
choice but the residue of text decoded with the wrong encoding, with the
original bytes lost. One of them shipped through two resolved chains,
leaving a rule justification unreadable in every project generated from
either. An unchecked rule did not merely fail to enforce a preference;
it failed to catch data loss.

**The box-drawing ban rests on the charset rule.** `base-docs` requires
ADR diagrams to use plain ASCII rather than Unicode box-drawing
characters, and gives its reason as staying consistent with the
ASCII-only source-content rule. Box-drawing appears 981 times across ten
source files, including 724 in the specification document, 131 in one of
the decision records here, and 22 in the agent context file. The only
stated justification for the ban is a rule this ADR is about to scope
elsewhere.

**Width.** `base-docs` Writing style governs tense, length, bold and the
formatting of identifiers, and says nothing about line width. Every
place a width *is* stated is scoped to source: `.editorconfig` sets
`max_line_length` under language blocks, contributor guides state it
under a Code style heading, and linters do not read Markdown. A project
ends up wrapping its documents at a width no rule states and no gate
reads.

This repository is the worked example. `.markdownlint.json` already sets
MD013 to 80 columns with fenced blocks and tables exempt. The rule
exists, configured, and nothing runs it, because markdownlint is a Node
tool in a repository whose entire toolchain is Python.

## Decision

1. **The ASCII restriction governs source code, not Markdown.**
   `base-quality` Code style applies to source files. Markdown documents
   are governed by rules 2 and 4 instead of inheriting a rule written
   for a different medium.

2. **Markdown permits an enumerated character set and bans the rest.**
   Permitted beyond ASCII:

   | Range or code point | What |
   | --- | --- |
   | U+00C0-U+024F | Latin letters with diacritics, for proper names |
   | U+00A7 | section sign |
   | U+00B1, U+00D7, U+2212, U+2248, U+2260, U+2264, U+2265 | mathematical signs |
   | U+2013, U+2014, U+2026 | en dash, em dash, ellipsis |
   | U+2190-U+21FF | arrows |
   | U+2500-U+259F | box-drawing and block elements, in fenced blocks only |

   Everything else outside ASCII is banned. The ban is not a matter of
   taste: it covers every character that is invisible, that is
   confusable with an ASCII character, or that signals a decoding
   failure. Non-breaking space, soft hyphen, zero-width characters, line
   and paragraph separators, byte-order marks, the four smart quotes and
   U+FFFD are named so that no reader has to infer them.

3. **The box-drawing ban is withdrawn.** Its stated premise does not
   survive decision 1. A diagram MUST stay legible in a monospace font
   and MUST NOT depend on colour or proportional spacing; box-drawing
   satisfies both, and reads better than the ASCII approximation for the
   directory trees and flow sketches this project actually draws.

4. **Markdown wraps at 80 columns.** Count characters, not bytes.
   Exempt: table rows, fenced blocks, and a line carrying a URL or link
   target that cannot be broken. A relative link is not exempt.

5. **Both rules are checked, by the project smoke runner.** Charset and
   width become smoke checks in `tests/run_smoke.py` alongside the
   existing document checks. markdownlint stays out of CI and
   `.markdownlint.json` stays as editor configuration: adding a Node
   runtime to install, pin and maintain is a poor trade for two rules
   that are a few dozen lines of standard library, and the existing
   checks already establish where a document gate lives here.

6. **Every rule stated here travels with its check.** A charset or width
   rule that reaches a generated context file MUST carry the command and
   pass condition that verifies it, so a consuming project inherits the
   means to self-check rather than the preference alone.

## Alternatives considered

- **Enforce the ASCII rule as written** — rejected; 5,593 substitutions
  across 155 files, replacing an em dash with a hyphen in every decision
  record and journal entry, to fix nothing. The measurement found none
  of the characters an ASCII restriction targets, and the one genuine
  defect it should have caught was a decoding failure that an allow-list
  catches directly by name.
- **Ban by Unicode property rather than an allow-list** — rejected;
  invisible and confusable are not single Unicode categories, so the
  rule would need a hand-maintained list anyway, and the check would be
  harder to write against the standard library than a list of roughly
  thirty code points and six ranges.
- **Put markdownlint in CI** — rejected; it settles width but not
  charset, and it buys one rule for the cost of a second language
  runtime in the toolchain.
- **Leave width to `.editorconfig`** — rejected; `max_line_length` is
  conventionally set under a language block, and the linters that read
  it do not read Markdown, which is how the constraint came to be
  universally observed and never stated.
- **Split this into two decision records, one per rule** — rejected;
  both are the same premise (a rule written for code, silently not
  covering prose), the same failure (no check), and the same remedy in
  the same file. Splitting would put half a rationale in each.

## Consequences

- `base-quality` Code style scopes its restriction to source files.
- `base-docs` Writing style gains the permitted-character table and the
  width rule, each stating its check.
- `base-docs` loses the box-drawing prohibition in the ADR diagram rule,
  and a monospace-legibility requirement replaces it.
- `tests/run_smoke.py` gains two checks; the resolved chains are
  regenerated.
- The repository becomes compliant with rules 2 and 4 without a content
  sweep, because the measurement that produced the permitted set was
  taken from the repository itself. This is deliberate: a rule derived
  from observed practice needs no migration, and the characters it bans
  are the ones already absent.
- This document uses the em dash it permits, and complies with the rule
  it states.
- A project wanting stricter ASCII-only prose overrides the charset rule
  by section id rather than replacing the writing-style contract.

## Related

- `templates/base/core/quality.md` — the restriction being scoped
- `templates/base/core/docs.md` — the home of both new rules
- `templates/base/workflow/quality-gates.md` — the pairing requirement
  that makes the checks mandatory rather than optional
