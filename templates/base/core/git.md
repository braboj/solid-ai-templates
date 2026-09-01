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
- **A local run is evidence about one platform.** Read the CI run for the
  push before describing the change as good. Where development and CI
  differ in operating system, interpreter version or locale, a green
  local suite and a green pipeline are different claims, and only the
  second covers what the project ships on. A pipeline check at session
  start is a different moment — it catches one broken before you began,
  not one you broke and are about to report as clean
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
- **Re-run the verification a pull request body claims, rather than
  reading it, whenever the base has advanced since the body was
  written.** A well-written body carries evidence — a grep that found no
  surviving references, a count, a command whose output justified the
  change. That evidence is scoped to the base it was produced against,
  and a commit landing afterwards can falsify it without producing a
  conflict, a failing check, or any other signal: the merge is clean, the
  checks pass against the merge commit, and the body still reads as
  verified. It matters most for a change that proves an ABSENCE — a
  deleted file, a removed reference, a retired flag — where the later
  commit reintroduces the very thing the body proved gone
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

Regenerating is owed by the edit, not by the review. Every rule below
inspects output that already exists, and none of them fires if the
regeneration never ran.

- MUST regenerate the artifact and stage both together in the change
  that edits a source. Where an artifact is derived from sources under
  version control, a test suite that does not read the artifact passes
  on a stale one — so local green is not evidence the artifact is
  current, and the first signal is whichever CI step compares the two,
  after the branch is pushed and the author has moved on
- MUST name the regeneration trigger beside the sources it derives from,
  so an author editing a source meets the obligation without having to
  know the build graph
- MUST run the staleness comparison AFTER the edit. Run before it, the
  comparison reports the previous state and reads as a pass:

```bash
<regenerate-command>
git diff --stat -- <artifact-path>
```

  Pass condition: empty. Any output means the committed artifact does not
  match what its sources produce, and the regeneration is part of this
  change rather than a follow-up. A regenerator that is not idempotent
  fails this against an already-current artifact, which is a defect in the
  generator rather than in the change under review

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
- MUST NOT replace the squash subject at merge time. The default is
  the pull request title with its number appended, and a check
  reading the log resolves that number back to the merged work and
  the issues it closed. A supplied subject keeps the title and drops
  the append, so the reference is absent from the only record such a
  check reads — and the commit looks correct, because the half a
  human reads is the half that survived
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
- SHOULD read a green check as naming the base it ran against. The
  paragraph above explains why the refusal is not a conflict, which
  makes the cycle read as bookkeeping — true only while the members are
  disjoint. Where two of them touch the same file, each carries checks
  measured against a base the other had not landed on, and the update
  cycle is the first and only execution of the combined result. A
  mergeable status asserts that the texts combine without conflict; it
  is not a claim that the combination passes

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
  way, and the safe path is only available where the setting is on. A
  setting that is off is the finding, not the reading:

```bash
py - <<'EOF'
import json, subprocess

# Only the automatic path is safe: it retargets a dependent pull request
# as it removes the branch. Where the setting is off nothing deletes a
# merged head branch, so every deletion is the manual kind, which closes
# the dependent instead of moving it.
raw = subprocess.run(["gh", "repo", "view", "--json", "deleteBranchOnMerge"],
                     capture_output=True, text=True).stdout
settings = json.loads(raw or "{}")

print("repository settings read: %d" % len(settings))

unsafe = [name for name, value in settings.items() if value is not True]
print("settings leaving no safe deletion path: %d" % len(unsafe))
for name in unsafe:
    print("  %s is %r -- nothing deletes a merged head branch, so every "
          "deletion is the manual kind, which closes any pull request "
          "targeting it" % (name, settings[name]))
EOF
```

  Pass condition: the first count is above zero, proving the settings
  were read rather than the command failing quietly, and the second is
  zero. Reading the setting is not by itself a check — both values print,
  so on the older form no configuration was ever a finding
- The setting licenses nothing. `true` describes what an *automatic*
  deletion does. Passing a delete-branch flag explicitly takes the manual
  path on a `true` repository exactly as it does on a `false` one, and
  closes the dependent either way — measured here, by losing a pull
  request that way on a repository configured `true`. A maintainer who
  reads the setting, sees `true` and types the flag has followed the
  reading and lost the pull request
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
  3. Where the project runs a periodic project-wide audit and this
     release moves the minor or major version, run one before the
     release — it SHOULD NOT ship with critical findings unresolved. A
     patch release owes neither the audit nor a record declining it, and
     a project with no such audit skips this step rather than inventing
     one for the release. The check is below
  4. Where the release is scoped to a milestone, verify that every issue
     closed since the previous tag carries that milestone — the check is
     below. Confirming a milestone's issues are all closed checks one
     direction of the relation only; work merged with no milestone is
     invisible to it, so the gate passes green while saying nothing about
     the commits actually being tagged. A routine release that was never
     scoped as a milestone skips this check rather than backfilling one:
     a planning artifact created after the fact carries no information,
     and every issue closed since the tag would otherwise be reported in
     the same shape as a finding
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
  8. Where the project keeps a changelog, reconcile its `Unreleased`
     section against what merged since the previous tag — the check is
     below. The release cuts that section into a dated entry, and the
     cut assumes each merged change added its line. Nothing else
     verifies that it did: each pull request is individually fine,
     omitting an entry breaks no gate, and the reviewer is reading a
     diff that has no changelog hunk whose absence they could notice

Which of these steps are enforced, audited one step at a time.
Enforcement is not transitive between neighbours: a step's gate covers
that step and says nothing about the one below it, however the sequence
reads. Four of the eight carry no pass condition:

| Step | Enforced by |
| --- | --- |
| 1 | `git branch --no-merged main`, run by hand. Command, no pass condition — "investigate any results" is a judgement |
| 2 | `git fsck --unreachable --no-reflogs`, run by hand. Same shape as step 1 |
| 3 | the periodic-review-scope check below. Conditional on the project running a periodic project-wide audit at all |
| 4 | the milestone-coverage check below |
| 5 | the pipeline-history check below |
| 6 | **nothing**, and it is the step to gate first |
| 7 | the release-ordering check below |
| 8 | the changelog-completeness check below. Conditional on the project keeping a changelog |

Step 6 is unenforced and unrecoverable, which is the combination the rule
says to address first: its own text records that a tag on a public
repository cannot be taken back cleanly, so a first pipeline execution
that ships is not an execution that can be retried. Until it carries a
check, the release proposal MUST name each pipeline step run by hand and
the result it produced. That record is what makes its absence visible —
an operator who skipped step 6 writes nothing, and nothing else reports
it.

Each check below carries a name, and every document that sends an operator
to one MUST refer to it by that name. A step number identifies a check only
within the sequence that numbers it: this file holds two sequences that both
have a step 5, and a consuming project's runbook numbers its own release
differently again, so a cross-document step number points at whichever
sequence the reader assumes. Selecting a check by position fails the same
way — this file holds several `py - <<'EOF'` blocks, and taking the first
one finds a real, runnable check answering a different question. Locate a
check by asserting on something only it contains.

**The milestone-coverage check** — step 4 of the sequence above. Run it
from the repository root. It is left flush with the margin rather than
indented under the step: a renderer strips a fenced block's own
indentation, and an indent deeper than the code's first level turns a
nested line into a shallower one.

```bash
py - <<'EOF'
import json, re, subprocess, sys

# The check prints a milestone title, which may hold characters the
# console code page cannot encode. Without this the check raises
# UnicodeEncodeError on the finding it exists to report.
sys.stdout.reconfigure(encoding="utf-8")

# The milestone this release is scoped to, or None for a routine release
# that was never scoped as one. Setting it is the decision the step asks
# for: a release with no milestone skips the check rather than reporting
# every issue closed since the tag.
MILESTONE = None

# Decode every subprocess as UTF-8 rather than the locale encoding. `gh`
# and `git` emit UTF-8; on a console whose code page is not, text=True
# alone decodes a non-ASCII milestone title into different characters
# than the literal it is compared against, and the check reports a
# mismatch between a string and itself.
RUN = dict(capture_output=True, text=True, encoding="utf-8")

if MILESTONE is None:
    print("release not scoped to a milestone; this check does not apply")
    raise SystemExit(3)

# Resolve the tag this release follows from the commit under release, not
# from a position in a list of tags.
previous = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                          **RUN).stdout.strip()
subjects = subprocess.run(["git", "log", "--format=%s", previous + "..HEAD"],
                          **RUN).stdout

# A subject carries the issue number, the pull request number, or both:
# the title convention puts the issue at the end and the squash appends
# the pull request. Read every reference in that trailing run rather than
# the last one alone, and assume nothing about which kind a number names.
references = set()
for subject in subjects.splitlines():
    trailing = re.search(r"((?:\s*\(#\d+\))+)\s*$", subject)
    if trailing:
        references.update(int(n) for n in re.findall(r"\d+",
                                                     trailing.group(1)))
merged = sorted(references)
print("previous tag: %s" % previous)
print("references in subjects since: %d" % len(merged))
if not merged:
    print("no references found since %s; either nothing is unreleased "
          "or the commit subject format drifted" % previous)

findings, seen = [], set()


def covered(issue, whose):
    """Record the milestone an issue carries, if it is not this release's."""
    if issue in seen:
        return
    seen.add(issue)
    detail = subprocess.run(["gh", "issue", "view", str(issue), "--json",
                             "milestone"], **RUN)
    if detail.returncode != 0:
        findings.append("issue %d could not be read" % issue)
        return
    found = (json.loads(detail.stdout).get("milestone") or {}).get("title")
    if found != MILESTONE:
        carries = "no milestone" if found is None else "milestone %s" % found
        findings.append("%s issue %d, which carries %s"
                        % (whose, issue, carries))


kinds = {"pull request": 0, "issue": 0}
for number in merged:
    # The issues endpoint answers for either kind and says which: a pull
    # request carries a `pull_request` key and an issue does not. Ask it
    # rather than sending every number to `gh pr view`, which fails on an
    # issue and establishes nothing about the release.
    proc = subprocess.run(
        ["gh", "api", "repos/{owner}/{repo}/issues/%d" % number], **RUN)

    # `gh api` prints an error body to stdout, so output is not evidence
    # that the call succeeded. Ask the exit status.
    if proc.returncode != 0:
        findings.append("reference %d could not be read" % number)
        continue

    if json.loads(proc.stdout).get("pull_request") is None:
        kinds["issue"] += 1
        covered(number, "a subject names")
        continue

    kinds["pull request"] += 1
    raw = subprocess.run(["gh", "pr", "view", str(number), "--json",
                          "closingIssuesReferences"], **RUN)
    if raw.returncode != 0:
        findings.append("pull request %d could not be read" % number)
        continue
    for ref in json.loads(raw.stdout).get("closingIssuesReferences") or []:
        covered(ref["number"], "pull request %d closed" % number)

print("resolved: %d pull request(s), %d issue(s)"
      % (kinds["pull request"], kinds["issue"]))
for finding in findings:
    print(finding)
EOF
```

Pass condition: with `MILESTONE` set, the command reports the previous
tag, how many references it found in the subjects since, and how many of
those resolved to a pull request and how many to an issue — then prints
nothing. An empty result is a failure too, since no references found
means either nothing is unreleased or the commit subject format drifted.
A reference it cannot read is a finding rather than a silent skip: the
gate establishes nothing about a number it did not resolve. A deferred
*open* issue correctly carries no milestone — this covers only issues
closed by merged work sitting between two tags.

The two counts are the check reading the history this convention actually
produces. A subject may name the issue, the pull request, or both, so a
resolver assuming one kind reports on the subset it happens to fit and
prints a healthy total while doing it.

With `MILESTONE` left at `None` the command reports that the check does
not apply, on exit status 3 — the reserved status for a check answering
that its question is not live, which is neither a pass nor a skip: the
line is the record that a routine release was cut deliberately without
one. Distinguish it from a
finding before running anything — a milestone-scoped release left at
`None` reports "does not apply" and proves nothing.

**The pipeline-history check** — step 5 of the sequence above. Name the
release workflow explicitly rather than reading whichever run finished
last — a repository with more than one workflow answers a different
question otherwise.

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

**The release-ordering check** — step 7 of the sequence above. Run it from
the release commit before the tag is pushed. Nothing else reports this:
both pull requests are green, both are mergeable in either order, and on a
repository whose protection does not require branches be up to date,
neither goes stale when the other lands. The post-release check does not
reach it either — it compares the manifest version against the tag, which
agrees in both orderings.

```bash
previous=$(git describe --tags --abbrev=0)
if git describe --tags --exact-match HEAD >/dev/null 2>&1; then
  echo "HEAD is $previous; no release is in preparation, so this check does not apply"
  exit 3
fi
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

That reading only holds while a release is being prepared, which is why
the command answers that question first. With the tag already at HEAD it
reports that it does not apply and stops on exit status 3, rather than
printing the failure-shaped zero its own pass condition describes. The emptiness is
not the detector: a carried count of zero the day after a release reads
as one the day after that, because an unrelated change merged, and
nothing was fixed in between.

The tag guard is complete here and would not be for the check below. A
carried count of zero requires HEAD to be the tag, which is exactly what
exit 3 covers; an uncut `Unreleased` section is instead the ordinary state
of every untagged commit. The two checks ask the same question and answer
it differently because their failure shapes differ.

**The changelog-completeness check** — step 8 of the sequence above. Run it
from the release commit before the `Unreleased` section is cut. The failure
it catches has no signal anywhere else: each pull request is individually
fine, the release is individually fine because the block gets cut and the
entry gets dated, and a gate asserting the entry EXISTS passes on an entry
describing almost nothing. Afterwards the entry is published and immutable
in practice, and reconstructing what the release contained means reading
the commit range by hand — the work the changelog existed to save.

```bash
# The release this check is preparing, or empty on an ordinary day.
# Setting it is the decision the step asks for: the check reads the
# `Unreleased` section against the commits a cut would carry, and no state
# of the repository distinguishes that moment from an ordinary one.
RELEASE=

if [ -z "$RELEASE" ]; then
  echo "no release is in preparation; this check does not apply"
  exit 3
fi
previous=$(git describe --tags --abbrev=0)
echo "commits since $previous: $(git log --format='%s' "$previous..HEAD" | wc -l)"
echo "entries in Unreleased: $(awk '/^## /{ n++ } n==1 && /^- /' CHANGELOG.md | wc -l)"
git log --format='  carried: %s' "$previous..HEAD"
```

Its moment is the release commit before the `Unreleased` section is cut,
so it asks first whether that moment is live — and asks the operator,
because nothing in the repository's state answers it. An untagged HEAD does
not mean a release is in preparation. It means a commit has landed since
the last tag, which is the ordinary condition of a repository between
releases, so a detector reading it as the moment reports the failure shape
on almost every day. A check whose ordinary output is its defect output
trains its reader to skip it.

Pass condition: the command prints both counts and lists every carried
commit once `RELEASE` names the release being prepared, and the operator
confirms each carried commit is either represented by an entry or is
deliberately not notable. The two
counts are NOT required to match — not every commit earns an entry. Zero
entries against commits carried is a failure where any carried commit is
notable; where every one of them is deliberately not, zero is the correct
reading. That is the guaranteed state directly after a cut, whose first
commit is the journal entry the release procedure records as owed. A count
of entries the listed commits cannot account for is the failure in the
other direction. Read the two numbers together: the observed failure this
check exists for was 37 commits against 2 entries, which no single-sided
assertion detects.

With `RELEASE` left empty the command reports that the check does not
apply, on exit status 3 — the same reserved status the milestone-coverage
check uses, and the same reason: the moment is a decision the operator
declares, not a state the repository can be asked for.

The check runs at release time and is the backstop, not the mechanism. The
entry is added by the change that causes it, per `base-docs`; a project
relying on this check to reconstruct the block at release time has already
lost the information it needs to do so.

### A currency gate compares non-strictly

The periodic project-wide audit above is the pre-release step a project
most often gates, by requiring the dated artifact it names — an audit, a
review, a sign-off — to be current with respect to the last release. Where
that artifact carries a date and no time, the comparison MUST admit a
record dated the release day. Requiring strictly-later makes a second
release on the day of the first impossible rather than merely unaudited:

```
previous release   2026-08-31          (shipped this morning)
newest record      cannot exceed today
verdict            fail, until tomorrow
```

Nothing clears it. Writing the artifact does not, because the new artifact
carries today's date. Declining the step does not either, wherever
declining is itself a dated record — it carries the same date and fails
the same comparison.

The strictness has a real motivation, which is what makes it easy to reach
for: a date with no time cannot separate an artifact written the morning
before a release from one written the evening after it, and only the
second covers the release. Refusing both is the cautious reading, and its
cost is invisible on the day the gate is written. It appears on the first
day two releases are wanted, and by then the procedure holds a step the
operator is invited to decline and cannot satisfy in any form — a worse
state than the ambiguity the strictness guarded against.

Comparing non-strictly leaves the case the gate exists for untouched: a
record older than the previous release still fails, and a missing record
still fails. One record then covers two same-day releases, which is the
intended outcome rather than a side effect. Recording a timestamp rather
than a date removes the ambiguity properly, and costs a rename of every
existing artifact plus every check that reads the filename shape — take
that where the artifacts are few, and loosen the comparison where they
are not.

Loosening it is a weakening of a gate and carries what attaches to one:
the same change MUST add an assertion for the same-day case, so a
comparison tightened back to strictly-later fails something rather than
passing green.

### A periodic review is owed by the releases that can move it

A project that runs a periodic project-wide audit and gates the release on
it has attached a review to the release event. Most releases are patches,
and a patch fixes a defect and changes no interface, so a review whose
subject is the shape of the project has nothing new to read on one. The
operator writes a record saying so and the tag proceeds.

That inverts the gate. A gate firing on an event class whose members
mostly cannot produce a finding trains the operator to produce the
artifact that clears it, and here the artifact is a document declining the
work — so the cheapest compliant path stops involving the work at all.
Nothing in the surrounding rules catches this: the check exists, it runs
correctly, and every signal available says it is working. The gate is not
too weak or too strong. It is scoped to the wrong event.

The obligation MUST therefore be scoped to the releases that change what
the review reads. A minor or major release owes the audit; a patch owes
nothing, neither report nor decline.

Two details travel with the narrowing, and both are easy to omit:

- A version the gate cannot parse MUST be a finding, never a pass. An
  unreadable version and an exempt version both mean the comparison does
  not run, and reading them alike turns a typo in a version literal into
  a silent exemption
- Narrowing a gate can retire its own negative controls. Fixtures named
  with a patch version stop firing the moment the gate skips patches, so
  the suite stays green while testing nothing. Re-point them at a minor
  or major version in the same change, and confirm each still fails
  before believing the narrowed gate

The deferral this replaces MUST NOT be a condition nothing polls. Making
the next audit due when some backlog reaches zero schedules nothing,
because no release meets the condition and nothing watches it — a
deferral with no watcher reads exactly like a live obligation.

**The periodic-review-scope check** — step 3 of the pre-release sequence
above. It answers whether this release owes the review, and where it does,
whether the record is current.

```bash
py - <<'EOF'
import os, re, subprocess

# The version being released, or empty on an ordinary day. Setting it is
# the decision the step asks for.
RELEASE = ""

# Where the project keeps its dated periodic audits, and the date shape
# its filenames carry.
AUDITS = "docs/audits"
DATED = re.compile(r"(\d{4}-\d{2}-\d{2})")

if not RELEASE:
    print("no release is in preparation; this check does not apply")
    raise SystemExit(3)

# An unreadable version and an exempt one both mean the comparison does
# not run. Reading them alike turns a typo in a version literal into a
# silent exemption, so refuse the version rather than skipping on it.
parsed = re.match(r"v?(\d+)\.(\d+)\.(\d+)$", RELEASE)
if parsed is None:
    print("release %r is not a version this check can read" % RELEASE)
    raise SystemExit(1)

major, minor, patch = (int(part) for part in parsed.groups())
if patch:
    print("%d.%d.%d is a patch release; the periodic review is not owed"
          % (major, minor, patch))
    raise SystemExit(3)

previous = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                          capture_output=True, text=True).stdout.strip()
released = subprocess.run(["git", "log", "-1", "--format=%cs", previous],
                          capture_output=True, text=True).stdout.strip()
names = os.listdir(AUDITS) if os.path.isdir(AUDITS) else []
dates = sorted(DATED.search(n).group(1) for n in names if DATED.search(n))

# Non-strict, per the currency rule above: a record dated the release day
# covers that release. Both counts are declared before any finding, so the
# check states what it read whichever verdict it reaches.
covering = [date for date in dates if date >= released]
print("audit records found: %d" % len(dates))
print("records covering %s, released %s: %d"
      % (previous, released, len(covering)))
if not dates:
    print("no audit record exists; this release owes one")
    raise SystemExit(1)
if not covering:
    print("newest record %s predates %s; this release owes one"
          % (dates[-1], released))
    raise SystemExit(1)
EOF
```

Pass condition: the command declares two counts — how many audit records
exist, and how many of them cover the previous release — and prints
nothing after them. Both MUST be non-zero. A record count of zero is a
failure rather than an empty tree, since a project reaching this check
runs the audit, so no record means none was written. A version the check
cannot read is a failure and never an exemption.

With the release left empty the command reports that the check does not
apply, on exit status 3.

### Projects with a version manifest
  9. `git checkout -b chore/release-vX.Y.Z`
  10. Bump version in the project manifest (`package.json`,
     `pyproject.toml`, `Cargo.toml`, or equivalent) to `X.Y.Z`, and
     where the project keeps a changelog, cut its `Unreleased` section
     into a dated `X.Y.Z` section in the same commit — the manifest
     version and the changelog heading name the same release, so they
     go stale together or not at all
  11. `git commit -m "chore: release vX.Y.Z"`
  12. Push, open PR, merge
  13. `git checkout main && git pull`
  14. `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
     — release tags MUST be annotated (`-a`/`-s`); a lightweight
     `git tag vX.Y.Z` is invisible to `git describe`, which reports
     a stale version to submodule/`describe` consumers
  15. SHOULD create a GitHub Release from the tag:
      `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`
      — a pushed tag alone does NOT create a Releases page entry.

### Post-release verification
  16. Verify the manifest version matches the tag — e.g.
      `grep '"version"' package.json` matches `git describe --tags`
  17. A mismatch means the bump was missed or the wrong commit was
      tagged — fix before announcing the release

### Projects without a version manifest (no-build)
  9. Where the project keeps a changelog, cut its `Unreleased` section
     into a dated `X.Y.Z` section and merge that through a pull request
     first. There is no version bump here to carry it, so the cut is
     the release commit — and the tag below MUST land on it or later,
     or the tagged tree holds a changelog that does not name its own
     release
  10. `git checkout main && git pull`
  11. `git tag -a vX.Y.Z -m "vX.Y.Z — <milestone name>"`
     — the `-a` is mandatory: a lightweight `git tag` is skipped by
     `git describe`, so consumers report a stale version. The annotated
     message is the artifact that carries the release theme
  12. `git push origin vX.Y.Z`
  13. Create a GitHub Release with auto-generated notes, titled with the
     bare version:
     `gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes`

The theme belongs to the tag message at step 11, and the release title is
the bare version. Both artifacts are generated from the same milestone at
cut time, so nothing is inconsistent on the day and the drift appears only
across releases: a list mixing themed and bare titles reads as two
conventions rather than one.

The theme is already recorded twice — in the tag message and in the
milestone description — so a themed title adds no record, and it spends
the one artifact that cannot be repaired cheaply. Re-cutting a published
release to change its title re-dates it, and a mis-ordered release list is
worse than an inconsistent one. A project that finds the drift late leaves
the published titles as they are and changes the procedure.

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

**The security-controls check** — step 5 of the migration sequence above,
a different sequence from the release one. Repository-level security
controls are per-repository and a new repository does not inherit them,
so a repository created to carry a clean history comes up with every
control off:

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

## Off-limits paths
- Some paths carry consequences a diff does not show. The change reads
  as ordinary and its blast radius is not local, so the usual signals —
  a small diff, a green suite — say nothing about it
- The project's context file MUST declare an **Off-limits** section
  listing paths that MUST NOT be modified without explicit approval. A
  restriction that lives only in a reviewer's head is not one
- Offer this as the default set and let the project cut it down: auth
  and session code, payment and billing code, database migrations,
  `.env*` and anything else handling secrets, CI/CD workflow
  definitions, and — where the project vendors its governing rules — the
  pointer to the submodule carrying them
- That last member earns its place differently from the others, so state
  why beside it. The rest are dangerous for what they execute or what
  they hold; a pointer executes nothing, so no linter, suite or gate
  reads it and the diff is a pair of hashes. One line replaces every rule
  the project binds, which is a wider blast radius than a workflow file,
  and a malformed workflow at least fails loudly
- A change inside an off-limits path MUST be proposed before it is
  made, and the proposal MUST carry a rollback strategy and the test
  coverage that would catch a regression. The approval is for that
  plan, not for the area
- A diff touching an off-limits path MUST say so at the top of its
  summary, naming the path. The reviewer's attention is the control,
  and it is only allocated if the summary spends it

The check, run from the repository root after committing and before
opening a pull request. Its subject is committed history, so a run
against staged but uncommitted work reports exactly what a compliant
branch reports. Keep `OFF_LIMITS` beside the declared list so the rule
and its check cannot drift apart:

```bash
py - <<'EOF'
import subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = "origin/main"

# Prefixes rather than patterns: a path holds no regex metacharacter to
# escape, so nothing can be lost on the way into the file.
OFF_LIMITS = [".github/workflows/", ".env", "migrations/"]

# This check's moment is a branch with commits on it. Run on the base
# itself the range is empty by construction, so the count below would
# print the shape of a failure for a question nobody asked.
here = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                      text=True, encoding="utf-8").stdout.strip()
there = subprocess.run(["git", "rev-parse", BASE], capture_output=True,
                       text=True, encoding="utf-8").stdout.strip()
if here == there:
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True,
                           encoding="utf-8").stdout.strip()
    if dirty:
        print("HEAD is at %s and the work is uncommitted; commit it and "
              "run again" % BASE)
        raise SystemExit(0)
    print("HEAD is at %s and the tree is clean; no branch is open, so "
          "this check does not apply" % BASE)
    raise SystemExit(3)

out = subprocess.run(["git", "diff", "--name-only", BASE + "...HEAD"],
                     capture_output=True, text=True,
                     encoding="utf-8").stdout
changed = [path for path in out.splitlines() if path]

print("files changed: %d" % len(changed))

for path in changed:
    for prefix in OFF_LIMITS:
        if path.startswith(prefix) or ("/" + prefix) in path:
            print("  off-limits: %s (matches %s)" % (path, prefix))
EOF
```

Pass condition: the command reports how many files it compared. Zero is
a failure rather than a clean branch, and the likeliest cause is that the
change is not committed yet — the natural moment to run a
pre-pull-request check is while writing it, and that run is guaranteed to
report nothing. The other cause is a wrong base. An unreached diff
reports the same nothing a clean one does.

The command separates those two from a third case that is not a failure
at all, and does it before counting. With HEAD at the base it asks
whether the tree is dirty: uncommitted work is the forgot-to-commit
failure above, and said in those words rather than as a zero; a clean
tree means no branch is open, so the check does not apply and exits 3.
The zero it would otherwise print carries the weight of a finding on a
tree where nothing is being proposed. Every
`off-limits:` line is an escalation trigger rather than a failure: it
says this change needs the proposal above before it merges.

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
