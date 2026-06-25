# Base — DevSecOps

[ID: base-devsecops]

## Principle

Security is not a phase — it is part of every build, review, and release.
Vulnerabilities and legal exposure MUST be surfaced during development —
not after deployment.

## Patterns

- Use break-the-build gate, vulnerability triage, SBOM generation,
  secret rotation, dependency update workflow, security smoke test,
  pre-merge security gate, and incident-to-hardening loop patterns
  where appropriate

## Tool selection

- Specific SAST and secret detection tools are defined per platform
  (CodeQL for GitHub, Semgrep for GitLab)

## SAST (Static Application Security Testing)

- Every pipeline run MUST include a static security analysis step
- A failed scan MUST stop the build — the branch MUST NOT progress until
  findings are resolved or formally accepted as false positives
- Accepted false positives MUST be documented with a written justification

## SCA (Software Composition Analysis)

- All dependencies MUST be tracked for known vulnerabilities and license risks
- SCA MUST run on every deployment to QA, staging, and production
- A SBOM (Software Bill of Materials) MUST be generated per release
- Dependencies with unacceptable licenses MUST NOT be merged

## Secret detection

- Secret detection MUST run in CI — any commit containing credentials, tokens,
  or API keys MUST be rejected automatically
- Sensitive values MUST NOT appear in any artefact that enters source control —
  this includes commit messages, issue comments, and documentation files
- Runtime secrets MUST be fetched from a dedicated vault at startup — MUST NOT
  be written to disk or committed in any form

## License compliance

- Before adding a dependency, verify its license is acceptable
- Copyleft licenses (GPL, AGPL) require explicit approval before use
- Document and justify any dependency with a non-standard or ambiguous license

## DAST (Dynamic Application Security Testing)

- DAST MUST run against the staging/QA environment after every deployment
- Never run DAST against production
- Automated DAST scans MUST complete before any production release
- Critical findings MUST block the release and be treated as incidents
- Lower-severity findings MUST be tracked and resolved within a defined timeframe

## IaC scanning (Infrastructure-as-Code)

- All infrastructure code (Terraform, Dockerfiles, Helm charts, Kubernetes
  manifests) MUST be scanned for security misconfigurations in CI
- A failed IaC scan MUST fail the build — the same rule as SAST
- Common issues to detect: overprivileged roles, exposed ports, unencrypted
  storage, hardcoded values, use of `latest` image tags
- IaC scan results MUST be reviewed in the same PR that introduces the change

## Penetration testing

- Schedule regular penetration testing by a qualified party
- Critical findings (severity A) MUST be treated as incidents and resolved
  immediately
- Lower-severity findings MUST be tracked and resolved within a defined
  timeframe

## Dependency hygiene

- Keep dependencies up to date — unpatched dependencies are a security risk
- Remove unused dependencies promptly
- Prefer dependencies that are actively maintained and widely adopted
- Pin third-party GitHub Actions to a full commit SHA, not a mutable
  tag, with the version in a trailing comment so Dependabot still bumps
  them — a moved tag is a supply-chain attack vector
