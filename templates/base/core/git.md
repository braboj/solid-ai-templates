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

### Post-release verification
  10. Verify the manifest version matches the tag — e.g.
      `grep '"version"' package.json` matches `git describe --tags`
  11. A mismatch means the bump was missed or the wrong commit was
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
