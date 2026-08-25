# DevSecOps Pipeline — Wiki

Wiki notes on reusable security structures for CI/CD pipelines.
Each entry describes a problem, solution structure, when to
use it, and examples.

See `base/devsecops.md` for SAST, SCA, secret detection, and
compliance rules.
See `security.md` for application-level security
patterns (input validation, encoding, CSRF, headers).

---

## 1. Break-the-build gate

**Problem:** Security scans run in CI but findings are advisory.
Developers see warnings, ignore them, and merge. Vulnerabilities
accumulate because nothing enforces action.

**Solution:** Security scan failures break the build — the PR
cannot merge until findings are resolved or explicitly accepted.
Same enforcement as lint or test failures.

```
PR → build → test → security scan
                        ├→ PASS → merge allowed
                        └→ FAIL → merge blocked
```

**When to use:**

- Every pipeline — this is the default enforcement model
- Apply to SAST, secret detection, SCA, and IaC scanning

**GitHub Actions:**

```yaml
security:
  runs-on: ubuntu-latest
  steps:
    - uses: github/codeql-action/analyze@v3
    # Action exits non-zero on findings → job fails → gate fails
```

**Rules:**

- Critical and high findings MUST block the build — no exceptions
- Medium findings SHOULD block the build — deviations require
  written justification in the PR
- Low findings MAY be tracked as issues instead of blocking
- False positives MUST be documented with a suppression comment
  in code — not silenced in CI configuration
- Never add `continue-on-error: true` to security scan steps

## 2. Vulnerability triage workflow

**Problem:** SCA tools report dozens of vulnerabilities across
transitive dependencies. The team has no process for deciding
which to fix first. Everything is treated equally — so nothing
gets fixed.

**Solution:** Triage vulnerabilities by exploitability and impact.
Assign a priority and a deadline. Track in the issue tracker like
any other bug.

```
SCA report → triage
  ├→ Critical + exploitable → P0, fix immediately
  ├→ High + reachable       → P1, fix this sprint
  ├→ Medium + deep transitive → P2, track and monitor
  └→ Low + no path          → P3, accept risk
```

**When to use:**

- After every SCA scan that produces new findings
- During scheduled dependency review (weekly or bi-weekly)

**Rules:**

- Triage MUST consider reachability — a vulnerability in an
  unused code path is lower priority than one in a hot path
- Every triaged finding MUST have an owner and a deadline
- Accepted risks MUST be documented with rationale and review
  date
- Re-triage accepted risks quarterly — the threat landscape
  changes

## 3. SBOM generation

**Problem:** A vulnerability is disclosed in a widely-used library.
The team cannot determine which services use the affected version.
Hours are spent auditing manually. Incident response is slow.

**Solution:** Generate a Software Bill of Materials (SBOM) on every
release. The SBOM lists every dependency and its version. When a
vulnerability is disclosed, search across SBOMs to identify
affected services in minutes.

```
build → generate SBOM → attach to release artifact
                      → store in registry

CVE disclosed → search SBOMs → list affected services → patch
```

**When to use:**

- Every production release
- Required for regulatory compliance (FDA, DoD, EU CRA)
- Recommended for any project with more than 10 dependencies

**GitHub Actions:**

```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    artifact-name: sbom.spdx.json
    output-file: sbom.spdx.json

- name: Attach to release
  uses: softprops/action-gh-release@v2
  with:
    files: sbom.spdx.json
```

**Rules:**

- Use standard formats: SPDX or CycloneDX
- Generate from the lock file, not from declared dependencies —
  transitive dependencies matter most
- Store SBOMs alongside release artifacts — they must be
  retrievable per version
- Automate SBOM generation in CI — never generate manually

## 4. Secret rotation

**Problem:** Secrets (API keys, database passwords, tokens) are
created once and never rotated. A leaked secret from months ago
still works. The blast radius of any breach extends indefinitely.

**Solution:** Rotate secrets on a schedule. Automate the rotation
so it requires no human intervention. Support overlapping validity
windows so consumers can switch without downtime.

```
Day 0:  create secret v2 (both v1 and v2 valid)
Day 1:  deploy consumers with v2
Day 2:  revoke v1

Timeline: [---v1 valid---][--overlap--][---v2 valid---]
```

**When to use:**

- All long-lived secrets (database passwords, API keys, tokens)
- After any suspected compromise — rotate immediately, do not
  wait for the schedule

**Rules:**

- Rotation MUST be automated — manual rotation does not happen
  on schedule
- Support dual-validity during rotation — never revoke the old
  secret before all consumers have switched
- Rotation period: 90 days for most secrets, 30 days for
  high-value secrets (production database, signing keys)
- Test rotation in staging before enabling in production
- Alert on rotation failure — a failed rotation is worse than
  no rotation (the secret is stuck)

## 5. Dependency update workflow

**Problem:** Dependencies are updated reactively — only when a
vulnerability is reported. By then, the update may span multiple
major versions, making it risky and time-consuming. Small frequent
updates are safer than rare large ones.

**Solution:** Automate dependency update PRs (Dependabot, Renovate).
Review and merge weekly. Combine with CI and auto-merge for
low-risk updates.

```
Weekly:
  Dependabot → patch/minor PRs → CI passes → auto-merge
  Dependabot → major PRs       → CI passes → human review → merge

Monthly:
  Review accepted vulnerability risks
  Update base images and runtime versions
```

**When to use:**

- Every project with external dependencies
- Combine with the auto-merge pattern from `cicd.md`

**Rules:**

- Patch and minor updates: auto-merge if CI passes (see the
  auto-merge section in `cicd.md`)
- Major updates: require human review of changelog and breaking
  changes
- Group related updates (e.g. all `@typescript-eslint/*` packages)
  into a single PR to reduce noise
- Pin a schedule: review dependency PRs on a fixed day — do not
  let them pile up
- Track update frequency — if a dependency has not been updated
  in 12 months, investigate whether it is abandoned

## 6. Security smoke test

**Problem:** Security headers, CSP, CORS, and TLS configuration
are set once and forgotten. A deployment change or proxy update
silently removes a header. The misconfiguration is not caught
until a pentest or an incident.

**Solution:** Run lightweight security assertions after every
deployment. Verify that critical security controls are present
in the live environment.

```
deploy → security smoke test
  ├→ HSTS header present?
  ├→ CSP header present?
  ├→ TLS 1.2+ only?
  ├→ No server version header?
  └→ CORS restricted to allowed origins?
```

**When to use:**

- After every deployment to staging and production
- As a post-deploy step in the CI/CD pipeline

**Example (curl-based):**

```bash
URL="https://staging.example.com"
FAIL=0

check_header() {
  if ! curl -sI "$URL" | grep -qi "$1"; then
    echo "MISSING: $1"
    FAIL=1
  fi
}

check_header "strict-transport-security"
check_header "content-security-policy"
check_header "x-content-type-options"

exit $FAIL
```

**Rules:**

- Security smoke tests MUST run after deploy, not just in CI —
  proxy and CDN configuration can strip headers
- Keep tests fast (under 10 seconds) — they run on every deploy
- Test the live URL, not the build output
- Alert immediately on failure — a missing security header in
  production is an incident

## 7. Pre-merge security gate

**Problem:** SAST and SCA run on every PR, but DAST only runs
after merge to staging. A vulnerability that SAST misses is not
caught until the code is already deployed. The feedback loop is
slow and the fix requires another PR.

**Solution:** Layer security checks at increasing depth before
merge. Each layer catches what the previous one cannot.

```
PR opened:
  Layer 1 → SAST (code patterns)
  Layer 2 → SCA (dependency vulnerabilities)
  Layer 3 → Secret detection (leaked credentials)
  Layer 4 → IaC scan (infrastructure misconfig)

All pass → merge allowed

Post-merge to staging:
  Layer 5 → DAST (runtime vulnerabilities)
```

**When to use:**

- Every project — the layers are additive; start with what
  you have and add more over time
- Minimum: SAST + secret detection (Layer 1 + 3)

**Rules:**

- Each layer runs independently — failure in one does not skip
  others
- Combine with the fan-out pattern from `cicd.md`
  for parallel execution
- DAST runs post-merge because it needs a running environment —
  but DAST findings MUST still block production deployment
- Track which layer catches each finding — if DAST consistently
  catches issues SAST misses, improve SAST rules

## 8. Incident-to-hardening loop

**Problem:** A security incident is resolved. The immediate fix
is deployed. But the root cause is never addressed. The same
class of vulnerability appears again in a different service.

**Solution:** Every security incident produces a hardening action
that prevents the same class of vulnerability. The action is
tracked as a task, implemented, and verified in CI.

```
Incident → root cause → hardening action
  ├→ New SAST rule
  ├→ New CI check
  ├→ New security smoke test
  ├→ Updated template/convention
  └→ ADR documenting the decision

Same class → caught automatically next time
```

**When to use:**

- After every security incident or pentest finding
- After any vulnerability that was not caught by existing
  automation

**Rules:**

- Every incident MUST produce at least one automation change —
  a human process ("be more careful") is not a valid hardening
  action
- Hardening actions MUST be verifiable in CI — if the same
  vulnerability is introduced again, CI fails
- Track hardening actions in the issue tracker with a link to
  the incident
- Review hardening coverage quarterly — are the same classes
  of vulnerabilities still appearing?
- Update templates and conventions when a pattern is reusable
  across projects
