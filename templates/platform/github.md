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

---

## SAST

[ID: platform-github-sast]

- **CodeQL** — GitHub-native, free for all repositories (public and private)
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
  - uses: github/codeql-action/init@v4
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
| SAST                      | CodeQL (GitHub-native)                   |
| SAST (Python)             | + Bandit (CI step)                       |
| SAST (Go)                 | + govulncheck (CI step)                  |
| Secret detection          | GitHub push protection + gitleaks action |
| Site quality              | `treosh/lighthouse-ci-action`            |
| Link checking             | `lycheeverse/lychee-action` (see note)   |
| All lint/format/type/test | Language-specific CLI in CI steps        |

**Lychee note:** When checking internal links on static site build
output, MUST use `--root-dir <build-dir>` to resolve root-relative
paths. Without it, links like `/about` produce false errors:

```yaml
- uses: lycheeverse/lychee-action@v2
  with:
    args: --offline --no-progress --root-dir dist dist/
```

---

## Issue labels

[ID: platform-github-labels]
[EXTEND: base-issues-types]

GitHub implements issue types and priorities as labels. Every issue
MUST have exactly one type label and one priority label. Triage
labels are terminal — applied when closing without action.

Every issue and pull request MUST also be assigned to a milestone
at creation. Issues without a target release MUST use the `Backlog`
milestone — the milestone field MUST NOT be empty. PRs SHOULD inherit
the milestone of the issue they close.

The `Expedite` milestone is a rolling fast-track lane for work
shipping between versioned releases — mainly bugs and incidents,
also small tasks. It never closes; issues move in when expedited
and out when shipped. Use `Expedite` instead of `Backlog` when the
work is small, urgent, or out-of-cycle and does not fit the current
versioned milestone's theme.

Milestones are forward-looking planning; GitHub Releases are the
backward-looking shipped record. Create a versioned milestone (e.g.
`v1.0.0`) only for a deliberately planned, scoped release. Routine or
emergent releases cut from `Backlog` / `Expedite` get no versioned
milestone — the Release is their shipped record. Do NOT backfill empty
per-version milestones after the fact; a planning artifact created
retroactively carries no information.

Colors follow the Atlassian design system palette. Type labels use
saturated hues; priority labels use a warm-to-cool gradient to
remain visually distinct when displayed side by side.

### Type labels (pick one)

| Label      | Color     | Maps to  |
| ---------- | --------- | -------- |
| `bug`      | `#C9372C` | Bug      |
| `epic`     | `#8270DB` | Epic     |
| `task`     | `#357DE8` | Task     |
| `spike`    | `#6CC3E0` | Spike    |
| `incident` | `#AE2E24` | Incident |

### Priority labels (pick one)

| Label | Color     | Maps to       |
| ----- | --------- | ------------- |
| `P0`  | `#E06C00` | P0 — Critical |
| `P1`  | `#FCA700` | P1 — High     |
| `P2`  | `#EED12B` | P2 — Medium   |
| `P3`  | `#4BCE97` | P3 — Low      |
| `P4`  | `#8590A2` | P4 — Backlog  |

### Triage labels

| Label       | Color     | When to use                            |
| ----------- | --------- | -------------------------------------- |
| `duplicate` | `#C1C7D0` | Already tracked by another issue       |
| `wontdo`    | `#C1C7D0` | Acknowledged but will not be addressed |
