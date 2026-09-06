"""Dispositions for the checks the templates embed.

This repository is a consumer of its own base tier, so the checks the
templates prescribe apply here. Every runnable fenced block under
`templates/` MUST appear below exactly once. `run_conformance.py` fails on
a block with no entry, which is what stops a check added to a template from
arriving unexamined.

A block is located by a string only its body contains, never by position:
`base/core/git.md` alone holds ten of them, and selecting by index has
already found the wrong one.
"""

# Disposition values.
RUN = "run"
SKIP = "skip"

# Pass predicates, named here and implemented in the runner.
#
#   [...]     a list naming what each line the check declares must hold:
#             "nonzero" for a count that proves the check reached its
#             inputs, "zero" for a violation count, "any" where zero is a
#             real answer, "line" for a declared line carrying no count.
#             Anything printed after the declared lines is a finding. A
#             check's own pass condition mixes the two directions, so a
#             single rule for the whole head does not fit
#   READ      ends the scored run inside such a list: the lines from
#             there on are a reading for whoever the verdict's failure
#             summons, carried into the report and never scored. An
#             entry using it MUST carry "reading", saying which lines
#             those are and who they are for; the runner refuses one
#             that does not. It is how a check reaches a verdict on the
#             counts its pass condition decides without failing on the
#             lines it leaves to a person
#   silent    the check prints nothing at all
#   manual    the check runs and its output is reported, but no automatic
#             verdict is possible -- the operator reads it. A manual entry
#             MUST carry "reason", naming what about the check takes a
#             person; the runner refuses one that does not. A check whose
#             pass condition declares a threshold and counts against it
#             has a verdict available and is not manual
#
# "grep": True marks a check whose last command is a grep. grep exits 1
# when it matches nothing, which is the CLEAN result, so the exit code
# carries no verdict.
SILENT = "silent"
MANUAL = "manual"
READ = "read"

CHECKS = [

    # -- base/core/docs.md ------------------------------------------------

    {"file": "base/core/docs.md", "find": "community health files checked",
     "title": "Community health files resolve to one location each",
     "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "decision records inspected",
     "title": "ADR frontmatter schema", "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "changelog entries measured",
     "title": "Changelog entries stay within the word bound",
     "do": RUN, "expect": ["nonzero", "nonzero", "any", "zero"]},

    {"file": "base/core/docs.md", "find": "entries, fenced = [], False",
     "title": "Development journal entry form", "do": RUN,
     "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "width, source = None, None",
     "title": "Documentation line width matches the declared one",
     "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "ungated figures",
     "title": "A documentation figure comes from a generator",
     "do": RUN, "expect": ["nonzero", "zero"]},

    {"file": "base/core/docs.md", "find": "(?:R|TD)[0-9]{2}",
     "title": "Risk and technical-debt identifiers stay in their owning doc",
     "do": RUN, "expect": ["nonzero", "nonzero", "nonzero"]},

    # -- base/core/examples.md ---------------------------------------------

    {"file": "base/core/examples.md", "find": "example failed: $f",
     "title": "Every example runs against a consumer install", "do": SKIP,
     "reason": "Placeholder runner. This repository's `examples/` holds generated "
               "context files rather than executable programs, so there is nothing "
               "to execute."},

    # -- base/core/git.md -------------------------------------------------

    {"file": "base/core/git.md", "find": "<regenerate-command>",
     "title": "Regenerated artifact matches its sources", "do": SKIP,
     "reason": "The regeneration command is a placeholder the consuming "
               "project fills in. This repository's equivalent is "
               "`py tools/sync.py`, already gated in CI."},

    {"file": "base/core/git.md", "find": "mask() {",
     "title": "Volatile parts of a binary artifact are masked before diffing",
     "do": SKIP,
     "reason": "Needs the paths of two generated bundles to compare. This "
               "repository commits no binary artifact."},

    {"file": "base/core/git.md", "find": "PATHS = [\"<file>\"]",
     "title": "Numbered headings stay consistent across concurrent edits",
     "do": SKIP,
     "reason": "PATHS is a placeholder naming the documents two open "
               "branches both edit; it is set per release, not per repo."},

    {"file": "base/core/git.md", "find": "git diff --stat :3:<path>",
     "title": "A conflict resolution keeps both sides' content", "do": SKIP,
     "reason": "Runs only during an unresolved merge conflict, against the "
               "conflicting path."},

    {"file": "base/core/git.md",
     "find": "settings leaving no safe deletion path",
     "title": "A merged head branch has a safe deletion path", "do": RUN,
     "expect": ["nonzero", "zero"]},

    {"file": "base/core/git.md", "find": "MILESTONE",
     "title": "Every issue closed since the previous tag carries the "
              "milestone", "do": RUN, "expect": MANUAL,
     "reason": "Parameterised by MILESTONE, which is unset here, so the "
               "check reports that the release is not scoped to a "
               "milestone and does not apply."},

    {"file": "base/core/git.md", "find": "<release-workflow>.yml",
     "title": "The release pipeline has executed before", "do": SKIP,
     "reason": "Names the release workflow as a placeholder; run at release "
               "time with the real filename."},

    {"file": "base/core/git.md", "find": "ready but unmerged",
     "title": "Release ordering against other ready pull requests",
     "do": RUN, "expect": MANUAL,
     "reason": "Each pull request it lists as ready is a decision about "
               "which side of the tag the work lands on. The check states "
               "that is not a warning it can score."},

    {"file": "base/core/git.md", "find": "entries in Unreleased",
     "title": "The Unreleased section accounts for what the release carries",
     "do": RUN, "expect": MANUAL,
     "reason": "Parameterised by RELEASE, which is unset here, so the check "
               "reports that no release is in preparation and does not "
               "apply. With it set, the two counts are deliberately not "
               "required to match and the operator reconciles them."},

    {"file": "base/core/git.md", "find": "audit records found",
     "title": "A minor or major release carries a current periodic review",
     "do": RUN, "expect": ["nonzero", "nonzero"]},

    {"file": "base/core/git.md", "find": "<source-owner>/<source-repo>",
     "title": "A repository migration preserves both remotes", "do": SKIP,
     "reason": "Placeholder owner/repo pairs, run once during a migration."},

    {"file": "base/core/git.md", "find": "BASE = \"origin/main\"",
     "title": "A diff touching an off-limits path says so", "do": RUN,
     "expect": MANUAL,
     "reason": "The finding is whether the change SAYS SO about the path it "
               "touches, which is prose in a pull request body and not a "
               "count."},

    # -- base/core/quality.md ---------------------------------------------

    {"file": "base/core/quality.md", "find": "Identifiers only",
     "title": "Identifiers stay ASCII", "do": RUN, "expect": SILENT},

    {"file": "base/core/quality.md", "find": "aside to the right of code",
     "title": "Comment layout", "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/quality.md", "find": "SCRIPTS = pathlib.Path",
     "title": "The scripts directory carries the rules it owes", "do": SKIP,
     "reason": "This repository has no `scripts/` directory. Its permanent "
               "tooling lives in `tools/`, which the rule's own text scopes "
               "out. Re-examine if `scripts/` is ever added."},

    {"file": "base/core/quality.md",
     "find": "ya?ml|json|txt|toml|cfg|ini|sh|sql|css|js|ts",
     "title": "No committed text file carries CRLF", "do": RUN,
     "expect": SILENT},

    {"file": "base/core/quality.md", "find": "eol() { git ls-files --eol",
     "title": "The checkout carries the line ending the index does",
     "do": RUN, "expect": ["nonzero", "zero"]},

    # -- base/core/review.md ----------------------------------------------

    {"file": "base/core/review.md", "find": "open pull requests inspected",
     "title": "An issue is not already in flight before work starts",
     "do": SKIP,
     "reason": "The jq filter carries `#<N>` for the issue being checked. "
               "Run per issue when picking up work, not against a tree."},

    {"file": "base/core/review.md", "find": "pull requests linked to it",
     "title": "A sibling's shipped route, not the one it proposed",
     "do": SKIP,
     "reason": "Takes the sibling issue number as a placeholder. Run per "
               "issue when picking one up that defers to another, not "
               "against a tree."},

    {"file": "base/core/review.md", "find": "--since=<filing date>",
     "title": "A filed issue's claim is re-measured against the tree",
     "do": SKIP,
     "reason": "Takes the issue's filing date as an argument; run per issue "
               "during a groom, which the PLAYBOOK covers."},

    # -- base/core/testing.md ---------------------------------------------

    {"file": "base/core/testing.md", "find": "module-under-change",
     "title": "A remedy naming another check is re-read before narrowing it",
     "do": SKIP,
     "reason": "Takes the module whose scope is narrowing as an argument. "
               "It is run per change, not as a property of the tree."},

    {"file": "base/core/testing.md", "find": "guard-field-name",
     "title": "A guard field has a consumer, not only an assignment",
     "do": SKIP,
     "reason": "Takes the module under review and the guard field as "
               "arguments. It is run when one inert primitive is found, to "
               "sweep for its siblings, not as a property of the tree."},

    {"file": "base/core/testing.md", "find": "class ServerFixture",
     "title": "Fixture shape for a threaded server", "do": SKIP,
     "reason": "An illustration of the pattern, not a check. It has no pass "
               "condition and names a project's own server class."},

    {"file": "base/core/testing.md", "find": "type[(]self[)]",
     "title": "A class attribute is not mutated through the instance",
     "do": RUN, "expect": ["nonzero"], "grep": True},

    {"file": "base/core/testing.md", "find": "SERVER_THREAD_NAME",
     "title": "A test names its server thread", "do": SKIP,
     "reason": "An illustration of the naming pattern, not a check."},

    {"file": "base/core/testing.md", "find": "ssl.TLSVersion.TLSv1_2",
     "title": "A TLS floor is asserted, not assumed", "do": SKIP,
     "reason": "An illustration: an assertion a consuming project's own "
               "suite makes about its own context object."},

    {"file": "base/core/testing.md", "find": "pkg.__all__",
     "title": "Everything in __all__ is importable", "do": SKIP,
     "reason": "This repository ships no importable package. It applies to "
               "a library stack, where `stack/python-lib.md` carries it."},

    {"file": "base/core/testing.md", "find": "def fingerprint(path)",
     "title": "A mechanical move leaves the fingerprint unchanged",
     "do": SKIP,
     "reason": "Compares two revisions of a module named as arguments; run "
               "during a module split, not against a tree."},

    # -- base/language/python.md ------------------------------------------

    {"file": "base/language/python.md", "find": "pkg/_accel.py",
     "title": "An optional accelerator is isolated to one module",
     "do": SKIP,
     "reason": "An illustration of the module layout, not a check."},

    {"file": "base/language/python.md", "find": "_LOG.addHandler",
     "title": "A library core attaches a null handler",
     "do": SKIP,
     "reason": "An illustration of the module layout, not a check."},

    {"file": "base/language/python.md", "find": "the library attaches no handler",
     "title": "A plain import leaves the library's logger silent",
     "do": SKIP,
     "reason": "Imports a package named `pkg`. This repository ships no "
               "importable package."},

    # -- base/security/devsecops.md ---------------------------------------

    {"file": "base/security/devsecops.md", "find": "sbom.json",
     "title": "The SBOM lists the components the build produced",
     "do": SKIP,
     "reason": "Reads `sbom.json`, produced by a build this repository does "
               "not have -- it ships Markdown and has no dependency graph "
               "to describe."},

    # -- base/workflow/quality-gates.md -----------------------------------

    {"file": "base/workflow/quality-gates.md", "find": "SUPPRESSIONS = (",
     "title": "A suppression names the rule it suppresses", "do": RUN,
     "expect": ["nonzero", "any", "zero"]},

    {"file": "base/workflow/quality-gates.md",
     "find": "'tests/*'", "title": "A change to an existing test is visible",
     "do": RUN, "expect": MANUAL,
     "reason": "Governance rather than a pass/fail metric: it decides "
               "review eligibility, not whether the build is green. Every "
               "template change owes a disposition in this file, which is "
               "itself a test edit, so scoring it would fail each "
               "conforming change on arrival."},

    {"file": "base/workflow/quality-gates.md",
     "find": "A shipped check is a heredoc inside a fenced block",
     "title": "A shipped rule states its check", "do": RUN,
     "expect": ["nonzero", "nonzero", "zero"]},

    {"file": "base/workflow/quality-gates.md", "find": "CHECK_LANGUAGES = (",
     "title": "A shipped check is safe to run where it is documented",
     "do": RUN, "expect": ["nonzero", "nonzero", READ],
     "reading": "The continuation count and the lines under it. A non-zero "
                "count is not a failure -- it is the set to read against "
                "what was written, because the check cannot tell a "
                "continuation that is safe where it sits from one a reader "
                "would lose. The two counts above it are decided: its pass "
                "condition says zero on either is a failure, the first "
                "meaning the fence pattern drifted and the second the "
                "language filter."},

    {"file": "base/workflow/quality-gates.md",
     "find": "checks stated outside a fence",
     "title": "Every stated check is in a form a tool can extract",
     "do": RUN, "expect": ["nonzero", "zero"]},

    # -- base/workflow/scope.md -------------------------------------------

    {"file": "base/workflow/scope.md", "find": "platform/[a-z-]+[.]md",
     "title": "The context file names exactly one platform", "do": SKIP,
     "reason": "Reads a generated project's `CLAUDE.md` for its platform "
               "axis. This repository's `CLAUDE.md` is authored, not "
               "generated, and declares no platform template."},

    # -- base/workflow/two-pass-review.md ---------------------------------

    {"file": "base/workflow/two-pass-review.md", "find": "usage: scan <artifact>",
     "title": "First-pass mechanical scan of an artifact under review",
     "do": SKIP,
     "reason": "Takes the artifact to scan as an argument. It is a review "
               "aid run per artifact, not a property of the tree."},

    # -- platform/github.md -----------------------------------------------

    {"file": "platform/github.md", "find": "gh run list --commit",
     "title": "A commit's checks have started, not merely not failed",
     "do": RUN, "expect": ["line", "nonzero", READ],
     "reading": "The rows under the count, one per run that did not "
                "succeed. Whether a run still going is acceptable depends "
                "on what is being decided, so the rows go to whoever the "
                "count summons. The count itself is decided: its pass "
                "condition says a zero must be resolved either way, since "
                "the check cannot tell a malformed query from a workflow "
                "that never fired."},

    {"file": "platform/github.md", "find": "code-scanning/analyses",
     "title": "Code scanning is entitled before the workflow is committed",
     "do": SKIP,
     "reason": "Placeholder owner/repo, and it answers a question asked "
               "once when adding the workflow."},

    {"file": "platform/github.md", "find": "state,headRefOid",
     "title": "A branch is deleted only against the merged pull request",
     "do": SKIP, "reason": "Takes a pull request number as a placeholder."},

    {"file": "platform/github.md", "find": "refs/pull/<N>/head",
     "title": "A rewritten head is inspected rather than assumed",
     "do": SKIP, "reason": "Takes a pull request number as a placeholder."},

    {"file": "platform/github.md", "find": "TYPES = re.compile",
     "title": "Every open issue carries one type and one priority label",
     "do": RUN, "expect": ["nonzero"]},

    # -- stack/c-embedded.md ----------------------------------------------

    {"file": "stack/c-embedded.md", "find": "Configure (cross-compile",
     "title": "Build commands for the embedded stack", "do": SKIP,
     "reason": "A stack's Commands section, not a check."},

    # -- stack/python-lib.md ----------------------------------------------

    {"file": "stack/python-lib.md", "find": "pathlib.Path(\"dist\").glob",
     "title": "The built wheel contains what it should", "do": SKIP,
     "reason": "Inspects a wheel under `dist/`. This repository builds no "
               "distribution."},

    {"file": "stack/python-lib.md", "find": "from importlib import import_module",
     "title": "A deferred import binds its name on first access", "do": SKIP,
     "reason": "This repository ships no importable package. The block is "
               "the module `__getattr__` pattern itself; the check that "
               "every advertised name resolves is `base/core/testing.md`'s "
               "and carries its own entry."},

    {"file": "stack/python-lib.md", "find": "_RENAMED = {\"OldName\"",
     "title": "A renamed public symbol resolves through the deferred map",
     "do": SKIP,
     "reason": "This repository ships no importable package."},
]
