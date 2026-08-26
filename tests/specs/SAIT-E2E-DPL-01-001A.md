---
id: SAIT-E2E-DPL-01-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567826
title: Cloud deployment target produces correct deployment rules in the output
product: sait
type: e2e
area: DPL
priority: p1
status: ready
environment: [local]
automatable: yes
created: 2026-03-22
author: Branimir Georgiev
product-version: "1.x"
tags: [e2e, deployment, cloud, certificates, dns]
---

## Short description

> **Given** `INTERVIEW.md`, a stack template, and `base/deployment.md` are attached to
> an agent
> **When** the interview answer selects **cloud** as the deployment target
> **Then** the generated `CLAUDE.md` contains cloud-appropriate deployment rules
> (public CA, managed DNS, external load balancer, public artifact registry)

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output references public CA, managed DNS, public registry, and external load balancer; no private PKI or air-gap assumptions present |
| FAILED | Output contains hybrid or offline rules (private CA, internal DNS); cloud-specific conventions absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/node-express.md`, `base/deployment.md`,
   `base/core/agents.md`
3. Interview answers:
   - Project name: PublicAPIService
   - Language: TypeScript
   - Deployment target: **cloud**
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Deployment` section specifies **cloud** target
2. Assert certificates reference a public CA (e.g., Let's Encrypt, ACM)
3. Assert DNS references managed cloud DNS (e.g., Route 53, Cloud DNS)
4. Assert artifact registry references a public or cloud-hosted registry
5. Assert no private PKI or air-gap instructions present
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-DPL-02-001A`, `SAIT-E2E-DPL-03-001A`
- Implements: `base/deployment.md` §Deployment targets — cloud
