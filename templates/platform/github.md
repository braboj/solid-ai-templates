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

---

## SAST

[ID: platform-github-sast]

- **CodeQL** — GitHub-native, free for all repositories (public and private)
- Enable via Settings → Code security → CodeQL analysis
- Runs as a GitHub Actions workflow or as automatic analysis
- Supports: JavaScript, TypeScript, Python, Go, Java, C/C++, C#, Ruby
- Stack-specific SAST supplements (Bandit, govulncheck) run as CI steps

---

## Secret detection

[ID: platform-github-secrets]

- **GitHub push protection** — native, blocks pushes containing known
  secret patterns; enable via Settings → Code security
- **gitleaks** — `gitleaks/gitleaks-action` in CI for additional coverage
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

Every issue MUST also be assigned to a milestone at creation. Issues
without a target release MUST use the `Backlog` milestone — the
milestone field MUST NOT be empty.

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
