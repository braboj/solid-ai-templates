# Base — Git Conventions
[ID: base-git]

## Committer identity
- Configure git with your full name and a consistent, professional email address
- Do not use private or personal email addresses for work repositories
- Identity must not change — git history and tooling depend on consistent
  authorship

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
- **A closing keyword auto-closes even when negated** — GitHub matches
  the bare `close/fix/resolve #N` substring regardless of surrounding
  words, so "does not close #N" in a PR body or commit still closes #N
  on merge. To reference an issue without closing it, write "part of #N"
  or `#N` alone — never a closing keyword next to the number unless the
  change truly resolves it
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
  - This rule applies to one-directional (source → artifact)
    derivations only. An artifact that also serves as, or feeds, the
    source of truth is bidirectional — the tell is an `--apply` or
    ingest step that reads the artifact back into the source. Do NOT
    auto-regenerate a bidirectional artifact from the pipeline it
    feeds: regeneration overwrites human-verified values. Refresh it
    only through the human-in-the-loop step that owns it, and flag
    the staleness explicitly instead
- **Before merging**, review the diff against the base branch. Follow
  `templates/base/core/review.md` priority order: security → correctness →
  clarity →
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
- Regenerate a known-current control artifact on its own first. A zero
  diff proves the generator is byte-deterministic in this environment
  and already matches the committed baseline, so every remaining diff
  is genuine change. A non-zero control diff means the environment
  disagrees with whatever produced the committed files — reconcile
  that before committing, or ship a spurious mass rewrite disguised as
  the intended change
- Mask the known-volatile parts, then diff the remainder. A
  self-contained bundle carries pieces that legitimately change every
  run — an embedded base64 blob, a generation timestamp, a build id. A
  clean masked remainder proves the data and prose are untouched and
  the change lives only where intended:

```bash
mask() { sed -E 's/base64,[A-Za-z0-9+/=]+/base64,#/g' "$1"; }
diff <(mask old.html) <(mask new.html) | grep -v 'generated '
```

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
  settings to prevent stale branches from accumulating. It fires on
  merge only — a PR closed without merging leaves its branch behind
  permanently, so branch hygiene is not fully automatic. It is the
  safe way to delete a branch under a stack, because deletion as part
  of the merge retargets dependent PRs rather than closing them
- SHOULD set `fetch.prune` so every fetch reconciles remote-tracking
  refs deleted on the server — the client-side complement to the
  setting above. Without it, `origin/<branch>` survives the branch it
  points at and reads as a branch that will not delete
- SHOULD use one focused commit per scope-slice on the branch
  rather than per-folder atomic commits. The squash collapses
  them on merge, so the per-folder narrative is wasted effort —
  only the squash commit lands on main. Document the per-folder
  breakdown in the PR description, where it stays after merge.
  Use path globs in `git add` for staging hygiene when needed.

### Merging a batch of PRs

Where branch protection requires branches be up to date before merging,
only the first PR in a batch merges cleanly. That merge moves the base
and makes every other open PR stale, so the next merge is refused:

```
Pull request #<N> is not mergeable: the head branch is not up to date
with the base branch.
```

This is a staleness check on the ref, not a content conflict. It fires
even when the two PRs touch entirely disjoint files, and even when
neither was stacked on the other — so neither "De-stacking a dependent
branch" nor "Merging a stack" explains it.

- MUST merge the base into every remaining PR of the batch after each
  merge, and let its checks re-run before merging it
- MUST NOT read the refusal as a conflict — merging the base in and
  pushing is the whole fix; no rebase, no fresh branch, no force-push
- SHOULD budget one update-plus-CI cycle per PR after the first. A
  batch of N ready PRs is N merges and N-1 update cycles, which is
  what makes merging a batch cost more than its diffs suggest

### Ordered documents merge cleanly and still collide

A clean merge proves the *edits* did not overlap. It proves nothing about
whether the *result* is coherent, and for a document with an ordered
structure those are different questions.

Two branches each add a section to the same numbered document. One appends
3.9 at the end; the other inserts 3.5 and renumbers the tail, so its last
section also becomes 3.9. The edits touch different regions, so git merges
them without a conflict and the result carries two sections numbered 3.9.
Nothing reports it — not the merge, not the checks, not a reviewer reading
either diff, because each diff is individually correct. The defect exists
only in the combination. Here a conflict would have been the good outcome:
it would have forced the reconciliation the clean merge skipped.

The existing rules do not reach it. Squash-merge safety is about commits
being orphaned, not content colliding. `Merging a batch of PRs` tells you
to merge the base in and re-run the checks, which resolves the staleness
and produces exactly this clean, wrong merge.

- MUST verify the merged numbering, not merely that the merge was clean,
  when two or more open pull requests edit one document with an ordered or
  numbered structure. The second to merge owns the check
- MUST re-run it after merging the base in, not before — the collision is
  created by the combination, so a run against either branch alone reports
  a clean document
- Applies to any ordered structure a reader relies on: numbered sections,
  ordered procedures, lettered clauses, a table whose rows carry an index

The check. `PATHS` names the documents two open pull requests both touch:

```bash
py - <<'EOF'
import re

# The documents under review -- those more than one open branch edits.
PATHS = ["<file>"]

# A numbered heading (### 3.9 Title) and a list ordinal (  4. Step).
HEADING = re.compile(r"^(#{1,6}) +([0-9]+(?:\.[0-9]+)*)\.? ")
LISTITEM = re.compile(r"^\s*([0-9]+)\. ")
PLAIN = re.compile(r"^#{1,6} ")

for path in PATHS:
    group, runs, problems, total = "(top)", {}, [], 0
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        match = HEADING.match(line)
        if match:
            parts = match.group(2).split(".")
            # Group a numbered heading under its parent, so 3.x and 4.x are
            # separate runs and each may legitimately restart.
            key = "%s %s" % (match.group(1), ".".join(parts[:-1]) or "(root)")
            value, label = int(parts[-1]), match.group(2)
            group = line.strip()
        else:
            if PLAIN.match(line):
                # A list restarts under each heading, numbered or not.
                group = line.strip()
                continue
            match = LISTITEM.match(line)
            if not match:
                continue
            key, value, label = group, int(match.group(1)), match.group(1)
        total += 1
        run = runs.setdefault(key, [])
        if value in run:
            problems.append("  %s:%d: %s repeats under %s"
                            % (path, n, label, key))
        elif run and value != run[-1] + 1:
            problems.append("  %s:%d: %s follows %s under %s"
                            % (path, n, label, run[-1], key))
        run.append(value)
    print("%s: %d ordinals across %d group(s)" % (path, total, len(runs)))
    for problem in problems:
        print(problem)
    if not total:
        print("  no ordinals found; the pattern drifted")
EOF
```

Pass condition: the command reports, for each document, how many ordinals
it inspected and how many groups they fall into, then prints nothing else.
A count of zero is a failure rather than a flat document — it means the
numbering pattern drifted and the check reached nothing. Adapt the two
patterns to the document's own convention before trusting a clean result;
a check calibrated against the wrong convention reports zero either way.

### De-stacking a dependent branch

When branch B was stacked on branch A and A has squash-merged to main,
B still contains A's now-duplicate commit. The tempting fix is to
rebase B onto main — but B is already pushed, so this requires a
force-push, which is forbidden.

- MUST NOT rebase the already-pushed B to drop A's commit
- MUST take one of two routes, both force-push free. Under squash
  merge they put byte-identical content on main, so the choice is
  about what happens to B, not about the result:
  - **Cherry-pick fresh** — branch off the updated main, cherry-pick
    only B's own commits, open the PR from the new branch, and delete
    the old stacked branch once its superseded PR is closed. Yields a
    clean, dependency-free diff, and discards B's review history
  - **Merge main in** — retarget B's PR to main, then merge the
    updated main into B and push. Keeps the PR, its comments and its
    approvals; carries a merge commit that the squash then discards
- SHOULD cherry-pick fresh when the diff will be read carefully and B
  has no review history worth keeping; SHOULD merge main in when B is
  already reviewed, or when the stack is deep enough that
  re-cherry-picking each level is error-prone
- Both routes keep remote history intact. Where merge is not the
  squash kind, the merge commit survives on main — cherry-pick fresh
  instead

The merge-main-in route needs a measurement, because its conflicts are
manufactured by the squash rather than by disagreement. A's commits are
replaced on the base by one equivalent commit that B is not descended
from, so the merge base stays the pre-stack tip and any file both sides
rewrote conflicts whole — including a file neither change is about.

- MUST expect the server-side update to refuse, and MUST NOT read the
  refusal as damage. B carries A's original commit while main carries A's
  squash, so every file both touched reads as modified on both sides.
  That is a content conflict, not the ref-staleness refusal described in
  `Merging a batch of PRs`, and it is the normal entry into the manual
  route — not a signal to rebase, to branch afresh, or to force-push
- MUST compare the conflict stages before resolving a whole-file
  conflict, rather than reasoning about which side is newer. Stage 2 is
  the branch, stage 3 is the base:

```bash
git diff --stat :3:<path> :2:<path>
```

  Pass condition: the command names the file and reports the lines
  resolving to the branch would add, remove and change. Additions only,
  with nothing removed and nothing changed, is the evidence that the
  branch discards nothing. Any removal is content on the base that B
  lacks, and taking B's side drops it
- MUST NOT apply "resolve in favour of the branch" without that
  evidence. The instruction is sound only while B is a strict superset
  of the base — true when A is the one thing that landed, false as soon
  as anything else merges in between. The narrative is usually right,
  and it is not a measurement
- MUST assert the resolution after resolving and before committing. Which
  assertion holds depends on how A merged, so name it before running it:
  - Where A was **rebase**-merged, main's content is byte-identical to
    what B already carries, so the merge can bring in nothing new and
    `git diff --stat HEAD` MUST be empty. Any output is either a real
    concurrent change to reconcile or a mis-resolved hunk
  - Where A was **squash**-merged, main carries one new commit whose
    content matches but whose history does not, so the tree-wide form
    does not hold. Assert per resolved file instead — `git diff
    <B-tip-before-merge> -- <path>` MUST be empty, proving the
    resolution reproduced B's content exactly
- MUST NOT read the merge's own diffstat as what the squash will land. It
  counts the base arriving on the branch, not the content going to main:
  a file the PR changes by 46 lines can report 156. Confirm the landing
  figures against the ones the PR reports — `git diff origin/main --stat`
  — and treat a mismatch in either direction as unresolved. Reading it the
  other way hides a real defect behind a number that looks explained

A whole-file conflict can also arrive for a reason nothing in the diff
explains. Where the merge base holds a byte that makes git classify the
blob as binary — a stray NUL the lower PR removed — there is no
three-way merge to attempt and every line reads as conflicting. The
stage comparison is what separates that case from a real disagreement,
and it is the same command either way.

### Merging a stack

How the base branch is deleted decides whether the PR stacked on it
survives. The two paths differ, and only one is safe:

- Deleting the branch **as part of the merge** — the repository's
  automatic head-branch deletion — retargets the dependent PR onto the
  merged PR's own base and leaves it open
- Deleting the branch **as a separate step**, such as a delete-branch
  flag on the merge command, does not. The host closes the dependent PR,
  and it cannot be reopened, because reopening requires the base ref to
  exist

Rules:

- MUST merge a stack bottom-up
- MUST NOT pass a delete-branch flag while any PR still targets the
  branch — let automatic deletion handle it, or retarget the dependent
  PR first and delete afterwards
- MUST read which of the two paths the repository actually takes before
  merging a stack. It is a repository setting, not a property of the
  merge command, so the command a maintainer types looks identical either
  way and the safe path is only available where the setting is on:

```bash
gh api repos/<owner>/<repo> --jq '.delete_branch_on_merge'
```

  Pass condition: the command prints the setting for the named
  repository. `true` means the merge itself deletes the head branch and
  retargets the dependent PR. `false` means nothing deletes it, the
  branch survives the merge, and any later deletion is the separate step
  that closes the dependent PR permanently — so retarget first
- To recover: recreate the deleted ref from the base branch, reopen the
  PR, retarget it, delete the ref again, then update the branch

The same shape bites automated dependency PRs. Merging a change to the
bot's own config invalidates every open PR it raised, closing them and
deleting their branches. Merge the pending bumps first when the intent
is to take them and change the policy.

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
- The README MUST conform to the structure and rules defined in
  `templates/base/core/readme.md`

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
  4. Verify that every issue closed since the previous tag carries the
     milestone being released — the check is below. Confirming a
     milestone's issues are all closed checks one direction of the
     relation only; work merged with no milestone is invisible to it, so
     the gate passes green while saying nothing about the commits
     actually being tagged
  5. Confirm the release pipeline has executed before — inspect the
     workflow's own run history, not the repository's; the check is
     below. A workflow file
     that merged green is evidence its YAML parses, not evidence its
     steps work: the pull request gate validated the branch path, and
     the tag path shares none of its jobs
  6. Where the history is empty, run the pipeline's steps by hand first
     — build, metadata check, artifact generation, and every assertion
     it makes — and reproduce each expected result locally. A release
     trigger is irreversible in a way the other pre-release checks are
     not: a tag on a public repository cannot be taken back cleanly, so
     the first execution MUST NOT be the one that ships
  7. Decide the order against every other pull request that is ready —
     the check is below. A release record describes the tree as of the
     release commit; anything merged between that commit and the tag
     ships inside the release with no entry naming it. Either merge what
     is ready before cutting the release branch, or hold it until the
     tag is pushed, but choose — the default is whichever happens to
     land first

The check for step 4, run from the repository root. It is left flush with
the margin rather than indented under the step: a renderer strips a fenced
block's own indentation, and an indent deeper than the code's first level
turns a nested line into a shallower one.

```bash
py - <<'EOF'
import json, re, subprocess

# Resolve the tag this release follows from the commit under release, not
# from a position in a list of tags.
previous = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                          capture_output=True, text=True).stdout.strip()
subjects = subprocess.run(["git", "log", "--format=%s", previous + "..HEAD"],
                          capture_output=True, text=True).stdout
merged = sorted({int(n) for n in re.findall(r"\(#(\d+)\)\s*$", subjects, re.M)})
print("previous tag: %s" % previous)
print("pull requests merged since: %d" % len(merged))
if not merged:
    print("no pull requests found since %s; either nothing is unreleased "
          "or the commit subject format drifted" % previous)
unmilestoned = []
for pr in merged:
    raw = subprocess.run(["gh", "pr", "view", str(pr), "--json",
                          "closingIssuesReferences"],
                         capture_output=True, text=True).stdout
    if not raw.strip():
        print("pull request %d could not be read" % pr)
        continue
    for ref in json.loads(raw).get("closingIssuesReferences") or []:
        issue = ref["number"]
        detail = subprocess.run(["gh", "issue", "view", str(issue), "--json",
                                 "milestone"],
                                capture_output=True, text=True).stdout
        if not detail.strip():
            print("issue %d could not be read" % issue)
            continue
        if not json.loads(detail).get("milestone"):
            unmilestoned.append((pr, issue))
for pr, issue in unmilestoned:
    print("pull request %d closed issue %d, which carries no milestone"
          % (pr, issue))
EOF
```

Pass condition: the command reports the previous tag and the number of
pull requests merged since it, then prints nothing. An empty result is a
failure too, since no pull requests found means either nothing is
unreleased or the commit subject format drifted. A deferred *open* issue
correctly carries no milestone — this covers only issues closed by merged
work sitting between two tags.

The check for step 5. Name the release workflow explicitly rather than
reading whichever run finished last — a repository with more than one
workflow answers a different question otherwise.

```bash
gh run list --workflow <release-workflow>.yml --limit 100 --json databaseId --jq 'length'
```

Pass condition: the command prints how many runs it found, capped by
`--limit`; the question is only whether that number is zero. A non-zero
count is the evidence the tag path has executed. `0` is the finding, not a
clean result — it prints `0` and exits `0`, so nothing surfaces it on its
own, and it means the tag about to be pushed is the workflow's first
execution and step 6 applies. An error naming an unknown workflow means
the filename drifted, which is a failure rather than an absence of runs.

The check for step 7, run from the release commit before the tag is
pushed. Nothing else reports this: both pull requests are green, both are
mergeable in either order, and on a repository whose protection does not
require branches be up to date neither goes stale when the other lands.
The post-release check does not reach it either — it compares the manifest
version against the tag, which agrees in both orderings.

```bash
previous=$(git describe --tags --abbrev=0)
echo "preceding tag: $previous"
git log --format='  carries: %s' "$previous..HEAD"
echo "commits carried: $(git log --format='%s' "$previous..HEAD" | wc -l)"
ready='select(.mergeStateStatus=="CLEAN")'
fmt='"  ready but unmerged: #\(.number) \(.title)"'
gh pr list --state open --json number,title,mergeStateStatus --jq ".[] | $ready | $fmt"
```

Pass condition: the command names the preceding tag, lists every commit
the release will carry with a count of them, and lists every open pull
request that is ready to merge. Each carried commit MUST have an entry in
the release record. Each pull request listed as ready is a decision, not a
warning — merge it into this release and record it, or hold it until the
tag is pushed. A carried count of zero is a failure rather than a clean
result: it means the tag would land on the same commit as its predecessor.

### Projects with a version manifest
  8. `git checkout -b chore/release-vX.Y.Z`
  9. Bump version in the project manifest (`package.json`,
     `pyproject.toml`, `Cargo.toml`, or equivalent) to `X.Y.Z`
  10. `git commit -m "chore: release vX.Y.Z"`
  11. Push, open PR, merge
  12. `git checkout main && git pull`
  13. `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
     — release tags MUST be annotated (`-a`/`-s`); a lightweight
     `git tag vX.Y.Z` is invisible to `git describe`, which reports
     a stale version to submodule/`describe` consumers
  14. SHOULD create a GitHub Release from the tag:
      `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`
      — a pushed tag alone does NOT create a Releases page entry.

### Post-release verification
  15. Verify the manifest version matches the tag — e.g.
      `grep '"version"' package.json` matches `git describe --tags`
  16. A mismatch means the bump was missed or the wrong commit was
      tagged — fix before announcing the release

### Projects without a version manifest (no-build)
  8. `git checkout main && git pull`
  9. `git tag -a vX.Y.Z -m "vX.Y.Z — <milestone name>"`
     — the `-a` is mandatory: a lightweight `git tag` is skipped by
     `git describe`, so consumers report a stale version
  10. `git push origin vX.Y.Z`
  11. Create a GitHub Release with auto-generated notes:
     `gh release create vX.Y.Z --title "vX.Y.Z — <milestone name>"
     --generate-notes`

## Migrating to a new repository

A migration moves the source. It does not move the settings around the
source, and it does not move the evidence the open issues were raised
against. Both losses are silent, and the migration looks complete
because every file and every issue arrived.

The order is forced by issue transfer, so treat it as a sequence rather
than a set of tasks:

  1. Create the destination **private**. A private repository's issue
     cannot be transferred to a public one, and both repositories MUST
     share an owner. Publishing first means recreating each issue by
     hand and losing its comments and its number
  2. Clone the label set BEFORE transferring. A label that does not
     already exist in the destination by name is dropped from the
     transferred issue silently — the issue arrives, the label does not
  3. Transfer the issues
  4. Grep the transferred bodies for surviving bare `#N` references. The
     host rewrites most of them to the fully-qualified form and not all,
     and a survivor resolves against the destination, pointing at a
     different issue than it did before
  5. Verify the destination's security-and-analysis settings against the
     source's — the check is below, and there is no other signal
  6. Re-verify the open issue cohort as a batch — see below
  7. Publish

The check for step 5. Repository-level security controls are
per-repository and a new repository does not inherit them, so a
repository created to carry a clean history comes up with every control
off:

```bash
for repo in <source-owner>/<source-repo> <dest-owner>/<dest-repo>; do
  echo "$repo"
  gh api "repos/$repo" --jq '.security_and_analysis | to_entries[] | "  \(.key): \(.value.status)"'
done
```

Pass condition: both repositories print the same keys with the same
statuses. A control `enabled` on the source and `disabled` or absent on
the destination was lost in the migration. `to_entries cannot be applied
to: null` under a repository name is a failure, not an absence of
controls — the field is returned only to an administrator of that
repository, so the message means the token cannot read it and the
comparison never happened. Run it before publishing:
a repository built to improve on a security incident can otherwise go
public with weaker protection than the one it replaced.

- MUST re-verify every open issue as a cohort at the migration, rather
  than one issue per session afterwards. A migration, clean-tree import,
  fork or extraction invalidates all of them at once: each is a claim
  about a tree that no longer exists, and the issue survives the move
  while its evidence does not
- The cohort shares one cause, so sweeping it is cheaper than
  rediscovering it. Expect two shapes — an issue whose cited defect the
  import already fixed, and an issue deferring to another that was
  closed and never covered the condition it deferred on. Both falsify in
  under a minute, with a grep for the cited defect and one issue read
- Acting on such an issue produces work that looks real throughout. A
  rewrite of a file that needed two sentences is indistinguishable from
  a rewrite that was needed, until someone checks the tree the issue
  described

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
- Share the editor config that mirrors the CI gates through an
  allowlist rather than ignoring the directory wholesale — ignore
  `.vscode/*`, then re-include `!settings.json` and
  `!extensions.json`. The shared project setup is versioned while
  per-user editor state stays ignored
- Use [gitignore.io](https://gitignore.io) or GitHub's templates as a
  starting point — then trim to what the project actually needs
- Do not ignore lockfiles — they MUST be committed
