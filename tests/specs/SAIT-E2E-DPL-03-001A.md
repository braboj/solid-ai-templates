---
id: SAIT-E2E-DPL-03-001A
uuid: a1b2c3d4-e5f6-7890-abcd-ef1234567828
title: Offline deployment target produces correct deployment rules in the output
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
tags: [e2e, deployment, offline, air-gapped, pki]
---

## Short description

> **Given** `INTERVIEW.md`, a stack template, and `base/deployment.md` are attached to
> an agent
> **When** the interview answer selects **offline** (air-gapped) as the deployment
> target
> **Then** the generated `CLAUDE.md` contains offline-appropriate deployment rules
> (self-hosted PKI, local DNS, local artifact mirror, no external dependencies)

## Results

| Result | Condition |
|--------|-----------|
| PASSED | Output mandates self-hosted PKI, local DNS resolver, local artifact registry mirror; no references to public internet services |
| FAILED | Output references public CAs, external registries, or cloud-managed services; air-gap constraints absent |
| SKIPPED | No agent available |
| BLOCKED | `SAIT-INT-TPL-01-001A` is failing |
| ERROR | Agent fails to load template files or produce output |

## Steps

### Prerequisites

- Repository cloned locally
- Claude Code available

### Setup

1. Open Claude Code
2. Attach `INTERVIEW.md`, `stack/python-fastapi.md`, `base/deployment.md`,
   `base/core/agents.md`
3. Interview answers:
   - Project name: SecureIngestService
   - Language: Python
   - Deployment target: **offline** (air-gapped, no internet access)
   - Output: CLAUDE.md

### Execution

1. Ask the agent to run the interview and generate `CLAUDE.md`
2. Provide the prepared answers

### Assertions

1. Assert `## Deployment` section specifies **offline** / air-gapped target
2. Assert self-hosted PKI referenced (internal root CA, no Let's Encrypt or public CA)
3. Assert local DNS resolver documented (no external DNS assumed)
4. Assert local artifact registry mirror documented (no pulls from Docker Hub, PyPI,
   etc.)
5. Assert no references to internet-dependent services (CDN, managed cloud services)
6. Assert base git conventions present

### Teardown

1. Delete generated `CLAUDE.md`

## Related

- Related procedures: `SAIT-E2E-DPL-01-001A`, `SAIT-E2E-DPL-02-001A`
- Implements: `base/deployment.md` §Deployment targets — offline
