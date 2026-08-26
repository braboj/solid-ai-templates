# Platform — GitHub

[ID: platform-github]
[DEPENDS ON: templates/base/workflow/quality-gates.md, templates/base/workflow/issues.md]

GitHub-specific CI, security, and issue label integration. Maps quality
gate categories to GitHub Actions workflows and GitHub-native features.

---

## CI

[ID: platform-github-ci]

- Pipeline definitions: `.github/workflows/*.yml`
- Trigger: `on: pull_request` for validation, `on: push` for main branch
- Actions marketplace for reusable steps
- **Least-privilege token scope.** Set the workflow-level `permissions:`
  to `contents: read` by default and grant a write scope ONLY on the
  specific job that needs it (release creation, artifact/asset attach),
  at job level. A single compromised step in a blanket-write workflow
  can do real damage; a read-only default contains it. Keep a scan that
  needs an elevated scope in its OWN workflow — SAST that writes
  findings needs `security-events: write`, and isolating it means that
  scope never rides along with the main CI jobs. An isolated workflow
  MUST then carry its own fan-in job, for the same reason the main one
  does; see "Fan out one gate per job". Prefer pipeline-as-code
  (a committed workflow file) over a platform default-setup toggle, so
  the scoped permission is reviewed and version-controlled.

  ```yaml
  permissions:
    contents: read          # workflow-level default
  jobs:
    release:
      permissions:
        contents: write     # only where needed
  ```
- **Authenticate GitHub API calls**, even for public-data reads. Any
  `api.github.com` call in a workflow MUST send
  `Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}`. Unauthenticated
  calls are rate-limited to 60/hour per source IP, and Actions runners
  share IP pools — so an innocent `curl .../releases/latest` for
  version resolution can return an empty body under load, with no
  curl error.
- **Fail loud on resolved shell values.** Any step that resolves a
  value via a pipeline (`curl | grep | cut`, `jq`, etc.) MUST
  `set -euo pipefail` AND check the result before use. Pipelines exit
  0 on empty intermediates, so `v${VERSION}_linux_x64.tar.gz` silently
  becomes `v_linux_x64.tar.gz` → 404, far from the real failure.

  ```yaml
  - name: Resolve version
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    run: |
      set -euo pipefail
      VERSION=$(curl -sSf -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        https://api.github.com/repos/owner/foo/releases/latest \
        | grep tag_name | cut -d '"' -f 4 | sed 's/v//')
      if [ -z "${VERSION}" ]; then
        echo "Failed to resolve VERSION" >&2
        exit 1
      fi
  ```
- **Pin third-party actions to a full commit SHA**, with the
  human-readable version in a trailing comment so Dependabot still
  bumps them. A tag can be moved to point at different code; a commit
  SHA cannot — SHA-pinning is the standard supply-chain control for
  third-party actions.

  ```yaml
  - uses: actions/checkout@<commit-sha>  # v4
  ```
- **Retry a transient `uses:` step with a conditional second
  attempt.** `nick-fields/retry` only retries a shell `command` — it
  cannot re-invoke a `uses:` step, and most first-party actions
  (`actions/deploy-pages`, etc.) are JS actions. Pattern:
  `continue-on-error: true` on the first attempt, then a retry gated
  on the step outcome:

  ```yaml
  - id: deployment
    uses: actions/deploy-pages@<commit-sha>  # v5
    continue-on-error: true
  - if: steps.deployment.outcome == 'failure'
    run: sleep 30
  - id: deployment-retry
    if: steps.deployment.outcome == 'failure'
    uses: actions/deploy-pages@<commit-sha>  # v5
  ```

  - Gate on `outcome`, not `conclusion` — `continue-on-error` flips
    the step's conclusion to `success` but leaves outcome `failure`
  - The retry step MUST NOT be `continue-on-error` itself — a double
    failure fails the job loud instead of masking an outage
  - Scope the retry to flaky infra steps only (deploys, registry
    pushes) — never a deterministic gate (`build`, `validate`), or a
    real failure gets masked
  - Distinguish three failure classes: a single-hit flake (the
    one-retry pattern above covers it), a multi-minute flake (the
    backend recovers in minutes but slower than one short backoff), and
    a sustained outage (retries cannot help). For the middle class,
    escalate to a bounded 3-attempt sequence with growing backoff (e.g.
    30s then 90s — attempts at roughly +0s / +45s / +2.5min), the final
    attempt NOT `continue-on-error`. The bound is the stop condition: if
    all three ever fail on a flake, reclassify as a sustained outage
    (wait-and-rerun) rather than adding a fourth attempt
- **Fan out one gate per job, fan in a single required check.** Run
  each quality gate as its own job (lint, type-check, test, build, e2e,
  scan) so each fails fast and reports independently, then make ONE
  `gate` job the required branch-protection context. The `gate`
  job runs `if: always()` and fails unless EVERY upstream result is
  exactly `success` — treating `skipped` and `cancelled` as failure,
  not just `failure`. This is the concrete encoding the "skipped is not
  passed" rule demands: a fan-in that checks only for `failure` lets a
  skipped required gate slip through as a pass.
- **One required context per workflow, not one per repository.** A
  fan-in job can only `needs:` jobs in its own workflow, so a scan
  isolated for its elevated scope cannot join the main one. It then
  either gates nothing, or takes its own per-job entry in branch
  protection — and a per-job list is exactly what the fan-in rule
  exists to avoid, because it goes stale silently the moment a job is
  added. Give the isolated workflow its own fan-in over its matrix, and
  require that. One context per workflow is the price of the isolation
- **A fan-in over a code-scanning matrix gates on the analysis having
  run, not on the code being clean.** The analysis succeeds and uploads
  its alerts; blocking a merge on those alerts is a separate platform
  control. Conflating the two produces a required check that looks
  stricter than it is

  ```yaml
  gate:
    needs: [lint, type-check, test, build, e2e, scan]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - run: |
          for r in ${{ join(needs.*.result, ' ') }}; do
            if [ "$r" != "success" ]; then
              echo "a required gate did not succeed" >&2
              exit 1
            fi
          done
  ```

---

## SAST

[ID: platform-github-sast]

- **CodeQL** — GitHub-native. Free on **public** repositories. On a
  **private** repository code scanning requires GitHub Code Security, a
  paid add-on, and the API declines the repository outright before any
  analysis starts. Confirm entitlement before committing a workflow:

```bash
gh api repos/<owner>/<repo>/code-scanning/analyses
```

  Pass condition: the command reports the repository's analyses. `HTTP
  404 no analysis found` means the repository is entitled and nothing has
  run yet. `HTTP 403 Code Security must be enabled for this repository to
  use code scanning` means it is not entitled, and a CodeQL workflow
  committed there can only ever be permanently red or permanently
  skipped. Distinguish the two before reading either as a failure
- Where a private project is not entitled, record the decline against
  the SAST gate with a revisit trigger. Committing an inert workflow
  instead satisfies the gate list by appearance while scanning nothing,
  which is the gate-by-omission shape the quality-gate rules name
- Enable via Settings → Code security → CodeQL analysis
- Runs as a GitHub Actions workflow or as automatic analysis
- Supports: JavaScript, TypeScript, Python, Go, Java, C/C++, C#, Ruby
- Stack-specific SAST supplements (Bandit, govulncheck) run as CI steps
- **Exclude captured-content test fixtures from CodeQL analysis.**
  Projects with web-scraper snapshots, contract-test fixtures, or
  vendored example payloads frequently get high-severity alerts on
  third-party minified JS / vendor libraries embedded in those
  fixtures. The fixtures are not project code — they are frozen
  snapshots for offline test repeatability. Add a
  `.github/codeql-config.yml` with `paths-ignore` for the fixture
  directories and reference it from the workflow:

  ```yaml
  # .github/codeql-config.yml
  name: "Project CodeQL config"
  paths-ignore:
    - "tests/fixtures/**"
    - "tools/**/tests/fixtures/**"
  ```

  ```yaml
  # .github/workflows/codeql.yml
  - uses: github/codeql-action/init@<commit-sha>  # v4
    with:
      languages: javascript-typescript
      config-file: ./.github/codeql-config.yml
  ```

  Applies to any captured-content fixture (HTML, JSON, JS), not just
  web-scraper output.

---

## Secret detection

[ID: platform-github-secrets]

- **GitHub push protection** — native, blocks pushes containing known
  secret patterns; enable via Settings → Code security
- **gitleaks** — `gitleaks/gitleaks-action` in CI for additional
  coverage. Free on personal repos; on **organization** repos it
  requires a paid `GITLEAKS_LICENSE` secret. For org repos, consider
  the authenticated curl-install pattern instead (see CI section,
  workflow authoring rules) to avoid the paywall.
- Both SHOULD be enabled — push protection catches on push, gitleaks
  catches in PR validation
- The gitleaks job MUST check out full history (`actions/checkout` with
  `fetch-depth: 0`) — the default shallow checkout scans only the tip,
  missing a secret that was committed and later deleted but still lives
  in old commits

---

## Dependency management

[ID: platform-github-deps]

- **Dependabot** SHOULD be enabled for automated dependency update PRs
- Configure in `.github/dependabot.yml`:
  ```yaml
  version: 2
  updates:
    - package-ecosystem: npm # or pip, gomod, etc.
      directory: /
      schedule:
        interval: weekly
      groups:
        dev-dependencies:
          dependency-type: development
  ```
- Group related dependencies to reduce PR noise
- Combine with auto-merge for patch and minor updates: a GitHub
  Actions workflow that merges passing `dependabot/` branches
- **Weekly-batch triage** — when a scheduled run opens several PRs at
  once:
  - Scan the queue without opening run pages:
    `for pr in <ids>; do gh pr checks $pr; done`
  - Expect a **lockfile-conflict cascade**: each squash-merge bumps the
    lockfile and conflicts every open sibling PR. Merge in small
    parallel batches (expect 1–2 race-losers), `@dependabot rebase` the
    losers, repeat. Generic to any lockfile ecosystem (npm, pnpm,
    cargo, poetry)
  - Dependabot **auto-supersedes** — it closes a PR once its target is
    reached transitively via sibling merges; do not manually reopen

---

## Branch cleanup

[ID: platform-github-branch-cleanup]

A squash merge writes a new commit, so `git branch --merged main` never
matches a squash-merged branch. It exits 0 having deleted nothing, which
reads exactly like a clean tree. Use the PR record instead — it survives
the head branch's deletion.

```bash
gh pr view <N> --json state,headRefOid --jq '"\(.state) \(.headRefOid)"'
git rev-parse <branch>
```

- `MUST` treat the branch as deletable only when the PR state is
  `MERGED` and `headRefOid` equals the local tip — then `git branch -D`
  (`-d` refuses, for the same ancestry reason `--merged` fails)
- A differing `headRefOid` is the normal case wherever branch protection
  requires branches be up to date, because `gh pr update-branch` rewrites
  the remote head and leaves the clone on the commit it replaced. Treat
  the mismatch as a prompt to inspect, never as proof of unpushed work
- `MUST` inspect a mismatch by content before deleting. Comparing
  ancestry gives false positives after a rebase, since the same work
  carries a new SHA on each side:

```bash
git fetch origin refs/pull/<N>/head
git diff --numstat FETCH_HEAD..<branch>
```

- Lines present only on the local side are safe when they are text that
  later commits superseded. Work the branch authored that appears nowhere
  in the PR head is not — push it before deleting

---

## GitHub Pages

[ID: platform-github-pages]

- MUST enable "Enforce HTTPS" in repository Settings → Pages for custom
  domains — GitHub Pages does not enforce HTTPS by default
- HTTP requests MUST 301 redirect to HTTPS — without enforcement, HTTP
  serves content with 200 OK, causing duplicate content and SEO penalties

---

## Quality gate integration

[ID: platform-github-gates]

| Category                  | Tool / Integration                       |
| ------------------------- | ---------------------------------------- |
| SAST                      | CodeQL — public repos; private needs Code Security |
| SAST (Python)             | + Bandit (CI step)                       |
| SAST (Go)                 | + govulncheck (CI step)                  |
| Secret detection          | GitHub push protection + gitleaks action |
| Site quality              | `treosh/lighthouse-ci-action`            |
| Link checking             | `lycheeverse/lychee-action` (see note)   |
| All lint/format/type/test | Language-specific CLI in CI steps        |

**Lychee note (internal links):** When checking internal links on static
site build output, MUST use `--root-dir <build-dir>` to resolve
root-relative paths. Without it, links like `/about` produce false
errors:

```yaml
- uses: lycheeverse/lychee-action@<commit-sha>  # v2
  with:
    args: --offline --no-progress --root-dir dist dist/
```

**Lychee note (external links):** External checking has different
failure modes and MUST be configured as a separate job:

- MUST run on a schedule, never as a merge-blocking check — a
  third-party outage is unrelated to the change under review, and a
  failure means a cited page moved, which is content work
- MUST accept `403` and `429` — some hosts refuse automated clients
  while serving browsers normally. Record in a comment beside the
  exclusion that this forfeits detection of a genuine permission change
- MUST pass `GITHUB_TOKEN` — a private repository's own README
  self-links return `404` to an unauthenticated client
- MUST exclude documentation example URLs by pattern — a placeholder
  host cited to demonstrate a format never resolves
- MUST enumerate paths rather than pass a bare `**/*.md` — a recursive
  glob skips dot-directories, silently omitting agent and skill
  definition files, which frequently carry external citations
- MUST run the check by hand and configure out its false positives
  before committing the workflow — a check that fails on its first run
  gets muted rather than fixed

```yaml
- uses: lycheeverse/lychee-action@<commit-sha>  # v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    args: >-
      --no-progress --accept 200,403,429 --max-retries 2 --timeout 20
      --exclude "^https://example-placeholder/"
      "docs/**/*.md" ".claude/**/*.md" "README.md"
    fail: true
```

**Aggregator timing:** when branch protection requires an aggregator
`gate` job that runs after its sub-checks, a merge issued in the gap
returns `the base branch policy prohibits the merge`. Merge waiters
MUST target the aggregator job by name, not the individual sub-checks —
and MUST target every one of them where an isolated scan workflow
carries its own. Waiting on one aggregator while a second is still
pending reproduces the same refusal from a state that reads as ready.

---

## Issue labels

[ID: platform-github-labels]
[EXTEND: base-issues-types]

GitHub implements issue types and priorities as labels. Every issue
MUST have exactly one type label and one priority label. Triage
labels are terminal — applied when closing without action.

Milestones are optional. An issue MAY carry one; an empty milestone
field is valid and means the work is not tied to a release, and is
where deferred work sits. A PR SHOULD inherit the milestone of the
issue it closes, when that issue has one.

Do NOT stand up a named holding lane — a `Backlog` or `Expedite`
milestone — to mark work as unscheduled or fast-tracked. An empty
milestone field already says unscheduled, and urgency is carried by the
severity label, which travels with the issue where a lane's meaning is
lost the moment the milestone is closed or deleted.

Milestones are forward-looking planning; GitHub Releases are the
backward-looking shipped record. Create a versioned milestone (e.g.
`v1.0.0`) only for a deliberately planned, scoped release. A routine or
emergent release that was never scoped as a milestone gets none — the
Release is its shipped record. Do NOT backfill empty per-version
milestones after the fact; a planning artifact created retroactively
carries no information.

Colors follow the Atlassian design system palette. Type labels use
saturated hues; priority labels use a warm-to-cool gradient to
remain visually distinct when displayed side by side.

### Type labels (pick one)

| Label      | Color     | Maps to  |
| ---------- | --------- | -------- |
| `bug`      | `#C9372C` | Bug      |
| `epic`     | `#9F8FEF` | Epic     |
| `task`     | `#579DFF` | Task     |
| `spike`    | `#6CC3E0` | Spike    |
| `incident` | `#AE2E24` | Incident |

### Priority labels (pick one)

| Label | Color     | Maps to       |
| ----- | --------- | ------------- |
| `P0`  | `#E06C00` | P0 — Critical |
| `P1`  | `#FCA700` | P1 — High     |
| `P2`  | `#EED12B` | P2 — Medium   |
| `P3`  | `#4BCE97` | P3 — Low      |

There MUST NOT be a fifth priority label. Deferral is carried by an
empty milestone field, not by a band below `P3`.

### Triage labels

| Label       | Color     | When to use                            |
| ----------- | --------- | -------------------------------------- |
| `duplicate` | `#C1C7D0` | Already tracked by another issue       |
| `wontdo`    | `#C1C7D0` | Acknowledged but will not be addressed |

### Label conformance check

GitHub has no mutually-exclusive label group, so nothing stops an
unlabeled or double-labeled issue being created. The rule is enforced
by running the check, not by the platform:

```bash
gh issue list --state open --limit 200 --json number,labels \
  --jq '[.[] | {n: .number,
                t: ([.labels[].name
                     | select(test("^(bug|epic|task|spike|incident)$"))] | length),
                p: ([.labels[].name | select(test("^P[0-3]$"))] | length)}
        | select(.t != 1 or .p != 1)]'
```

Output MUST be `[]`. Each reported entry names the issue and its actual
type and priority counts. The type alternation is the project's own
taxonomy; the `P[0-3]` pattern is fixed, and matches the whole priority
scale — the check does not filter on the milestone field, so a deferred
issue passes on its labels like any other.
