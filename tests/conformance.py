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
#             real answer. Anything printed after the declared lines is a
#             finding. A check's own pass condition mixes the two
#             directions, so a single rule for the whole head does not fit
#   silent    the check prints nothing at all
#   manual    the check runs and its output is reported, but no automatic
#             verdict is possible -- the operator reads it
#
# "grep": True marks a check whose last command is a grep. grep exits 1
# when it matches nothing, which is the CLEAN result, so the exit code
# carries no verdict.
SILENT = "silent"
MANUAL = "manual"

CHECKS = [

    # -- base/core/docs.md ------------------------------------------------

    {"file": "base/core/docs.md", "find": "community health files checked",
     "title": "Community health files resolve to one location each",
     "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "decision records inspected",
     "title": "ADR frontmatter schema", "do": RUN, "expect": ["nonzero"]},

    {"file": "base/core/docs.md", "find": "changelog entries measured",
     "title": "Changelog entries stay within the word bound",
     "do": RUN, "expect": MANUAL},

    {"file": "base/core/docs.md", "find": "entries, fenced = [], False",
     "title": "Development journal entry form", "do": RUN,
     "expect": MANUAL},

    {"file": "base/core/docs.md", "find": "width, source = None, None",
     "title": "Documentation line width matches the declared one",
     "do": RUN, "expect": MANUAL},

    {"file": "base/core/docs.md", "find": "(?:R|TD)[0-9]{2}",
     "title": "Risk and technical-debt identifiers stay in their owning doc",
     "do": RUN, "expect": MANUAL},

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
              "milestone", "do": RUN, "expect": MANUAL},

    {"file": "base/core/git.md", "find": "<release-workflow>.yml",
     "title": "The release pipeline has executed before", "do": SKIP,
     "reason": "Names the release workflow as a placeholder; run at release "
               "time with the real filename."},

    {"file": "base/core/git.md", "find": "ready but unmerged",
     "title": "Release ordering against other ready pull requests",
     "do": RUN, "expect": MANUAL},

    {"file": "base/core/git.md", "find": "entries in Unreleased",
     "title": "The Unreleased section accounts for what the release carries",
     "do": RUN, "expect": MANUAL},

    {"file": "base/core/git.md", "find": "<source-owner>/<source-repo>",
     "title": "A repository migration preserves both remotes", "do": SKIP,
     "reason": "Placeholder owner/repo pairs, run once during a migration."},

    {"file": "base/core/git.md", "find": "BASE = \"origin/main\"",
     "title": "Security controls survive a migration", "do": RUN,
     "expect": MANUAL},

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

    {"file": "base/core/quality.md", "find": "i/crlf\" { print }",
     "title": "No committed file carries CRLF", "do": RUN,
     "expect": SILENT},

    # -- base/core/review.md ----------------------------------------------

    {"file": "base/core/review.md", "find": "open pull requests inspected",
     "title": "An issue is not already in flight before work starts",
     "do": SKIP,
     "reason": "The jq filter carries `#<N>` for the issue being checked. "
               "Run per issue when picking up work, not against a tree."},

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

    # The rule states that this is governance rather than a pass/fail
    # metric: it decides review eligibility, not whether the build is
    # green. Reported, not scored -- and every template change owes a
    # disposition here, so scoring it would fail each one on arrival.
    {"file": "base/workflow/quality-gates.md",
     "find": "'tests/*'", "title": "A change to an existing test is visible",
     "do": RUN, "expect": MANUAL},

    {"file": "base/workflow/quality-gates.md",
     "find": "A shipped check is a heredoc inside a fenced block",
     "title": "A shipped rule states its check", "do": RUN,
     "expect": MANUAL},

    {"file": "base/workflow/quality-gates.md", "find": "blocks, risky = 0, []",
     "title": "A shipped check is safe to run where it is documented",
     "do": RUN, "expect": MANUAL},

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
     "do": RUN, "expect": MANUAL},

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
     "title": "Every name in __all__ imports", "do": SKIP,
     "reason": "This repository ships no importable package."},
]
