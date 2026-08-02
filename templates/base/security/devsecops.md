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
- Attach the SBOM to the per-tag release record as a durable,
  per-version asset — a CI build artifact expires with run retention.
  Once the pipeline creates a release record on a tag, upload the SBOM
  from the advisory scan job (`gh release upload "$TAG" <sbom>
  --clobber`). Guard the upload (missing release or SBOM → exit 0) and
  mark the job `continue-on-error` so a scan hiccup never blocks or
  erases the release — the scan job reaches forward to the release,
  never the reverse. Needs `contents: write` at job scope
- Dependencies with unacceptable licenses MUST NOT be merged

## Scan by actionability

The block-vs-inform decision turns on one question: can I fix this
before release? A finding you own has a fix you can apply; a finding in
a base layer you do not control does not.

- **Gate (blocking) on findings you own** — SCA over your own
  dependencies (`pip-audit`, `npm audit`, `govulncheck`). A vulnerable
  dependency has a fix you can apply, so it MUST block the merge
- **Inform (advisory) on findings you cannot fix at will** — image and
  base-layer scans (Trivy, Grype). Run them and publish the report plus
  an SBOM, but do not fail the build on an unfixable upstream CVE
  (`continue-on-error` plus a non-failing exit code)
- **Advisory by construction for release-gated scans** — a scan that
  runs only on a tag or release job cannot be dry-run on a PR, so a
  hard fail first surfaces mid-release. Keep such scans advisory and
  OFF the deploy dependency path, so an image hiccup cannot block the
  deploy or erase the release record
- **Make the fixable-base case a PR, not a standing advisory** — track
  the base image with a dependency bot (docker ecosystem) so an
  available base bump arrives as a reviewable PR, not a perpetual
  scan finding

## Secret detection

- Secret detection MUST run in CI — any commit containing credentials, tokens,
  or API keys MUST be rejected automatically
- The scan MUST cover the full git history, not just the current tip: a
  secret committed and later deleted still lives in old commits, so a
  shallow checkout gives a false sense of safety. Check out full-depth
  before the scan (`actions/checkout` with `fetch-depth: 0`)
- Run the scanner both in CI (full history) and as a pre-commit hook
  (catch it before it is ever committed) — defense in depth
- Sensitive values MUST NOT appear in any artefact that enters source control —
  this includes commit messages, issue comments, and documentation files
- Runtime secrets MUST be fetched from a dedicated vault at startup — MUST NOT
  be written to disk or committed in any form

## License compliance

- Before adding a dependency, verify its license is acceptable
- Copyleft licenses (GPL, AGPL) require explicit approval before use
- Document and justify any dependency with a non-standard or ambiguous license
- Approving a license does not discharge the obligation that attaches
  when the dependency is **redistributed** inside a built artifact
  handed to users (container image, bundle, installer, fat jar). A
  permissive or weak-copyleft (LGPL, MPL) dependency shipped that way
  carries an attribution obligation of its own
- Ship a third-party notice file inside the artifact, at a stable path
  a runtime bind mount cannot shadow (e.g. `/licenses/`), placed after
  the dependency-install layer so editing it does not bust the build
  cache
- Guard the notice with a test that derives the required entries from
  the dependency manifest, so a newly added redistributed dependency
  fails the build until it is documented. Hand-maintained attribution
  rots

## DAST (Dynamic Application Security Testing)

- DAST MUST run against the staging/QA environment after every deployment
- Never run DAST against production
- Automated DAST scans MUST complete before any production release
- Critical findings MUST block the release and be treated as incidents
- Lower-severity findings MUST be tracked and resolved within a defined
  timeframe

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
