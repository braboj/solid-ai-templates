# Base — Git Conventions
[ID: base-git]

## Committer identity
- Configure git with your full name and a consistent, professional email address
- Do not use private or personal email addresses for work repositories
- Identity must not change — git history and tooling depend on consistent authorship

## Commit messages
- Use conventional commit prefixes:
  `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `style:`, `test:`
- Keep the subject line under 80 characters
- Use the imperative mood: "add feature" not "added feature"

## Branching
- Always work on a branch — never commit directly to `main`
- Branch naming: `feat/description`, `fix/description`, `chore/description`,
  `docs/description`

## Pull requests
- PRs should be small and focused — one concern per PR
- Always test locally before committing
- **Repeat the closing keyword before each issue number** when a PR
  closes more than one issue: `Closes #a, closes #b, closes #c` closes
  all three. `Closes #a, #b, #c` closes only `#a` — a bare `#b`/`#c` is
  a plain reference, not a closing one, and stays open after merge.
- **Regenerate derived artifacts in the same PR** — when a change
  affects generated or derived files committed to the repo (extractor
  outputs, snapshot fixtures, generated docs), regenerate them in the
  fixing PR, not a follow-up. A stale artifact is indistinguishable
  from a regression to the next reviewer. Include a before/after
  summary (verdict matrix, delta table, screenshot diff) in the PR
  body so reviewers see the user-visible impact without re-running
  the pipeline.
  - When regeneration is too expensive to bundle (e.g. >30s in CI or
    >100 files), the PR MUST open a tracked follow-up issue AND state
    the STALE accounting explicitly (N files affected, named or
    globbed) — silent staleness is the failure mode
- **Before merging**, review the diff against the base branch. Follow
  `templates/base/core/review.md` priority order: security → correctness → clarity →
  conventions. Check CI passes. Only merge after the review passes.
- **Before pushing or creating a PR**, check `git status` and list open PRs.
  If the previous PR is closed or merged, create a new branch rather than
  pushing to a stale one.
- **Never force-push a branch**, including with `--force-with-lease`.
  Force-push rewrites shared history and can clobber upstream commits
  (collaborators, agents, CI bots) that haven't been fetched locally.
  - When a PR branch is behind `main`, merge `main` into the branch —
    do not rebase and force-push. On GitHub, use the "Update branch"
    button or `gh pr update-branch <N>`.
  - Squash-merge collapses the merge commit on merge, so local branch
    shape does not pollute `main` history.
- **After a PR is merged**, delete both remote and local branch, then pull main:
  ```
  git branch -d <branch>
  git push origin --delete <branch>
  git checkout main && git pull
  ```

### Verifying regenerated artifacts

After regenerating derived artifacts and before staging them, verify
the diff is real and the output is correct.

- Filter line-ending and whitespace noise first: `git diff
  --ignore-all-space <file>` with no output means the change is
  CRLF/whitespace-only — `git checkout -- <file>` to drop it so the
  PR stays scoped to genuine content (and the noise does not reappear
  as a fake regression on another OS)
- Binary artifacts (images, diagrams, screenshots, plots) diff as
  "Binary files differ" — opaque to git and often uncovered by the
  test suite. Open each in a viewer (or an image-read tool for agent
  workflows) and confirm it tracks its source data with no corruption
- When a fix regenerates many artifacts, pair a spot-check of 3-5
  representative cases (the fix's primary target, the most complex
  case, a clean baseline) with a global metric that aggregates across
  the population (test pass rate, link check, accessibility score,
  calibration result). The spot-check catches broken regeneration;
  the metric catches population-wide drift — together they match full
  per-artifact review at a fraction of the cost

### Squash-merge safety

When using squash merge, the branch commits become orphaned after
the PR merges — only the squash commit lands on main. If a branch
contains multiple concerns and only one is merged via PR, the
remaining commits are silently lost.

- MUST NOT mix unrelated changes on a single branch
- MUST verify that all branch commits are accounted for before
  deleting a branch — compare the squash diff against the branch diff
- SHOULD enable "automatically delete head branches" in repository
  settings to prevent stale branches from accumulating
- SHOULD use one focused commit per scope-slice on the branch
  rather than per-folder atomic commits. The squash collapses
  them on merge, so the per-folder narrative is wasted effort —
  only the squash commit lands on main. Document the per-folder
  breakdown in the PR description, where it stays after merge.
  Use path globs in `git add` for staging hygiene when needed.

### De-stacking a dependent branch

When branch B was stacked on branch A and A has squash-merged to main,
B still contains A's now-duplicate commit. The tempting fix is to
rebase B onto main — but B is already pushed, so this requires a
force-push, which is forbidden.

- MUST NOT rebase the already-pushed B to drop A's commit
- MUST branch fresh off the updated main and cherry-pick only B's
  own commits; open the PR from the new branch
- Delete the old stacked branch once its superseded PR is closed

This keeps remote history intact and yields a clean,
dependency-free diff.

### Bulk operations

When a bulk operation (cohort emit, codebase-wide migration, mass
rename, dependency bump) hits a per-item bug mid-run, do not stall
the whole batch on one broken item — split it into two stacked PRs.

- PR A ships the bulk operation with the broken items in an explicit
  skip-list and a tracking issue filed for the bug
- PR B, stacked on A, fixes the bug, re-runs the operation on the
  skipped items, and removes the skip-list
- The skip-list MUST live in the operation's input filter, not in the
  target data; each entry MUST reference the tracking issue
- Merge A first, then refresh B onto updated main per "De-stacking a
  dependent branch" before merging it

Two surgical PRs beat one stalled PR: PR A ships the work that is
done, PR B ships the work that was blocked, and each is reviewed on
its own scope.

### Close-and-resubmit when framing drifts

When a PR's framing turns out to be wrong mid-review — the rule it
amends should be superseded, the feature it adds belongs on a
different layer, the bug it fixes is a symptom of a deeper issue —
the title, branch name, body, and commit messages no longer match
the actual decision.

- SHOULD close the PR and open a new one with the correct framing,
  rather than rewriting title, body, and commit history in place
- The closed PR remains as the record of the rejected framing —
  leave a comment pointing at the replacement
- The new PR is internally consistent end-to-end: title, branch,
  commits, and body all describe the actual decision
- Indicator that close-and-resubmit is the right move: the branch
  name is no longer accurate

When NOT to close-and-resubmit:
- Trivial title/body wording fixes — just amend
- Scope additions during review that align with the original
  framing — push more commits to the same branch
- Renamed-but-equivalent decisions — just amend

## README
- Every repository MUST contain a `README.md`
- The README MUST conform to the structure and rules defined in `templates/base/core/readme.md`

## Versioning
- Use [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`
  - **MAJOR** — incompatible API or breaking changes
  - **MINOR** — new functionality, backwards-compatible
  - **PATCH** — backwards-compatible bug fixes
- Tags use the `v` prefix: `v1.0.0`, `v0.3.1`
- Pre-release versions: `v1.0.0-alpha.1`, `v1.0.0-rc.1`

## Release process

### Pre-release checks
  1. Check for unmerged branches: `git branch --no-merged main`
     — investigate any results before proceeding
  2. Check for orphaned commits: `git fsck --unreachable --no-reflogs
     | grep commit` — verify no unique work is lost
  3. Run a 360-degree analysis if the project uses
     `templates/base/workflow/360.md` — the project SHOULD NOT
     ship with critical findings unresolved

### Projects with a version manifest
  4. `git checkout -b chore/release-vX.Y.Z`
  5. Bump version in the project manifest (`package.json`,
     `pyproject.toml`, `Cargo.toml`, or equivalent) to `X.Y.Z`
  6. `git commit -m "chore: release vX.Y.Z"`
  7. Push, open PR, merge
  8. `git checkout main && git pull`
  9. `git tag vX.Y.Z && git push origin vX.Y.Z`
  10. SHOULD create a GitHub Release from the tag:
      `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`
      — a pushed tag alone does NOT create a Releases page entry.

### Post-release verification
  11. Verify the manifest version matches the tag — e.g.
      `grep '"version"' package.json` matches `git describe --tags`
  12. A mismatch means the bump was missed or the wrong commit was
      tagged — fix before announcing the release

### Projects without a version manifest (no-build)
  4. `git checkout main && git pull`
  5. `git tag -a vX.Y.Z -m "vX.Y.Z — <milestone name>"`
  6. `git push origin vX.Y.Z`
  7. Create a GitHub Release with auto-generated notes:
     `gh release create vX.Y.Z --title "vX.Y.Z — <milestone name>" --generate-notes`

## General
- Do not commit build output, secrets, or dependency directories
- Do not commit generated files that can be reproduced by running a
  build command
- Treat every repository as if it were public — no secrets,
  credentials, or sensitive information in source files or history

## `.gitignore`
- Every repository MUST have a `.gitignore` file
- Ignore at minimum:
  - **Dependencies** — `node_modules/`, `.venv/`, `vendor/`
  - **Build output** — `dist/`, `build/`, `out/`, `*.pyc`, `__pycache__/`
  - **Secrets** — `.env`, `.env.local`, `*.pem`, `*.key`
  - **IDE/editor** — `.idea/`, `.vscode/`, `*.swp`, `*.swo`
  - **OS files** — `.DS_Store`, `Thumbs.db`, `desktop.ini`
  - **Test/coverage** — `coverage/`, `.coverage`, `htmlcov/`
- Use [gitignore.io](https://gitignore.io) or GitHub's templates as a
  starting point — then trim to what the project actually needs
- Do not ignore lockfiles — they MUST be committed
