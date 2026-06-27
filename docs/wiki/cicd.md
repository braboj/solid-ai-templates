# CI/CD — Wiki

[ID: cicd-wiki]
[DEPENDS ON: base/cicd.md]

Wiki notes on reusable CI/CD pipeline structures. Each entry
describes a problem, solution structure, when to use it, and
platform examples.

See `base/cicd.md` for pipeline stages and delivery rules.
See `platform/github.md` or `platform/gitlab.md` for tool-specific
configuration.

---

## 1. Gate job

[ID: cicd-wiki-gate]

**Problem:** Required status checks block merges when conditional
jobs are skipped. Docs-only PRs wait for a full build that will
never run.

**Solution:** A lightweight gate job is the only required check.
It always runs, waits for conditional jobs, and fails if any of
them fail.

```
changes ──→ build ──→ lighthouse
    │                      │
    └───────→ gate ←───────┘
```

- `gate` runs on every PR — always satisfies the required check
- `gate` depends on conditional jobs and checks their results
- Conditional jobs skip when path filters exclude them
- A skipped dependency does not fail the gate — only `failure` does

**When to use:**

- Required checks exist alongside path-filtered jobs
- Different file types need different validation (code vs docs)

**GitHub Actions:**

```yaml
gate:
  runs-on: ubuntu-latest
  needs: [build, lighthouse]
  if: always()
  steps:
    - name: Check results
      run: |
        if [[ "${{ needs.build.result }}" == "failure" \
           || "${{ needs.lighthouse.result }}" == "failure" ]]; then
          exit 1
        fi
```

**GitLab CI:**

```yaml
gate:
  stage: .post
  needs:
    - job: build
      optional: true
    - job: lighthouse
      optional: true
  script:
    - echo "All required jobs passed"
  rules:
    - when: always
```

---

## 2. Path filtering

[ID: cicd-wiki-path-filter]

**Problem:** Every PR runs the full pipeline regardless of what
changed. Docs and config changes wait minutes for irrelevant
builds and tests.

**Solution:** A changes detection job runs first and exports
boolean outputs. Downstream jobs use those outputs as conditions.

```
changes (fast) ──→ build (if code)
                ──→ lint-docs (if docs)
                ──→ deploy-preview (if code)
```

**When to use:**

- The repo contains both code and non-code files
- Build or test stages take more than 30 seconds

**GitHub Actions:**

```yaml
changes:
  runs-on: ubuntu-latest
  outputs:
    code: ${{ steps.filter.outputs.code }}
    docs: ${{ steps.filter.outputs.docs }}
  steps:
    - uses: actions/checkout@v6
    - uses: dorny/paths-filter@v4
      id: filter
      with:
        filters: |
          code:
            - 'src/**'
            - 'package.json'
            - 'package-lock.json'
          docs:
            - 'docs/**'
            - '*.md'

build:
  needs: changes
  if: needs.changes.outputs.code == 'true'
```

**GitLab CI:**

```yaml
build:
  rules:
    - changes:
        - src/**
        - package.json
      when: on_success
    - when: never
```

---

## 3. Fan-out / fan-in

[ID: cicd-wiki-fan-out]

**Problem:** Running lint, test, security scan, and type check
sequentially wastes time. A lint failure at minute 5 means tests
never run — but all checks are independent.

**Solution:** Independent jobs run in parallel (fan-out). A gate
job waits for all of them (fan-in) before allowing merge or
triggering the next stage.

```
        ┌→ lint ────────┐
        ├→ test ────────┤
build → ├→ security ────┼→ gate → deploy
        └→ type-check ──┘
```

**When to use:**

- Three or more independent validation steps
- Total sequential time exceeds 2 minutes
- Combine with the gate pattern for required checks

**GitHub Actions:**

```yaml
lint:
  needs: build
test:
  needs: build
security:
  needs: build

gate:
  needs: [lint, test, security]
  if: always()
  steps:
    - run: |
        for result in "${{ needs.lint.result }}" \
                       "${{ needs.test.result }}" \
                       "${{ needs.security.result }}"; do
          if [[ "$result" == "failure" ]]; then exit 1; fi
        done
```

---

## 4. Artifact promotion

[ID: cicd-wiki-artifact-promotion]

**Problem:** Rebuilding the application for each environment
introduces the risk that staging and production run different
code.

**Solution:** Build the artifact once. Tag it with the commit SHA.
Promote the same artifact through environments by retagging — never
rebuild.

```
build → push :sha → staging (sha) → promote → production (sha)
```

**When to use:**

- The project deploys to multiple environments
- Container images or binary artifacts are involved
- Reproducible builds matter (regulated, audited)

**Rules:**

- Tag images with the git commit SHA, not `latest`
- Promotion = retag or copy, not rebuild
- Environment differences come from configuration, not code
- The artifact that passed tests in staging is the artifact that
  runs in production

---

## 5. Dependency caching

[ID: cicd-wiki-caching]

**Problem:** Installing dependencies on every CI run adds minutes
to every pipeline. Package registries are external — network
latency and outages slow or break builds.

**Solution:** Cache the dependency directory between runs. Bust the
cache only when the lock file changes.

**When to use:**

- `npm ci`, `pip install`, or `go mod download` takes more than
  15 seconds
- The lock file changes infrequently relative to code changes

**GitHub Actions:**

```yaml
- uses: actions/setup-node@v6
  with:
    node-version: 22
    cache: npm # caches ~/.npm, keyed on package-lock.json
```

For custom caches:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ hashFiles('requirements.lock') }}
    restore-keys: pip-
```

**GitLab CI:**

```yaml
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push
```

---

## 6. Matrix build

[ID: cicd-wiki-matrix]

**Problem:** The project must work across multiple runtime versions,
operating systems, or configurations. Testing them sequentially
multiplies pipeline time.

**Solution:** Define a matrix of variables. The CI platform spawns
one job per combination, all running in parallel.

**When to use:**

- Libraries that support multiple runtime versions (Node 18/20/22)
- Cross-platform tools (Linux, macOS, Windows)
- Multiple database backends or feature flag combinations

**GitHub Actions:**

```yaml
test:
  strategy:
    matrix:
      node: [18, 20, 22]
      os: [ubuntu-latest, windows-latest]
    fail-fast: false
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/setup-node@v6
      with:
        node-version: ${{ matrix.node }}
    - run: npm ci && npm test
```

**Rules:**

- Use `fail-fast: false` to see all failures, not just the first
- Keep matrix size reasonable — 2-3 dimensions, not combinatorial
  explosion
- Use matrix `include`/`exclude` to cover only realistic
  combinations

---

## 7. Auto-merge for bot PRs

[ID: cicd-wiki-auto-merge]

**Problem:** Dependabot and Renovate create PRs for dependency
updates. Each requires manual review and merge — hundreds per
year pile up and go stale.

**Solution:** Enable auto-merge for bot PRs that pass all CI
checks. Restrict to patch and minor updates — major updates still
require human review.

**When to use:**

- Dependabot or Renovate is configured
- CI pipeline is trusted (tests, security scan, type check)
- Patch/minor updates are low-risk due to lock file and tests

**GitHub Actions:**

```yaml
auto-merge:
  runs-on: ubuntu-latest
  if: github.actor == 'dependabot[bot]'
  permissions:
    contents: write
    pull-requests: write
  steps:
    - uses: dependabot/fetch-metadata@v2
      id: meta
    - if: steps.meta.outputs.update-type != 'version-update:semver-major'
      run: gh pr merge --auto --squash "$PR_URL"
      env:
        PR_URL: ${{ github.event.pull_request.html_url }}
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Rules:**

- Only auto-merge patch and minor updates
- Major version bumps require manual review
- CI MUST pass before auto-merge triggers — never bypass checks
- Review the changelog of auto-merged updates periodically

---

## 8. Deploy preview

[ID: cicd-wiki-deploy-preview]

**Problem:** Reviewing code changes without seeing the result
requires the reviewer to check out the branch and build locally.
Visual and UX changes are hard to review from diffs alone.

**Solution:** Deploy an ephemeral preview environment for every PR.
The preview URL is posted as a PR comment. The environment is
destroyed when the PR is closed.

```
PR opened → build → deploy preview → comment URL
PR closed → destroy preview
```

**When to use:**

- Frontend or full-stack projects with visual output
- Stakeholders who review without a local dev environment
- Design changes that need visual sign-off

**Rules:**

- Preview environments MUST NOT have access to production data
- Preview URLs SHOULD be unique per PR (e.g. `pr-123.preview.example.com`)
- Destroy previews on PR close — do not accumulate stale environments
- Do not deploy previews for docs-only changes (combine with path
  filtering)
