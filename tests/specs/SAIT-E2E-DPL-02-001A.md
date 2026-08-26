---
id: SAIT-E2E-DPL-02-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567827
title: Hybrid deployment target produces correct deployment rules in the output
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
tags: [e2e, deployment, hybrid, private-ca, pki]
---

## Short description

> **Given** `INTERVIEW.md`, a stack template, and `base/deployment.md` are attached to
> an agent
> **When** the interview answer selects **hybrid** as the deployment target
> **Then** the generated `CLAUDE.md` contains hybrid-appropriate deployment rules
> (private CA for internal traffic, split DNS, mixed registry strategy)

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output references private CA for internal services, split DNS strategy, and mixed registry; no assumptions that all traffic is public or fully air-gapped |
| FAILED | Output applies cloud-only or air-gap-only rules; split-trust model absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/go-service.md`, `base/deployment.md`,
   `base/core/agents.md`
3. Interview answers:
   - Project name: InternalPlatformAPI
   - Language: Go
   - Deployment target: **hybrid** (on-premises + cloud)
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Deployment` section specifies **hybrid** target
2. Assert internal services reference a private CA for mTLS or TLS
3. Assert split DNS strategy documented (internal vs. external resolvers)
4. Assert mixed registry strategy documented (private registry for internal, public for
   external)
5. Assert no assumption that all services can reach the public internet
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-DPL-01-001A`, `SAIT-E2E-DPL-03-001A`
- Implements: `base/deployment.md` §Deployment targets — hybrid
