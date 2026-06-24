---
id: "013"
status: Accepted
date: 2026-06-24
category: composition
supersedes: ["012"]
superseded_by: []
---

# ADR-013: Split data-quality — calibration and tool-trust move to core

## Context

`base-data-quality` carried agent-behavior rules — calibration
discipline and cross-validation / tool-trust — alongside genuine
data-schema rules. A prior decision wired `base-data-quality` into
the Python service stack so those rules would reach generated
chains, but deferred splitting the file as follow-up work.

`base-data-quality` is opt-in: it reaches only stacks that declare
it (today, the Python service chain), so its broadly-applicable
agent-behavior rules are invisible to every other stack.
`base-ai-workflow` — the apparent home for agent-behavior rules —
is not in the core tier and is declared by no stack, so relocating
the rules there would make them reach no generated chain at all.

The core tier (`base-quality`, `base-git`, `base-docs`,
`base-readme`, `base-testing`) is the only set of templates every
stack resolves. A rule that must reach all stacks has to live there.

## Decision

1. **Calibration and tool-trust move to core** — the "Calibration
   discipline" and "Cross-validation and tool trust" sections move
   from `base-data-quality` into `base-quality` (core tier), reaching
   every stack. They are quality rules — do not fool yourself with
   suspect reference data or buggy tools — not data-schema rules.
2. **Data-research workflow stays in `base-data-quality`** — the
   source-conflict, full-record-audit, figure-cropping, and
   cache-validity rules are genuinely data-research-specific and
   cross-reference the data-sourcing rule; they remain in
   `base-data-quality`.
3. **`base-data-quality` stays opt-in and stays wired into the
   Python service stack** — the residual data-schema + research file
   keeps its existing `depends_on` and stack wiring. Broader rollout
   stays gated on the planned data-heavy stack.

```
            before                          after
  base-data-quality (opt-in)      base-quality (core, all stacks)
  +-- calibration            -->  +-- calibration
  +-- cross-validation       -->  +-- cross-validation
  +-- data-research               base-data-quality (opt-in)
  +-- schema rules                +-- data-research
                                  +-- schema rules
```

## Alternatives considered

- **Move agent-behavior rules to `base-ai-workflow`** — rejected;
  it is not core and no stack declares it, so the rules would reach
  no generated chain (a regression from the current Python-service
  reach).
- **Add `base-ai-workflow` to the core tier** — rejected; pulls the
  entire AI-workflow lifecycle doc into every generated context
  file, far more content than the two rule clusters being relocated.
- **Leave the file as-is** — rejected; the agent-behavior rules stay
  invisible to all stacks except the Python service chain, the gap
  that prompted the split.

## Consequences

- `base-quality` gains two sections (`quality-calibration`,
  `quality-cross-validation`); every `generated/<stack>.md` includes
  them after `py tools/sync.py`.
- `base-data-quality` shrinks to data-schema + data-research rules;
  its `manifest.yaml` description updates accordingly.
- The Python service chain (and transitively Flask, FastAPI, Django)
  keeps the data-research and schema rules; no change to their
  wiring.
- `py tools/sync.py` and `py tests/run_smoke.py` MUST pass after the
  move.

## Related

- #424 — the split task this ADR records
- #298 — data-heavy stack proposal governing future broader rollout
