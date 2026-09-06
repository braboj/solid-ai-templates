# SOLID-AI Templates consolidated product and architecture handoff

**Status:** Consolidated analysis and directional handoff  
**Date:** 2026-09-01  
**Customer-objective update:** 2026-09-06
**Competitor findings:** 2026-09-06; section 9 records approved v3.0 scope.
**Audience:** Maintainer or agent evaluating the next project phase  
**Decision status:** Directional proposals; implementation status is tracked in
linked issues and PRs. Consequential architectural choices may need an ADR;
routine maintenance and these working notes do not automatically require one.

## 1. Purpose

This document consolidates four temporary design reports into one source for
later analysis. It covers:

- product concepts and boundaries;
- current and proposed features;
- practical adoption scenarios;
- architecture and compiler direction;
- policy quality;
- risks and technical debt;
- issue and release amplification;
- stabilization and migration options;
- proposed success measures;
- decisions still required.

It is a diagnostic and architectural handoff, not an implementation mandate.

## 2. Executive summary

The target users are small engineering teams pursuing autonomous coding and
routine code review. The team develops specifications and architecture, defines
tests, and validates the resulting behaviour. Agents implement, run automated
checks, review changes, and repair defects within that agreed scope.

SOLID-AI contributes engineering policy and verification guidance alongside the
team's specification tools, agent runners, and test infrastructure. The objective
is to find a workable balance of autonomy, correctness, human effort, and cost
for each team and class of change.

An **engineering-policy compiler for AI coding agents** is a proposed technical
means to that outcome. Building a compiler or generating more context files does
not, by itself, demonstrate customer value. Section 3 defines the customer goals
and the first validation targets.

Its central question is:

> What engineering rules should this software satisfy?

Its valuable asset is not generated Markdown. It is portable, composable,
versioned, validated engineering knowledge.

The existing project has a credible foundation:

- modular concern templates;
- base, language, layer, platform, and stack composition;
- explicit dependencies;
- `EXTEND` and `OVERRIDE` semantics;
- a machine-readable manifest;
- several real stack implementations;
- agent-independent intent;
- interview/bootstrap support;
- structural checks and an extensive decision history.

The current operating model is nevertheless unstable. The repository has a
strong mechanism for adding policy and almost no equivalent mechanism for
rejecting, consolidating, expiring, or deleting it. Large central templates mix
invariants, preferences, procedures, historical failures, and edge cases.
Audits create issues faster than releases consume them, while structural
validation has grown more quickly than evidence that agents perform better.

The project therefore has two related jobs:

1. **Stabilize and compress the policy corpus and its governance.**
2. **Move deterministic mechanics from LLM interpretation into a compiler.**

Do not attempt both as one uncontrolled rewrite. Freeze semantics, establish
fixtures and outcome baselines, then move mechanics into code while policy
compression proceeds against measured behaviour.

### 2.1 Assessment

The original practical-use assessment was 7/10. Detailed repository and tracker
analysis lowers current production readiness to **5.5/10**, while preserving a
higher long-term potential.

| Dimension | Score | Summary |
|-----------|------:|---------|
| Composition concept | 7/10 | Useful graph, extension, and override model |
| Reusable engineering standards | 8/10 | Valuable catalogue across several stacks |
| Structural rigor | 8/10 | Strong internal checks and recorded decisions |
| Supported greenfield use | 8/10 | Good bootstrap potential for existing stacks |
| Incremental refactoring | 7/10 | Useful target policy, but needs behaviour baselines |
| Company-wide adoption | 6/10 | Needs overlays, compact outputs, and governance |
| Product focus | 4/10 | Policy-system work dominates adopter capability |
| Outcome validation | 3/10 | Live agent evidence is stale and incomplete |
| Context efficiency | 3/10 | Generated profiles are too large by default |
| Governance sustainability | 3/10 | Audits and releases amplify obligations |
| Backlog economics | 3/10 | No cap or meaningful admission control |
| Current production design | **5.5/10** | Valuable core inside an unstable loop |

## 3. Customer needs and measurable objectives

### 3.1 Customer outcome

Customer outcome:

> Enable small teams to delegate coding and routine code review to agents while
> concentrating on specifications, architecture, tests, and acceptance of behaviour.

The primary customer-value measure is human effort per accepted change. Measure
specification, supervision, review, and repair time; include an allocated share
of setup and maintenance effort. Compare like-for-like tasks against a realistic
baseline. An accepted change satisfies independently defined behavioural and
quality criteria, not merely an agent's assertion that it is finished.

Track total delivery cost alongside human time: labour at an agreed rate, model
and tooling costs, and product fees. Count regressions found during a stated
follow-up window. Report task failures and unfinished changes as well as accepted
ones so the measure cannot improve by excluding difficult work.

### 3.2 Target users and their needs

The initial users are small engineering teams already using coding agents and
spending material time reviewing or correcting their output. They need to combine
SOLID-AI with their existing tools, apply their own standards, and delegate routine
implementation and review without continuous supervision.

The team owns the specifications, architectural decisions, test expectations,
and acceptance testing. Agents can assist with these activities, but generated
code and agent-written tests do not redefine the intended behaviour. Automated
test execution inside the agent loop supplies evidence for the team's testing
and acceptance work.

Start validation with one representative stack and a reference project, guided
setup/customization, automated checks, and named model and agent versions.
Internal Imbra projects supply fixtures and early learning; include independent
users to test whether the experience works without the maintainer's knowledge.

### 3.3 Proposed validation objectives

The following numbers are initial customer-outcome targets proposed on 2026-09-05.
They are not achieved results, forecasts, or published product promises. Day 0
is the start of a resourced pilot programme; the deadlines are relative to that
start. Review feasibility after establishing baselines, and record target changes
before the final evaluation rather than adjusting them to flatter its result.

| Goal | Proposed measurable objective | Evidence and decision |
|------|-------------------------------|-----------------------|
| Prove engineering savings | By day 90, demonstrate at least 20% lower median total human effort and 30% lower median review/repair time on matched tasks | Paired baseline/candidate trials on one reference stack across three named model configurations; report per-model results, variability, failures, and customer-pilot observations |
| Preserve correctness | Meet predefined acceptance tests with no observed increase in serious defects during the pilot evaluation and 30-day follow-up | Independent outcome checks and human review; small samples do not prove equivalence, and unresolved serious regressions block a savings claim |
| Make adoption economical | By day 90, at least four of five observed engineers complete setup and one useful custom rule in at most 60 minutes without maintainer intervention | Record all attempts, assistance, and validation outcomes; the custom rule must compose and pass its example scenario |

Include the customer's setup, maintenance, model, and tooling costs when assessing
the benefit. Saving tokens while spending more engineering time does not establish
the intended improvement.

Also measure the share of changes accepted without human implementation or
routine code-review intervention after the team agrees the specification and test
expectations. Record interventions, their causes, and escaped defects; required
team acceptance remains part of total human effort. Increased autonomy counts as
progress only when correctness and overall effort remain acceptable. The useful
balance varies by task, model, stack, and team; it is not one universal setting.

### 3.4 Capabilities that serve the goals

| Engineer need | Product response | Success signal |
|---------------|------------------|----------------|
| See why templates are worth adopting | Runnable reference project with ordinary documentation, concise handwritten guidance, and SOLID-AI comparison conditions | Reproducible differences in accepted-change effort and quality, broken down by model |
| Spend less time reviewing code | Bounded implementation/check/repair loop integrated with an existing agent runner; concise evidence and unresolved decisions | Reduced review and repair effort with acceptance criteria preserved |
| Create personal or company templates | Guided authoring that finds existing rules, chooses extension/override scope, previews reach and cost, and validates an example | Useful customization without expert intervention or unnecessary upstream changes |
| Report bugs or conceptual mistakes easily | Guided, user-reviewed report preparation with version/rule context and duplicate suggestions | An actionable report without repeated information requests; no automatic publication of private material |

These capabilities do not promise arbitrary unattended development. Expand
automation by change category when observed reliability supports it, with bounded
retries and escalation for ambiguity or failure. The engineer owns behavioural
intent; the repair loop cannot weaken acceptance criteria to obtain a pass.

### 3.5 Supporting capabilities and boundaries

The existing Imbra plans already assign these responsibilities:

- `solid-ai-templates`: shared policy, composition, validation, and behavioural
  evidence. Engineering Policy as Code remains the proposed technical category.
- ImContext: the user experience built on that library,
  including guided generation, maintained bundles, and organization customization.
- ImCost: an optional source of session/model cost measurements; its product brief
  remains an idea seed and its implementation is not a pilot prerequisite.
- Code with Branko: demonstrations and technical education that help engineers
  understand, evaluate, and apply the templates.

References: [ImContext product plan][context-imcontext], [ImCost][context-imcost],
and [Code with Branko][context-teaching]. These describe possible supporting
capabilities; their availability and benefit need validation before reliance.

[context-imcontext]:
  https://github.com/Imbra-Ltd/imbra-explore/blob/main/projects/im-context/IMCONTEXT.md
[context-imcost]:
  https://github.com/Imbra-Ltd/imbra-explore/blob/main/projects/im-cost/IMCOST.md
[context-teaching]:
  https://github.com/Imbra-Ltd/imbra-explore/blob/main/projects/codewithbranko/CODEWITHBRANKO.md

### 3.6 Customer-driven priorities

Prioritize work that reduces delivery effort, preserves correctness, removes an
adoption obstacle, or makes customization and feedback easier. Architecture work
needs a causal connection to one of these outcomes.

Start with one supported stack and expand when users demonstrate an unmet need
and the evaluation shows useful outcomes. If users do not save effort, investigate
and improve the experience before expanding the catalogue or delivery channels.

Use existing work instead of creating a new hierarchy of initiatives: #1184 owns
effectiveness evidence, #1511 quality goals, #414 skill evaluation, and #1512
intake. The generic evaluation method in Imbra exploration issue #281 is complete
and its handoff exists; it is no longer a pending prerequisite for #1184.

## 4. Core concepts

### 4.1 Policy

A rule or decision criterion describing what must or should be true of
engineering work or resulting software.

### 4.2 Skill

A reusable procedure describing how an agent performs a particular task.

Examples include migration, release, security review, and incident analysis.

### 4.3 Workflow

A sequence describing how work is scheduled, coordinated, and handed between
people, agents, or systems.

### 4.4 Policy pack

A versioned group of policies distributed together, such as an organization,
platform, language, or stack pack.

### 4.5 Target or adapter

An output representation for a coding-agent ecosystem, such as `AGENTS.md`,
`CLAUDE.md`, Cursor rules, or GitHub Copilot instructions.

### 4.6 Normalized policy

The deterministic, effective policy representation after dependency resolution,
precedence, extensions, overrides, conflict detection, and provenance capture,
but before target rendering.

### 4.7 Kernel, catalogue, skills, and enforcement

The target content model has four layers:

```text
Kernel
  Minimal policy needed on nearly every agent turn

Catalogue
  Detailed policy loaded only for relevant projects, paths, or tasks

Skills
  Reusable procedures loaded for particular work

Enforcement
  Linters, schemas, tests, CI, and architecture checks
```

This distinction prevents every useful lesson from becoming permanent prompt
context.

## 5. Product boundary

### 5.1 SOLID-AI owns

- engineering standards;
- architecture conventions;
- language and framework conventions;
- security and quality policy;
- relevant infrastructure conventions;
- organization policy and project overrides;
- policy composition and precedence;
- validation and conflict detection;
- provenance and explainability;
- target-specific compilation;
- policy compliance evaluation.

### 5.2 SOLID-AI does not own

- product requirements management;
- feature specification methodology;
- issue tracking;
- general project management;
- generic task decomposition;
- generic agent planning;
- multi-agent orchestration;
- general-purpose prompt libraries;
- CI infrastructure itself.

Workflow guidance belongs in SOLID-AI only when it expresses engineering policy
or is packaged as an explicitly invoked skill.

### 5.3 Position among adjacent systems

| Concern | Appropriate abstraction |
|---------|--------------------------|
| What are we building? | Specification and intent |
| How should an agent perform a task? | Skill or methodology |
| What rules must the result satisfy? | **SOLID-AI policy** |
| How is work orchestrated? | Planning and orchestration tooling |
| Is the result correct? | Tests, CI, security, and policy evaluation |

SOLID-AI should integrate with the adjacent abstractions rather than imitate
them.

Evaluate the combined toolchain on the same reference tasks with and without
SOLID-AI. Its contribution should improve the team's outcomes without requiring
replacement of their specification method, agent runner, or test infrastructure.

## 6. Current features and assets

The current repository provides:

- 75 Markdown template files;
- core, language, workflow, security, infrastructure, data, backend, frontend,
  platform, and stack concerns;
- 17 generated stack chains;
- Python, Go, Node.js, Astro, HTMX, gRPC, and embedded C coverage;
- a dependency manifest;
- core-tier inclusion and transitive dependency resolution;
- section-level extension and override directives;
- direct, interview, reference, inline, and hybrid consumption concepts;
- generated `CLAUDE.md` or `AGENTS.md` examples;
- smoke, conformance, and agent E2E test infrastructure;
- redundancy auditing;
- ADR, playbook, onboarding, audit, and journal records.

These assets should become migration fixtures. They should not be discarded in
a clean-slate rewrite.

## 7. Proposed product features

### 7.1 Explicit project configuration

Introduce a canonical `solid-ai.yaml`:

```yaml
version: 1

stack: stack.python.fastapi
platform: platform.github

extras:
  - workflow.release
  - workflow.quality-gates
  - security.devsecops
  - infra.containers

organization:
  - org.imbra

targets:
  - agents
  - claude
```

Keep the first schema small. Profiles, policy pins, path scopes, and lockfile
semantics can follow after the compiler stabilizes.

### 7.2 Stable policy identity

Filesystem paths should not become the external contract.

Prefer:

```text
core.testing
stack.python.fastapi
platform.github
```

over:

```text
templates/base/core/testing.md
templates/stack/python-fastapi.md
```

Stable IDs permit file moves without breaking consumers.

### 7.3 Deterministic resolver

Input:

- policy catalogue;
- `solid-ai.yaml`.

Output:

- ordered, deduplicated policy graph;
- conflicts and diagnostics;
- dependency and provenance paths.

Required behaviour:

1. Load selected policies.
2. Validate IDs.
3. Traverse dependencies.
4. Detect missing dependencies and cycles.
5. Detect explicit incompatibilities.
6. Deduplicate nodes.
7. Topologically order the graph.
8. Apply deterministic same-level ordering.
9. Retain resolution provenance.

The resolver must not depend on filesystem order or LLM interpretation.

### 7.4 Composition engine

Preserve explicit section-level composition:

```markdown
## Testing strategy
[ID: core-testing-strategy]
```

```markdown
## Python testing
[EXTEND: core-testing-strategy]
```

```markdown
## Organization testing
[OVERRIDE: core-testing-strategy]
```

`EXTEND` preserves and adds. `OVERRIDE` replaces. Unknown targets fail. Two
applicable equal-precedence overrides of the same rule also fail.

### 7.5 Precedence

Initial precedence, lowest to highest:

```text
core
  -> concern or layer
  -> language
  -> platform
  -> stack
  -> organization
  -> project
```

This ordering is directional until ratified by the system specification and an
ADR.

### 7.6 Normalized model

The compiler should produce one internal model consumed by all adapters.

Conceptually:

```python
PolicySet(
    schema_version=1,
    policies=[...],
    sections=[...],
    provenance={...},
    capabilities={...},
)
```

A section retains identity, content, source, extensions, override, and lineage.
Exact classes are implementation details.

### 7.7 CLI

Phase-one commands:

```text
solid-ai init
solid-ai resolve
solid-ai build
solid-ai validate
solid-ai explain
```

Later commands:

```text
solid-ai test
solid-ai diff
solid-ai update
```

`init` may use AI for repository inference and unresolved questions. `resolve`,
`build`, and deterministic validation should require no AI call.

### 7.8 Output adapters

Initial targets:

- `AGENTS.md`;
- `CLAUDE.md`.

Later targets:

- Cursor project and path-scoped rules;
- GitHub Copilot repository and path-specific instructions;
- other agent-native formats;
- Agent Skills for genuinely procedural content.

An adapter may change representation but not engineering meaning.

### 7.9 Explainability and provenance

Every effective rule should retain:

- defining policy and version;
- dependency path;
- extensions and overrides;
- source pack;
- organization or project origin.

Example:

```text
Rule: backend-http-timeout

Defined:    backend.http@1.3.0
Included:   stack.python.fastapi -> stack.python.service -> backend.http
Extended:   org.imbra.networking@2.1.0
Effective:  Outbound HTTP requests MUST define an explicit timeout.
```

### 7.10 Organization overlays

Organizations should be able to add approved libraries, architecture
boundaries, security gates, API conventions, logging requirements, and
deployment restrictions without forking upstream policy.

Organization packs should eventually be independently versionable and
privately distributable.

### 7.11 Context optimization

Support compact, full, reference, hybrid, and eventually path-scoped profiles.

Possible commands:

```text
solid-ai build --profile compact
solid-ai build --profile full
```

Optimization may deduplicate, filter by relevance, change layout, and report
token contribution. It must not silently weaken mandatory policy.

### 7.12 Behavioural policy testing

Structural compilation proves that policy was assembled correctly. It does not
prove that an agent follows it.

Policies should eventually carry representative scenarios:

```yaml
tests:
  - id: fastapi-layer-boundary
    task: Add an endpoint that loads a user by ID.
    assert:
      - router_does_not_access_database_directly
      - service_or_repository_boundary_used
```

Evaluation results must identify policy, adapter, agent, model, model version,
and scenario suite. Prefer deterministic assertions; keep optional LLM judges
explicitly separate.

### 7.13 Distribution and trust

Near term:

- clone, submodule, or vendored policy;
- organization directories;
- pinned repository versions.

Later:

- external and private packs;
- lockfile;
- hashes and signatures;
- explicit trust policy;
- registry.

Do not build a registry before schema, resolver, normalized model, composition,
compiler, and validation semantics are stable.

## 8. Practical adoption scenarios

### 8.1 New FastAPI service

Use `stack-fastapi` with project-appropriate security, data, scope, and platform
modules. Keep the always-loaded file concise:

```markdown
## Commands

- Install: `uv sync`
- Test changed code: `uv run pytest path/to/test.py`
- Verify: `uv run ruff check . && uv run mypy src && uv run pytest`

## Architecture

- Routes validate transport concerns only.
- Application services own use cases.
- Domain code does not import FastAPI or SQLAlchemy.
- Repository implementations own persistence.

## Safety boundaries

- Present a plan before changing authentication, billing, migrations, CI, or
  secrets handling.
```

Detailed procedures remain referenced or task-scoped. CI enforces formatting,
typing, tests, migrations, and dependency direction.

### 8.2 Refactoring a Flask monolith

Use `stack-flask` to describe the desired architecture, not to claim the legacy
system already complies.

1. Inventory entry points, dependencies, side effects, and tests.
2. Add characterization tests around preserved behaviour.
3. Define the target architecture.
4. Refactor one vertical slice at a time.
5. Separate structural work from upgrades and product changes.

Templates provide a target and review policy. They do not discover hidden
legacy behaviours on which users depend.

### 8.3 Rewriting Express in Go

Use source and destination profiles, but make executable contracts authoritative:

- OpenAPI or protocol contract;
- behavioural tests against both systems;
- data compatibility and reconciliation;
- performance baseline;
- feature-parity tracking;
- cutover and rollback procedures.

Prefer a strangler migration over a one-shot rewrite.

### 8.4 Modernizing a Python library

Use `stack-python-lib`, inventory the public API, add compatibility tests, and
introduce linting, typing, packaging, examples, and release automation
incrementally.

Public imports remain contracts, removals use deprecation, and examples should
be smoke-tested.

### 8.5 Security hardening

Compose stack, security, DevSecOps, authentication, configuration, CI/CD, and
container concerns. Begin with a read-only audit that requires evidence,
exploitability, severity, smallest remediation, and a verification test.

Only approved findings become implementation work.

## 9. Alternatives and complements

| Approach | Best use | Relationship to SOLID-AI |
|----------|----------|--------------------------|
| Hand-maintained agent file | Few distinct repositories | Simpler until repetition and drift appear |
| Cursor rules | Path- and task-scoped guidance | Compilation target |
| GitHub Copilot instructions | Repository and organization guidance | Compilation target |
| Skills and custom agents | Repeatable specialized procedures | Complements persistent policy |
| Cookiecutter, Copier, Backstage | Working project scaffolds | Creates artefacts policy later governs |
| Semgrep, CodeQL, OPA, architecture tests | Deterministic enforcement | Replaces enforceable prose |
| Agent orchestration | Parallel issue-to-PR execution | Consumes policy but remains outside core |

A mature environment combines them:

```text
Scaffolder       -> creates a working repository
SOLID-AI         -> compiles repository policy
Scoped rules     -> load relevant context
Skills           -> define procedures
CI and tests     -> verify outcomes
Agent platform   -> executes isolated work
Human review     -> controls risk and what ships
```

### 9.1 Competitor mechanisms selected for v3.0

The owner selects the following adaptations for
[v3.0 — Restructure](https://github.com/braboj/solid-ai-templates/milestone/8)
on 2026-09-06. They address the customer needs in section 3 and refine the
features in section 7. They are planned work, not shipped capabilities.

The findings come from source and workflow-template inspection. Competitor code
was not executed, and feature availability does not establish improved outcomes.
Source links below pin the inspected revisions so later changes do not alter the
evidence behind these notes.

| Customer need | Inspected mechanism | v3.0 adaptation and acceptance evidence |
|---------------|---------------------|----------------------------------------|
| Custom templates fail clearly when invalid | OpenSpec validates schema shape, duplicate IDs, missing references, and cycles before resolution | Share manifest validation between tools and checks. Reject invalid inputs before producing output; report the missing dependency or full cycle path. Exercise invalid references, duplicates, self/long cycles, and a valid diamond dependency. [Source][v3-os-schema] |
| Understand and customize inherited rules | Spec Kit resolves layers with source/version information and provides local authoring scaffolds | Explain inclusion paths and declared section overrides. Guide an engineer through one local template, validation, and reach preview using existing IDs and precedence. [Resolution][v3-sk-source], [scaffold][v3-sk-scaffold] |
| Load relevant guidance without accumulating generated content | Ruler excludes skills from ordinary rule concatenation, identifies generated inputs, and isolates target capabilities behind adapters | Separate persistent policy, task procedures, and generated artifacts. Render proposed outputs before applying them. Verify repeat generation does not ingest its own output; test loading in each supported agent. [Discovery][v3-ruler-read], [adapters][v3-ruler-adapters] |
| Update or remove templates without losing local work | Ruler previews output operations and supports original backups and revert | Provide a full diff, retain originals, and compare current content with the last generated digest before replacement/removal. Preserve local edits and report conflicts. Exercise repeated apply, unchanged output, edited output, and selective removal. [Writes][v3-ruler-backup], [revert][v3-ruler-revert] |
| Report defects and conceptual friction easily | OpenSpec combines guided report preparation with a submission command | Default to an editable local draft containing selected version/stack/rule context and expected/actual behavior. Suggest related reports; submit the reviewed draft under explicit authorization. Exercise incomplete reports, duplicates, and sensitive-content exclusion. [Workflow][v3-os-feedback], [command][v3-os-submit] |
| Concentrate on behavior while routine implementation is verified | BMAD separates an intent contract from implementation planning, verification, review triage, and terminal status | Integrate a bounded implementation/check/repair trial with an existing runner. Preserve agreed behavior, return verification evidence and unresolved decisions, and enforce time/retry limits in the runner. [Intent][v3-bmad-intent], [review][v3-bmad-review] |

At SAT revision `93de71d55096fd0747e1a23811d0479a6adb28d6`, in-memory
fixtures for `tools/resolve.py` confirmed the first gap: a valid dependency
returned files in dependency order, a missing dependency was silently omitted,
and a cycle raised `RecursionError` without a named cycle diagnostic. Smoke
already checks manifest references; direct resolution needs the same validation.

### 9.2 Boundaries and improvements over the inspected mechanisms

- Preserve independent resolution roots and the existing section-ID contract.
  Runtime validation does not require a folder move or new root-composition model.
- SAT currently concatenates source material and relies on the agent for the
  final merge. Explain declared overrides honestly; deterministic semantic
  composition requires the compatibility work in sections 18 and 21. Spec Kit's
  additional composition strategies are not required for this adaptation.
- Ruler's inspected revert recognizes generated ownership using markers and
  sidecars; it does not establish that the current output is locally unmodified.
  Add digest-based drift detection. Its operation preview also does not substitute
  for a full textual diff or establish all-or-nothing writes.
- OpenSpec's review/anonymization step is an agent instruction; the inspected CLI
  can submit directly when authenticated. Keep draft preparation separate from
  submission, and select diagnostic fields explicitly rather than collecting
  environment variables, whole transcripts, or project source automatically.
- BMAD's inspected review template limits a spec-repair loop to five iterations,
  but this is an instruction to the agent, not a global execution budget enforced
  by code. Verification results must support completion; a status label alone
  does not prove it. Intent ambiguity returns to the engineer.
- Use proportional review and deduplicate findings before considering tickets.
  BMAD's per-finding logs and append-only deferred entries are not adopted as
  mandatory artifacts. Deferred observations do not automatically become issues
  or ADRs; sections 22.4 and 22.5 govern the intake boundary.

### 9.3 v3.0 delivery order and outcome checks

1. Harden runtime validation and diagnostics in the existing resolver.
2. Add inclusion explanations and a guided local customization example.
3. Separate rendering from writes and establish output/loading boundaries.
4. Add preview, local-edit protection, and reversible update/removal.
5. Add draft-based reporting for users exercising those workflows.
6. Trial the bounded behavior-driven loop through an existing runner, retaining
   policy and verification ownership in SOLID-AI and orchestration outside core.

Run the reference evaluation from #1184 alongside this work. Compare accepted
outcomes and human effort with concise handwritten guidance and a relevant
existing workflow. Reuse #1511 for quality scenarios, #414 for skill evaluation,
and #1512 for intake rather than creating a ticket per borrowed mechanism.
Choose a small set of agent targets from actual use; no new registry, marketplace,
or general orchestration framework is a prerequisite for this v3.0 scope.

[v3-os-schema]: https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/src/core/artifact-graph/schema.ts#L23
[v3-sk-source]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/src/specify_cli/presets/__init__.py#L5719
[v3-sk-scaffold]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/presets/scaffold/README.md#L14
[v3-ruler-read]: https://github.com/intellectronica/ruler/blob/0fa2caeef4efaef4c5f8ffbedee8feca4b0b00e2/src/core/FileSystemUtils.ts#L319
[v3-ruler-adapters]: https://github.com/intellectronica/ruler/blob/0fa2caeef4efaef4c5f8ffbedee8feca4b0b00e2/src/agents/IAgent.ts
[v3-ruler-backup]: https://github.com/intellectronica/ruler/blob/0fa2caeef4efaef4c5f8ffbedee8feca4b0b00e2/src/core/FileSystemUtils.ts#L492
[v3-ruler-revert]: https://github.com/intellectronica/ruler/blob/0fa2caeef4efaef4c5f8ffbedee8feca4b0b00e2/src/core/revert-engine.ts#L164
[v3-os-feedback]: https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/src/core/templates/workflows/feedback.ts#L25
[v3-os-submit]: https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/src/commands/feedback.ts#L271
[v3-bmad-intent]: https://github.com/bmad-code-org/BMAD-METHOD/blob/abe4eb1bce919c9d22cd18b3519353d5824c4b75/skills/bmad-build-auto/spec-template.md
[v3-bmad-review]: https://github.com/bmad-code-org/BMAD-METHOD/blob/abe4eb1bce919c9d22cd18b3519353d5824c4b75/skills/bmad-build-auto/step-04-review.md

## 10. How AI-first engineering operates

The intended operating model lets a small team concentrate on defining and
testing the system while agents perform routine implementation and code review.

| Participant | Responsibility |
|-------------|----------------|
| Engineering team | Develop specifications and architecture; define test expectations; perform acceptance testing; resolve design ambiguity and decide what is ready to ship |
| Coding and review agents | Implement the agreed change, add appropriate implementation tests, run checks, review the actual diff, repair verified defects, and return evidence or unresolved questions |
| SOLID-AI | Supply relevant engineering policy, composition and override rules, and verification guidance that work with the team's tools |
| Specification tools, agent runners, and CI | Carry specifications, execute isolated work and automated checks, enforce configured limits, and expose results to the team |

```text
Team: specifications + architecture + test expectations
      -> agreed change and engineering policy
      -> agents: implement -> check -> review -> repair
      -> evidence or unresolved design questions
      -> team: acceptance testing and delivery decision
```

The loop is bounded by the team's scope and the runner's execution limits.
Agents escalate ambiguous intent, architectural changes outside that scope, and
verification failures they cannot resolve. They preserve the agreed acceptance
criteria instead of weakening tests to obtain a pass. Routine code review is
delegated; human intervention is driven by unresolved questions and the team's
chosen boundaries rather than a mandatory duplicate review of every change.

Repositories must be legible to machines: predictable structure, deterministic
commands, explicit boundaries, schemas, searchable documentation, reproducible
environments, and actionable errors.

Repeated failures should improve the harness through a better instruction,
example, tool, test, architectural constraint, permission, or signal. Generated
code volume is not a success measure; accepted outcomes are.

## 11. Policy quality assessment

### 11.1 Overall finding

The composition architecture is stronger than the current policy corpus. A
small group of high-reach base files has become encyclopedic and overly
absolute.

Desired shape:

```text
rule -> decision criteria -> exceptions -> verification
```

Current accretion often looks like:

```text
rule -> explanation -> historical failure -> edge cases -> recipe -> new rule
```

Primary authoring principle:

> One rule, minimum sufficient explanation.

### 11.2 Largest policy-quality concerns

| Rank | Template | Approx. size | Quality | Main concern |
|-----:|----------|-------------:|--------:|--------------|
| 1 | `base/workflow/quality-gates.md` | 62 KB | 4/10 | Encyclopedic implementation mandates |
| 2 | `base/core/docs.md` | 65 KB | 4.5/10 | Documentation governance became a handbook |
| 3 | `base/core/git.md` | 53 KB | 5/10 | Git invariants mixed with incident procedures |
| 4 | `base/core/quality.md` | 51 KB | 5.5/10 | Principles buried under special cases |
| 5 | `base/core/testing.md` | 47 KB | 6/10 | One test philosophy over-generalized |
| 6 | `base/workflow/ai-workflow.md` | 39 KB | 6/10 | Policy, tutorial, and methodology mixed |
| 7 | `base/workflow/360.md` | 21 KB | 6.5/10 | Heavy default procedure |
| 8 | `base/core/review.md` | 19 KB | 7/10 | Useful but oversized |

Smaller language, backend, platform, and stack-specific templates generally
demonstrate healthier scope.

### 11.3 `quality-gates.md`

Its editor, pre-commit, CI, and review model is strong. The file then turns good
defaults into universal mechanisms. Prefer capability-oriented policy:

> Projects must provide reproducible local verification for checks required
> before merge. Pre-commit hooks should be used when they provide low-friction
> enforcement.

This states the outcome without forcing one tool.

### 11.4 `docs.md`

It mixes rule language, source-of-truth policy, README, security, onboarding,
playbook, ADR, and synchronization governance.

Candidate split:

```text
core/docs.md
docs/readme.md
docs/security.md
docs/onboarding.md
docs/playbook.md
docs/adr.md
```

Only applicable concerns enter a chain.

### 11.5 `git.md`

Keep universal Git invariants in core. Move closing-keyword details, generated
artefact recovery, conflict recipes, release operations, and uncommon controls
into narrower modules or skills.

### 11.6 `quality.md`

Keep DRY, KISS, YAGNI, evidence-based abstraction, and justified complexity.
Rewrite universal prohibitions as decision criteria where literal application
would cause overengineering.

For example, replace a universal ban on boolean parameters with guidance to
avoid them when they select materially different behaviour and obscure the call
site.

### 11.7 `testing.md`

Focus on confidence, behavioural boundaries, determinism, and meaningful test
doubles. Do not make mocks mandatory or define acceptance criteria as inherently
manual.

### 11.8 `MUST` inflation

RFC 2119 language is useful, but an AI agent treats large numbers of `MUST`
statements as behaviour programming.

Proposed threshold:

> `MUST` means violation makes the engineering result objectively unacceptable
> or violates an explicit project constraint.

Everything else should normally be `SHOULD`, `SHOULD NOT`, or a decision rule.

### 11.9 Policy-authoring principles

1. One rule, one authoritative home.
2. Load only what applies.
3. Use minimum sufficient explanation.
4. Reserve `MUST` for genuine invariants.
5. Prefer decision criteria over blanket prohibitions.
6. Policy states outcomes; skills and playbooks state procedures.
7. Incidents should produce tests before permanent global rules.
8. Finish locally; backlog deliberately.
9. Every rule must justify its attention cost.
10. Optimize for agent behaviour, not handbook completeness.

## 12. Measured technical debt

### 12.1 Repository and tracker snapshot

Measurements taken on 2026-09-01:

| Metric | Value |
|--------|------:|
| Issues created | 711 |
| Issues closed | 636 |
| Issues open | 75 |
| Open and unmilestoned | 61 |
| Open P1/P2/P3 | 1 / 37 / 37 |
| Open bugs/tasks/spikes/epics | 11 / 46 / 17 / 1 |
| Template Markdown | 75 files / 17,576 lines |
| Generated chains | 17 files / 115,159 lines |
| Test specifications | 51 files / 3,893 lines |
| Numbered ADRs | 35 files / 3,557 lines |
| Section IDs | 367 occurrences |
| `MUST` / `MUST NOT` / `SHOULD` | 748 / 100 / 104 |
| Runnable shell or Python fences | 38 |

Generated chains range from approximately 270 KB and 5,385 lines to 457 KB
and 9,574 lines.

### 12.2 Issue flow

| Month | Created | Closed | Net |
|-------|--------:|-------:|----:|
| 2026-03 | 5 | 0 | +5 |
| 2026-04 | 29 | 31 | -2 |
| 2026-05 | 160 | 127 | +33 |
| 2026-06 | 170 | 184 | -14 |
| 2026-07 | 100 | 44 | +56 |
| 2026-08 | 212 | 234 | -22 |
| 2026-09 through September 1 | 35 | 16 | +19 |

The backlog does not grow monotonically. Closure capacity is high, but new work
arrives in large audit and release bursts.

### 12.3 Release correlation

| Tag | Tagged UTC | Open issues at tag |
|-----|------------|-------------------:|
| `v2.64.0` | 2026-08-29 07:23 | 52 |
| `v2.65.0` | 2026-08-29 08:19 | 50 |
| `v2.66.0` | 2026-08-31 07:23 | 55 |
| `v2.67.0` | 2026-08-31 08:07 | 55 |
| `v2.68.0` | 2026-08-31 08:24 | 53 |
| `v2.69.0` | 2026-09-01 07:11 | 56 |
| `v2.70.0` | 2026-09-01 07:37 | 57 |
| `v2.71.0` | 2026-09-01 11:28 | 72 |
| `v2.72.0` | 2026-09-01 14:19 | 70 |

Nine minor releases landed in four calendar days. The `v2.71.0` audit reported
140 findings and filed nineteen issues after its release work closed six.

### 12.4 Debt categories

#### Policy debt

- oversized high-reach templates;
- excessive absolute rules;
- local incidents generalized globally;
- insufficient deletion and expiry;
- procedures mixed into persistent policy;
- loaded but irrelevant content.

#### Composition debt

- graph semantics described in multiple places;
- more than one manifest interpretation;
- file paths acting as identity;
- LLM-dependent merge and conflict handling;
- generated artefacts rewritten across branches.

#### Validation debt

- extensive structural checks but stale live E2E;
- internal correctness mistaken for user outcome evidence;
- behavioural compliance weakly measured;
- checks and dispositions recursively governing each other.

#### Documentation debt

- repeated procedures across templates and playbooks;
- large audit and journal surfaces;
- counts and claims requiring synchronization;
- ADR and documentation density disproportionate to product capability.

#### Backlog debt

- every actionable audit finding becomes an issue;
- unscheduled issues remain permanently active;
- the whole unmilestoned set is repeatedly reread;
- no backlog cap or admission economics;
- meta-governance issues compete with adopter features.

#### Product debt

- no canonical installed compiler experience;
- limited output adapters;
- no stable project configuration;
- no upgrade/diff workflow;
- compact and scoped output incomplete;
- behavioural proof behind policy growth.

## 13. Backlog-amplification diagnosis

The current feedback loop is:

```text
Downstream incident
  -> reusable-rule proposal
  -> template + check + docs + disposition
  -> minor release
  -> release-triggered audit
  -> findings
  -> issue per actionable finding
  -> more downstream and meta-policy work
```

Root causes:

1. Audit policy optimizes for recall, not issue admission value.
2. Frequent minor releases trigger further whole-project review.
3. The repository applies consumer rules to itself beyond useful similarity.
4. A downstream incident has a low threshold for global promotion.
5. Rules grow monotonically in practice.
6. Unmilestoned work is treated as permanently active.
7. Duplicated truth creates new drift surfaces.
8. Governance work has become easier to justify than adopter capability.

More issues can reveal existing debt, so issue count alone is not quality.
However, a healthy mature design should reduce marginal change cost and show a
flattening rate of governance defects. The current system does not yet converge.

## 14. Risks

### 14.1 Current-system risks

#### Attention dilution

Agents must reconcile too many independent instructions. Relevant rules may be
buried even when the context window can technically hold the profile.

#### Pathological literalism

Hundreds of `MUST` statements can drive overengineering or irrelevant work.

#### False confidence

Green structural tests can be mistaken for evidence that policies improve agent
outcomes.

#### Recursive governance

Rules about checks, dispositions, audits, and release controls generate more
policy surfaces than they retire.

#### Backlog exhaustion

The tracker becomes an anxiety inventory rather than a set of plausible
commitments.

#### Product displacement

Maintainers can spend most available time keeping policy internally consistent
instead of delivering a usable compiler and adapters.

#### Supply-chain risk

Future remote policy can inject unsafe instructions or change behaviour without
review unless versions, hashes, provenance, and explicit trust are present.

### 14.2 Correction risks

#### Hiding real debt

Closing low-value issues must not delete evidence. Persist findings in audits
and link consolidated issues back to them.

#### Overcompression

A smaller prompt can omit load-bearing policy. Compression must be evaluated
against agent outcomes, not bytes alone.

#### More governance to reduce governance

Do not give every admission rule its own metadata, checks, dispositions, and
ADRs before the simple human policy has been tested.

#### Misclassification

A manifest or generator issue may be directly adopter-visible. Classify by user
impact, not filename.

#### Lost downstream learning

Quarantine new observations rather than discarding them. Promote only after the
evidence threshold is met.

#### Simultaneous compiler and policy rewrite

Changing semantics and implementation together makes parity impossible to
establish. Use existing content as fixtures while mechanics migrate.

## 15. Stabilization proposals

These are candidate controls, not approved permanent policy.

### 15.1 Stop automatic issue conversion

Record every verified audit finding, but create an issue only when the finding:

- is P0 or P1;
- is selected for the next two milestones;
- recurs across independent projects;
- or has an observable activation trigger.

Group multiple manifestations under one mechanism-level issue.

### 15.2 Add backlog admission limits

Trial limits:

- at most 30 open issues;
- at most 15 open unmilestoned issues;
- at most five active meta-governance issues;
- no new P3 unless another P3 is closed, merged, or rejected.

At the cap, new work must replace, merge into, or outrank existing work.

### 15.3 Freeze universal-rule additions

For two to four weeks, accept only:

- P0/P1 correctness fixes;
- policy consolidation and deletion;
- measurable adopter capability;
- outcome-evaluation infrastructure.

Collect downstream observations without immediately promoting them.

### 15.4 Slow the release train

- Use patch releases for corrections.
- Reserve minor releases for adopter capabilities.
- Permit at most one minor release per week during stabilization.
- Move toward a planned monthly minor release.
- Run 360 reviews quarterly, before major releases, or after major milestones.

### 15.5 Apply a complexity budget

Trial constraints:

- no more than 10K tokens of always-loaded context;
- no net core-rule growth during stabilization;
- a new core rule replaces, merges, or removes existing content;
- every minor release reports instruction tokens added and removed;
- policy growth remains net-negative until the budget is met.

### 15.6 Promote rules through evidence

A widely shared rule should require:

1. Recurrence in two independent projects or one severe incident.
2. No stronger remedy in code, types, configuration, tests, or CI.
3. A demonstrated agent failure without the instruction.
4. Measurably better behaviour with the instruction.
5. Known applicable stacks or paths.
6. Available context budget.

A single-project lesson defaults to local project policy.

### 15.7 Finish locally; backlog deliberately

Correctness, acceptance criteria, tests, and documentation consistency belong
in the current change. A follow-up issue should represent independently valuable
work outside accepted scope, not every possible improvement.

## 16. Outcome evaluation

Before further policy expansion, establish a stable benchmark:

- three representative consumer projects;
- ten to twenty real tasks;
- compact versus full profiles;
- with-policy versus without-policy;
- at least two agent or model families.

Measure:

- task completion;
- tests passing;
- relevant instruction adherence;
- unnecessary modifications;
- review corrections;
- regressions introduced;
- tokens, latency, time, and cost.

Candidate admission rule:

> No reproduced incident or failing evaluation, no new universal rule.

Structural smoke tests remain necessary. A minor release should also carry a
recent live outcome evaluation.

## 17. Target compiler architecture

```text
CLI
  |-- project discovery
  `-- initialization/interview
        |
Configuration loader
        |
Policy catalogue loader
        |
Dependency resolver
        |
Policy parser
        |
Composition engine
        |
Validator
        |
Normalized policy model
        |-- explain engine
        |-- test engine
        `-- adapters
              |-- AGENTS
              |-- Claude
              `-- future targets
```

Core rule:

> Use AI for semantic judgement. Use deterministic code for deterministic
> mechanics.

Code owns schema, dependency traversal, ordering, precedence, cycle detection,
conflict detection, composition, and rendering mechanics. AI may assist with
repository inference, interviews, explanations, semantic review, and optional
judging.

### 17.1 Validation levels

1. **Schema:** required metadata, IDs, values, and configuration.
2. **Graph:** missing dependencies, cycles, and incompatibilities.
3. **Composition:** duplicate rules, missing targets, and override collisions.
4. **Output:** duplicates, unresolved metadata, malformed targets, and size.
5. **Semantic linting:** later detection of contradiction, vagueness,
   duplication, obsolete versions, and policy that belongs in a skill.

Keep deterministic validation distinguishable from heuristic or LLM linting.

### 17.2 Error design

Diagnostics are a product feature. Errors should identify policy, rule, source,
cause, and remediation.

### 17.3 Performance

Ordinary resolve, validate, and build operations should feel instantaneous and
require no AI call. Prefer pure functions, one catalogue load, one graph
resolution, and parsed-policy reuse.

### 17.4 Security

Treat policy packs as software-supply-chain inputs. Do not silently fetch or
execute remote policy. Later controls include pins, hashes, provenance,
reviewable diffs, signatures, and explicit trust.

## 18. Migration strategy

Section 9 defines the selected v3.0 adaptations within this broader roadmap.
Establish the reference benchmark first and use it throughout; Phase 4 expands
verification rather than introducing outcome measurement for the first time.

### Phase 0: Stabilize

1. Freeze universal-rule growth.
2. Change audit-to-issue admission.
3. Apply temporary backlog and release limits.
4. Establish outcome baselines.
5. Begin policy compression.

### Phase 1: Freeze semantics

Document current intended behaviour for core inclusion, dependencies, extras,
platforms, ordering, `EXTEND`, and `OVERRIDE`.

Turn representative current stacks into fixtures:

```text
old expected chain == new resolver chain
```

Review every difference.

### Phase 2: Deterministic core

1. Validate the existing manifest.
2. Implement one canonical graph parser and resolver.
3. Parse Markdown with source locations and provenance.
4. Introduce the normalized model.
5. Implement extension, override, precedence, and conflicts.
6. Add schema, graph, composition, and output validation.
7. Introduce `solid-ai.yaml`.
8. Implement AGENTS and Claude adapters.
9. Add `resolve`, `validate`, `build`, and `explain`.
10. Move the interview behind `init`.
11. Retire LLM graph mechanics only after parity is demonstrated.

### Phase 3: Portability and explainability

- repository detection;
- streamlined interview;
- Copilot and scoped-rule adapters;
- organization overlays;
- richer explain output;
- context-budget reporting;
- compact and full profiles;
- schema migration;
- policy diff.

### Phase 4: Verification

- scenario metadata;
- task fixtures;
- agent runner abstraction;
- deterministic assertions;
- optional judge;
- model and policy version metadata;
- regression reporting;
- critical-policy suite;
- optional CI integration.

### Phase 5: Ecosystem

Only after core semantics stabilize:

- pack format;
- external and private sources;
- lockfile;
- registry;
- signatures;
- compatibility metadata;
- community contribution model.

## 19. Policy-compression plan

Prioritize high-reach files:

1. `base/workflow/quality-gates.md`
2. `base/core/docs.md`
3. `base/core/git.md`
4. `base/core/quality.md`
5. `base/core/testing.md`
6. `base/workflow/ai-workflow.md`

For each file:

- identify genuine invariants;
- downgrade unjustified `MUST`s;
- remove duplicate rules;
- extract procedures into skills or playbooks;
- extract narrow concerns into optional policies;
- remove narrative that does not alter agent decisions;
- convert prohibitions into decision criteria where appropriate;
- replace enforceable prose with checks;
- measure behaviour before and after compression.

A directional size target for the largest core files is 10-20 KB of high-signal
policy. Behavioural density and relevance matter more than bytes.

## 20. Backlog-reduction plan

Classify the 75 open issues:

| Group | Action |
|-------|--------|
| Consumer-visible correctness | Keep and prioritize |
| Product capability | Keep only when tied to the next outcome |
| Meta-governance | Consolidate by common mechanism |
| Speculative lesson or polish | Return to audit history and close |

Start with the 61 unmilestoned issues. Ask:

1. Is the claim still true?
2. Does an adopter experience the problem?
3. Is there a credible scheduling trigger?
4. Does the audit already preserve enough evidence?
5. Can it merge into a mechanism-level issue?
6. What existing work should it displace?

If an item has no credible trigger or planning horizon, close it as `wontdo`.
Audit, issue, and Git history retain the evidence.

## 21. Testing strategy

### 21.1 Compiler unit tests

Cover ID validation, graph functions, cycle detection, precedence, conflicts,
parsing, normalization, and adapters.

### 21.2 Golden and integration tests

For representative configurations:

```text
configuration
  -> expected graph
  -> expected normalized policy
  -> expected target output
```

### 21.3 Invariants

- resolution is deterministic;
- graphs contain no duplicate nodes;
- order respects dependencies;
- effective override targets exist;
- equal-precedence conflicts fail;
- generated output contains no internal directives;
- all adapters consume the same normalized model.

### 21.4 Behavioural tests

Run representative tasks and measure outcomes. Structural and behavioural tests
answer different questions and neither replaces the other.

## 22. Candidate success measures

These are proposed stabilization targets, not permanent requirements:

| Measure | Candidate target |
|---------|------------------|
| Open issues | 30 or fewer |
| Unmilestoned open issues | 15 or fewer |
| Active meta-governance issues | Five or fewer |
| Minor-release cadence | At most weekly, later monthly |
| Always-loaded context | 10K tokens or fewer |
| Live agent E2E | Every minor release and scheduled cadence |
| Governance work | At most 20% over a rolling period |
| Rule growth during stabilization | Net-negative |
| Audit issue conversion | High-value, scheduled, recurrent, or triggered only |
| Compiler determinism | Repeated builds byte-identical |
| Adapter parity | Same normalized meaning across targets |

These numeric targets are earlier proposals, not measured acceptance thresholds.
The 2026-09-05 discussion refines their interpretation below: reducing the number
of issues or releases is not itself evidence of quality. Do not close valid bugs
or delay useful fixes to satisfy these numbers.

### 22.1 Quality means useful outcomes at sustainable cost

High quality means agents complete real engineering work correctly, with fewer
recurring mistakes, at an affordable cost to understand, run, adopt, and maintain.
Structural correctness is necessary; it does not establish useful behaviour.

| Dimension | Evidence to seek |
|-----------|------------------|
| Correctness | Valid composition and precedence; no harmful conflicting instructions or lost user work |
| Effectiveness | Representative tasks complete correctly; changes reduce observable failures |
| Relevance | Selected policy fits the project and task without unrelated obligations |
| Efficiency | Context, elapsed time, retries, and adoption effort relative to outcomes |
| Predictability | Versioned changes and overrides have explainable effects and manageable migration |
| Maintainability | Lower recurring defects, reconciliation effort, and policy-induced work |

The change-admission question is: does this improve a demonstrated outcome enough
to justify the cost carried by affected consumers? Credible material risks,
including security risks, can justify prevention before an incident occurs.
One team's preference does not automatically justify a shared rule.

Measure baselines before choosing numerical targets. Report critical correctness
or safety failures separately; an average score must not conceal them. Counts of
rules, checks, ADRs, releases, or issues closed are activity measures, not proof
of quality. A smaller context is useful when it preserves or improves outcomes.

### 22.2 Representative quality scenarios

These are initial evaluation cases, not claims that the current system passes.
Each starts from a pinned fixture and records observable actions or artifacts.

| Context and stimulus | Expected response | Observable result |
|----------------------|-------------------|-------------------|
| A small library requests generated context | Include relevant policy and resolve project overrides correctly | Applicable rules present; overridden rules replaced; context size recorded |
| An agent receives a bounded code task | Complete the task with relevant checks | Task tests pass; unrelated files and tracker records remain untouched |
| A consumer starts with uncommitted edits | Preserve the user's work while making the requested change | Original edits survive; no unsolicited commit or publication |
| A newer template version becomes available | Assess applicability and adoption cost | No automatic compliance tickets or mandatory pin bump merely for a new tag |
| A maintainer moves an ordinary document | Update affected references | References work; no ADR created solely because a path changed |
| A consequential compatibility choice arises | Explain alternatives and durable consequences | Decision is reviewable; related work can share one qualifying ADR |

Compare baseline and candidate on the same task, model/settings, fixture, and
permissions. Include a minimal/no-template baseline when testing the value claim.
Use at least two representative stacks and repeat stochastic trials; record
revisions, failures, skips, variability, tokens, time, and retries. Include
sanitized consumer-derived cases where permitted. Evidence from related repos
under shared ownership supports the diagnosis, but is not an independent causal
experiment or proof that every consumer needs the same policy.

### 22.3 Tools and optional skills

Reuse the manifest/resolver, smoke tests, generated-file synchronization,
redundancy audit, chain budgets, and relevant CI/security checks. The missing
evidence is whether generated instructions improve agent behaviour: required
strings in a generated file alone do not prove that an agent follows them.

Start with a small behavioural suite. Run deterministic checks on relevant PRs,
a proportionate behavioural sample for rule changes, and broader evaluation
before material releases. Paid model execution on every documentation change
would add cost without corresponding evidence.

Three optional maintainer procedures merit trials:

- Triage a report: find evidence, versions, duplicates, and a useful disposition.
- Evaluate a change: compare observable outcomes, regressions, and consumer cost.
- Review a contribution: assess the actual diff, correctness, impact, and scope.

Package a procedure as a skill only if it helps in trials. Keep it outside the
always-loaded core. No change or an explained decline is a valid result; a skill
should not generate subissues, ADRs, or new rules merely to complete its steps.
Use existing tools before creating a new automation service or dashboard.

### 22.4 Intake when participation reaches 1,000 reporters

Incoming reports are evidence. Accepted work and scheduled commitments are
maintainer decisions. More contributors increase the need for triage; automation
does not increase implementation capacity by itself.

Use existing GitHub facilities to route questions and open ideas separately
from actionable defects/proposals, with private vulnerability reporting retained.
Request only what makes a report actionable: affected version and stack, expected
and actual behaviour, and reproduction or equivalent evidence.

Search issue bodies and relevant closed issues as well as titles. Consolidate
repeated reports under a canonical issue while preserving new evidence and
version-specific regressions. Apply a disposition: accept, bounded investigation,
needs information, duplicate, or decline. Valid requests may still be outside
scope. Schedule only work supported by available maintainer capacity, and state
the service level honestly rather than promising to implement every report.

Automation can suggest routes and duplicate candidates. Uncertain closures and
scope decisions remain with maintainers. Treat submitted text and code as
untrusted input; triage must not execute supplied commands or expose privileged
credentials. Do not close reproducible bugs solely because they are old.

Trial intake on a bounded sample with duplicates, incomplete reports, old valid
bugs, regressions, out-of-scope requests, and malicious instructions. Estimate
triage time under stated volume assumptions and compare accepted work with actual
capacity. Keep the response lightweight: no ticket per formatting defect, no
repeated audit of the entire backlog, and no universal downstream intake policy.

### 22.5 Preventing the feedback loop

The consumer review supports a reinforcing loop: local observations become shared
rules, releases trigger adoption work, and reconciliation produces more issues
and documentation. This is a mechanism diagnosis, not a claim that every issue
or ADR is waste. Correct the shared mechanism or remove a confusing rule before
adding exceptions. Selective adoption and a meaningful ADR threshold interrupt
the loop without discarding useful downstream evidence or architectural history.

Existing work owns the implementation:

- [#1511](https://github.com/braboj/solid-ai-templates/issues/1511): measurable
  quality goals and scenarios.
- [#1512](https://github.com/braboj/solid-ai-templates/issues/1512): bounded intake
  and triage; can ship before the v3.0 folder restructuring.
- [#1184](https://github.com/braboj/solid-ai-templates/issues/1184): effectiveness
  evidence, extended with the behavioural cases above.
- [#414](https://github.com/braboj/solid-ai-templates/issues/414): evaluate useful
  skills, extended with optional triage, evaluation, and contribution review.
- [#1368](https://github.com/braboj/solid-ai-templates/issues/1368): live test
  execution; [#368](https://github.com/braboj/solid-ai-templates/issues/368):
  latency measurement;
  [#1462](https://github.com/braboj/solid-ai-templates/issues/1462):
  chain-budget meaning.
- [#1353](https://github.com/braboj/solid-ai-templates/issues/1353) and
  [#1506](https://github.com/braboj/solid-ai-templates/issues/1506): selective
  adoption and ADR thresholds, with implementation proposed in
  [#1508](https://github.com/braboj/solid-ai-templates/pull/1508).
- [#1480](https://github.com/braboj/solid-ai-templates/issues/1480): shared core
  boundary; [#1504](https://github.com/braboj/solid-ai-templates/issues/1504):
  folder reorganization. Moving files alone does not reduce obligations.

### 22.6 Later arc42 placement

When these notes become architecture documentation, place the prioritized quality
goals in section 1 and the concrete quality scenarios in section 10. Put relevant
cross-cutting concepts in section 8 and unresolved amplification, evaluation,
and adoption risks in section 11. Section 9 links qualifying architectural
decisions; it does not turn each conclusion into a new ADR. Intake procedures
belong in contributor/maintainer guidance, referenced only where architecturally
relevant. Keep delivery status in issues rather than copying the tracker into
the architecture document.

## 23. Explicit non-goals and deferred features

Do not prioritize during stabilization and deterministic-core work:

- hosted SaaS;
- marketplace or registry;
- sophisticated UI;
- agent personas;
- multi-agent orchestration;
- generic task planning;
- issue-management dashboards;
- generic prompt marketplace;
- dozens of additional stack templates;
- premature remote-pack protocol;
- aggressive repository reorganization for aesthetics.

The current stack set is sufficient to exercise the architecture.

## 24. Working decisions and unresolved questions

### 24.1 Working direction from the temporary reports

These are consistent recommendations. The competitor-derived adaptations in
section 9 are selected for v3.0; other proposals retain their directional status:

- engineering policy is the core abstraction;
- agent files are compilation targets;
- explicit project configuration becomes the source of truth;
- deterministic mechanics move into code;
- one normalized model separates composition from rendering;
- organization overlays are first-class;
- policy, skills, and workflows remain distinct;
- validation is a first-class product feature;
- behavioural testing is the long-term differentiator;
- orchestration stays outside core;
- ecosystem work follows compiler stability;
- stabilization and subtraction precede broad policy expansion.

### 24.2 Open questions

1. Which reference tasks best measure the customer outcome defined in section 3?
2. Which current rules have behavioural evidence?
3. Which rules belong in the always-loaded kernel?
4. Which rules are actually skills or procedures?
5. Which rules can code, types, linters, or CI replace?
6. How many downstream projects consume each policy?
7. What share of recent issues came from adopters versus self-governance?
8. Should generated chains be committed or published as release artefacts?
9. What events genuinely justify a 360 audit?
10. What context budget applies to each target?
11. What should `wontdo` mean when evidence remains valuable?
12. Can internal projects supply evaluation tasks without exposing private data?
13. Where should policy metadata live?
14. How granular should policy modules become?
15. How should monorepo and path-specific policy work later?
16. What exact schema, lockfile, and remote-pack formats are appropriate?
17. Should compiler software and policy content use different licences?

## 25. Recommended decision sequence

Section 9.3 orders the selected v3.0 competitor adaptations within this broader
sequence. Runtime validation, explanation, and authoring improvements can proceed
before the full compiler migration.

1. Define the product outcome and boundary.
2. Decide whether to pause universal-rule growth.
3. Change audit-to-issue admission semantics.
4. Set temporary backlog and release limits.
5. Define the smallest useful behavioural benchmark.
6. Classify and reduce the existing backlog.
7. Approve the kernel/catalogue/skills/enforcement model.
8. Freeze current composition semantics.
9. Approve deterministic resolver and normalized-model ADRs.
10. Build and prove compiler parity.
11. Compress policy against behavioural evidence.
12. Add portability, organization, and ecosystem features later.

This sequence avoids building new machinery before deciding which outcome the
project optimizes.

## 26. Phase-one definition of done

This describes the compiler target, distinct from the semantics-freezing phase
in section 18. The first v3.0 improvements in section 9 can ship before the entire
target is complete.

Phase one is complete when a repository contains `solid-ai.yaml` and can run:

```text
solid-ai validate
solid-ai resolve
solid-ai build
```

with these guarantees:

- no AI required for compilation;
- deterministic dependency resolution;
- invalid graphs and conflicts fail clearly;
- `EXTEND` and `OVERRIDE` are deterministic;
- AGENTS and Claude targets use the same normalized policy;
- emitted rules retain provenance;
- representative current stacks are fixture-tested;
- compact output stays within an agreed context budget;
- live policy evaluation is current enough to guide policy changes.

## 27. Reproduction notes

Tracker metrics were collected with:

```powershell
gh issue list `
  --repo braboj/solid-ai-templates `
  --state all `
  --limit 2000 `
  --json number,state,createdAt,closedAt,title,labels,milestone
```

Release backlog counts compare issue creation and closure timestamps with
annotated tag times from:

```powershell
git for-each-ref `
  --sort=version:refname `
  --format='%(refname:short)|%(taggerdate:iso-strict)' `
  refs/tags
```

A rough title classification matched 51 of 75 open issues to terms associated
with rules, checks, releases, audits, documentation, manifests, templates, or
other governance. This measure overlaps categories and is directional only.

## 28. References

Repository sources:

- `templates/manifest.yaml`
- `templates/INTERVIEW.md`
- `templates/base/workflow/360.md`
- `templates/base/workflow/issues.md`
- `docs/SPEC.md`
- `docs/PLAYBOOK.md`
- `docs/audits/2026-09-01-360.md`
- `docs/meta/agent-context-tradeoffs.md`
- `docs/meta/template-content-quality.md`
- `docs/decisions/011-provenance-principle.md`
- `docs/decisions/033-periodic-review-scoped-to-minor-and-major.md`

External references retained from the practical assessment:

- [AGENTS.md open format](https://agents.md/)
- [Anthropic Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Cursor rules](https://docs.cursor.com/context/rules)
- [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/reference/custom-instructions-support)
- [OpenAI harness engineering](https://openai.com/index/harness-engineering/)
- [DORA 2025 AI-assisted development](https://dora.dev/research/2025/dora-report/)
- [METR developer productivity study](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf)

## 29. Hourglass architecture analysis

### 29.1 Principle

A healthy software hourglass has many producers above, many consumers below,
and one small stable contract between them:

```text
              MANY POLICY SOURCES
        standards / stacks / companies
      projects / plugins / private policies
                    \       /
                     \     /
                      \   /
                       \ /
                +----------------+
                |  NARROW WAIST  |
                | stable contract|
                +----------------+
                       / \
                      /   \
                     /     \
                    /       \
          MANY OUTPUTS AND CONSUMERS
       agents / IDEs / CI / evaluation
```

The waist should change slowly. Policy producers and policy consumers should be
able to evolve independently.

### 29.2 Current shape

The current SOLID-AI flow is approximately:

```text
                    POLICY INPUTS
     +-------------------------------------------+
     | base rules                                |
     | backend and frontend rules                |
     | language rules                            |
     | stack templates                           |
     | platform templates                        |
     | interview answers                         |
     | lessons from internal projects            |
     +-------------------------------------------+
                         |
                         v
     +-------------------------------------------+
     | manifest.yaml                             |
     | dependency graph                          |
     | ID / EXTEND / OVERRIDE                    |
     +-------------------------------------------+
                         |
                         v
     +===========================================+
     |              CURRENT WAIST                |
     |                                           |
     | LLM reads the dependency graph            |
     | LLM interprets precedence                 |
     | LLM resolves conflicts                    |
     | LLM merges policy                         |
     | LLM applies interview answers             |
     | LLM interprets output formatting          |
     | LLM chooses inline or reference content   |
     | large core templates always participate   |
     | governance rules participate              |
     +===========================================+
                         |
                         v
              +---------------------+
              | Generated Markdown  |
              |                     |
              | CLAUDE.md           |
              | AGENTS.md           |
              | reference / hybrid  |
              +---------------------+
                         |
                         v
              +---------------------+
              | Coding agent reads  |
              | generated policy    |
              +---------------------+
```

This resembles a funnel feeding a thick processing chamber rather than an
hourglass:

```text
       many inputs
    \              /
     \            /
      \          /
       \        /
        +------+
        |      |
        |      |  large policy corpus
        |      |  + composition logic
        |      |  + rendering logic
        |      |  + governance
        |      |  + LLM judgement
        +------+
           ||
           ||
       few outputs
```

The closest current approximation to a narrow contract is:

```text
manifest.yaml
      +
stable template and section IDs
      +
DEPENDS ON / EXTEND / OVERRIDE
```

This is a valuable structural foundation, but it is not a complete semantic
contract. It does not independently produce deterministic precedence, composed
sections, conflicts, normalized policy, provenance, context profiles, or
output-independent meaning. The LLM currently supplies those semantics.

### 29.3 Why the current waist expands

New downstream lessons frequently enter high-reach policy and then create
secondary obligations:

```text
Internal project incident
          |
          v
     new shared rule
          |
          v
  core or high-reach policy
          |
          +--> more prompt context
          +--> more composition interactions
          +--> more checks
          +--> more documentation
          +--> more audit surface
          `--> more issues
```

Instead of extending above or below the waist, new behaviour is placed inside
it:

```text
Ideal                          Current

\             /                \             /
 \           /                  \           /
  \         /                    \         /
   \       /                      +-------+
    \     /                       | rules |
     \   /                        | checks|
      \ /                         | docs  |
     [IR]                         | audit |
      / \                         | LLM   |
     /   \                        +-------+
    /     \                           ||
   /       \                          ||
```

This is the architectural expression of policy and backlog amplification.

### 29.4 Target hourglass

The target waist is a small normalized policy contract, not Markdown and not
the manifest alone:

```text
              POLICY PRODUCERS
 +-------------------------------------------+
 | SOLID-AI standard policy                  |
 | language and framework packs              |
 | security and infrastructure packs         |
 | organization-private packs                |
 | project overrides                         |
 | imported industry standards               |
 | third-party policy packs                  |
 +-------------------------------------------+
                      \   /
                       \ /
          +-----------------------------+
          |     SOLID-AI NARROW WAIST   |
          |                             |
          | PolicySet schema v1         |
          | stable policy and rule IDs  |
          | deterministic graph         |
          | composition semantics       |
          | precedence and conflicts    |
          | provenance                  |
          +-----------------------------+
                       / \
                      /   \
 +-------------------------------------------+
 |               POLICY CONSUMERS            |
 |                                           |
 | AGENTS.md          CLAUDE.md               |
 | Cursor rules       Copilot instructions   |
 | skills             IDE integrations       |
 | CI policy          architecture checks    |
 | explain and diff   behavioural evaluation |
 | future agents      internal company tools |
 +-------------------------------------------+
```

Conceptually, the waist exposes:

```text
PolicySet v1
|-- selected policies
|-- effective rules
|   |-- stable ID
|   |-- requirement
|   |-- applicability
|   |-- severity
|   `-- provenance
|-- conflicts
`-- metadata
```

Everything above compiles into `PolicySet`. Everything below consumes it.

### 29.5 Tight compiler core

The implementation surrounding the waist should also remain small:

```text
                 POLICY SOURCES
                       |
                       v
               +---------------+
               | Configuration |
               +---------------+
                       |
                       v
               +---------------+
               | Catalogue     |
               +---------------+
                       |
                       v
          +---------------------------+
          |       TIGHT CORE          |
          |                           |
          | parse                     |
          | resolve graph             |
          | compose                   |
          | validate                  |
          | normalize                 |
          +---------------------------+
                       |
                       v
               +---------------+
               | PolicySet v1  |  <-- narrow contract
               +---------------+
                       |
          +------------+------------+
          |            |            |
          v            v            v
       render        explain       evaluate
```

The core should not know Claude formatting, Cursor globs, GitHub organization
settings, or one company's engineering conventions.

### 29.6 Open above the waist

Many policy sources can implement one source contract:

```text
                       Policy source interface
                                |
          +---------------------+---------------------+
          |                     |                     |
          v                     v                     v
  Built-in catalogue     organization pack      project policy
          |                     |                     |
          +---------------------+---------------------+
                                |
                         normalized policy
```

Possible sources include built-in Markdown, YAML packs, private repositories,
vendored company policy, standards-derived packs, and plugins. All produce the
same normalized model.

### 29.7 Open below the waist

Many consumers can use one `PolicySet`:

```text
                         PolicySet v1
                              |
       +-----------+----------+----------+-----------+
       |           |          |          |           |
       v           v          v          v           v
   AGENTS.md   CLAUDE.md   Cursor     Copilot       CI
                                          |
                             +------------+-----------+
                             |                        |
                             v                        v
                      architecture tests      security checks
```

Adding an adapter should not require changes to policy sources or composition:

```text
Before:

PolicySet -> AGENTS
          -> Claude

After:

PolicySet -> AGENTS
          -> Claude
          -> Cursor
          -> Copilot
          -> future agent X
```

### 29.8 Skills and procedures

Skills sit below or beside policy rather than inside the waist:

```text
                        PolicySet
                            |
              +-------------+-------------+
              |                           |
              v                           v
        persistent rules           task procedures
              |                           |
              v                           v
     AGENTS / CLAUDE / CI       migration / release /
                               audit / incident skills
```

Policy says:

```text
Database migrations must be reversible.
```

A migration skill says:

```text
1. Inspect the current schema.
2. Generate the migration.
3. Test forward migration.
4. Test rollback.
5. Verify application compatibility.
```

Putting the whole procedure into persistent policy widens the waist.

### 29.9 Enforcement

Mechanically enforceable policy should flow downward into checks:

```text
                       Policy
                         |
          Domain must not import HTTP layer
                         |
                         v
               architecture constraint
                         |
             +-----------+-----------+
             |                       |
             v                       v
       agent instruction      dependency test
```

One effective rule can serve several consumers:

```text
                  effective rule
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
   agent prose     CI assertion     review report
```

The instruction guides the agent. The test determines compliance.

### 29.10 Waist boundaries

Only stable semantic mechanisms belong in the waist:

```text
IN THE WAIST

+ stable IDs
+ dependency resolution
+ applicability
+ composition
+ precedence
+ conflict rules
+ normalized effective policy
+ provenance
+ schema version
```

Sources remain above and consumers below:

```text
ABOVE                          BELOW

+ Python rules                 + AGENTS formatting
+ FastAPI rules                + Claude formatting
+ company standards            + Cursor globs
+ project overrides            + Copilot instructions
+ security packs               + CI configuration
+ external policy packs        + skills
                               + evaluation runners
```

These concerns stay outside SOLID-AI's core:

```text
OUTSIDE THE HOURGLASS

- issue tracking
- generic project planning
- product requirements
- agent orchestration
- sprint management
- universal release ceremony
- development-session journaling
```

### 29.11 Architectural decision test

For every proposed change:

1. If it is a new policy source, place it above the waist.
2. If it is a new output or integration, place it below the waist.
3. If it changes stable policy semantics, treat it as a rare core change.
4. If it is a procedure, implement it as a skill.
5. If it is mechanically enforceable, generate or configure a check.
6. If it is project management, keep it outside SOLID-AI.

The desired final shape is:

```text
                  OPEN POLICY ECOSYSTEM
       organization   standards   project   stacks
             \            |          |       /
              \           |          |      /
               \          |          |     /
                +-------------------------+
                |   POLICYSET CONTRACT    |
                |      small + stable     |
                +-------------------------+
                  /       |       |      \
                 /        |       |       \
                /         |       |        \
         AGENTS       CLAUDE    Cursor    CI / evals
                  OPEN CONSUMER ECOSYSTEM
```

The present model has the right graph-shaped foundation, but policy content,
mechanics, rendering, and governance occupy a thick middle. The target
architecture makes `PolicySet v1` the narrow waist and requires integrations to
grow outward on either side rather than adding more material to the core.

## 30. Final handoff

The project should not be discarded or rewritten from scratch. Its composition
model and policy catalogue are valuable migration assets.

The unstable part is the governance economics:

- adding policy is cheap;
- every rule creates maintenance obligations;
- audits maximize findings;
- findings become tracker commitments;
- minor releases trigger further review;
- structural validation outpaces outcome validation;
- deletion has no equivalent force.

The next milestone should be evaluated as stabilization rather than expansion:

> Reduce total policy and governance surface while preserving or improving
> measured agent outcomes.

Evidence of success is better measured agent outcomes with manageable adoption
and maintenance cost, as defined in section 22. Reduced duplication and smaller
context support that outcome when behaviour is preserved. A lower issue count
or slower release cadence alone does not establish improvement. The proposed
compiler direction needs its own validation; it is not a prerequisite for
improving quality and intake now.
