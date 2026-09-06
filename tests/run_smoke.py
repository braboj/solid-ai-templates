#!/usr/bin/env python3
"""
Smoke and integration test runner for solid-ai-templates structural checks.

Implements:
  SAIT-SMK-SYS-01-001A  — all DEPENDS ON paths resolve to existing files
  SAIT-SMK-SYS-02-001A  — all section IDs are unique across all templates
  SAIT-SMK-SYS-03-001A  — every template file has a manifest entry
  SAIT-SMK-SYS-04-001A  — DEPENDS ON headers match manifest depends_on
  SAIT-SMK-TPL-04-001A  — all EXTEND/OVERRIDE directives reference existing IDs
  SAIT-SMK-TPL-08-001A  — every base template has at least one [ID:] tag
  SAIT-SMK-TPL-09-001A  — no empty [ID:] sections
  SAIT-SMK-ADR-01-001A  — ADR frontmatter matches the ADR-010 schema
  SAIT-INT-TPL-06-001A  — EXTEND/OVERRIDE targets reachable in resolved chain
  SAIT-INT-MNF-01-001A  — all manifest entries reference valid paths and IDs

Usage:
  py tests/run_smoke.py              # run all checks
  py tests/run_smoke.py SYS-01       # run one check by short ID
  py tests/run_smoke.py SYS-01 MNF-01
"""

import datetime
import io
import os
import re
import subprocess
import sys

from lib import (ROOT, PASS, FAIL, ERR, write_report,
                 repository_files, template_files)
from cases import ALL_TESTS

# Set the output encoding at the boundary rather than inheriting the
# console default, which mangles any non-ASCII this program prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# The one failure a check returns when the manifest cannot be read at all.
# It is a constant rather than fourteen copies of a string so the runner's
# preflight can recognise it, instead of keeping a second list of which
# checks need the dependency.
MISSING_YAML = "  PyYAML not installed — run: pip install pyyaml"


# ---------------------------------------------------------------------------
# [ID: ...] declaration matching
# ---------------------------------------------------------------------------
# An [ID: foo] tag is a declaration only when it is the entire content of
# its line (whitespace-only surroundings allowed). Inline occurrences in
# prose, code blocks, or table cells are references and MUST NOT count as
# declarations — otherwise referencing another template's ID in prose
# would trip duplicate-detection (SYS-02).

_DECL_LINE = re.compile(r'^\s*\[ID:\s*([^\]]+)\]\s*$')


def iter_id_declarations(content):
    """Yield (section_id, line_number) for each [ID:] declaration line."""
    for i, line in enumerate(content.splitlines(), start=1):
        m = _DECL_LINE.match(line)
        if m:
            yield m.group(1).strip(), i


# ---------------------------------------------------------------------------
# Manifest resolution helpers (shared by MNF-02, MNF-03, MNF-04)
# ---------------------------------------------------------------------------

def _load_manifest():
    """Load manifest.yaml and return (core_ids, entries, file_to_id)."""
    manifest_path = os.path.join(ROOT, "templates", "manifest.yaml")
    with io.open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    entries = {}
    for section in ("base", "platform", "frontend", "backend", "stacks"):
        for entry in data.get(section, []):
            entries[entry["id"]] = entry

    file_to_id = {e["file"]: e["id"] for e in entries.values()}
    return data.get("core", []), entries, file_to_id


def _resolve_stack(stack_id, core_ids, entries):
    """Resolve full dependency chain for a stack.

    Returns (ordered_files, resolved_ids).
    """
    resolved = set()
    files = []

    def add(eid):
        if eid in resolved:
            return
        resolved.add(eid)
        entry = entries.get(eid)
        if entry:
            files.append(entry["file"])

    def resolve(eid):
        if eid in resolved:
            return
        entry = entries.get(eid)
        if not entry:
            return
        for dep in entry.get("depends_on", []):
            resolve(dep)
        add(eid)

    for cid in core_ids:
        add(cid)

    resolve(stack_id)
    return files, resolved


def _opt_in_roots(core_ids, entries):
    """The manifest IDs a project picks directly, that no stack chain carries.

    A project resolves its stack, then its extras, then its platform, each as
    its own root -- the algorithm ADR-004 states and `tools/resolve.py`
    implements. An opt-in template is therefore guaranteed only the core tier
    plus its own dependency tree, so a directive or a prose reference it
    carries has to resolve there, not in a stack chain it may never be paired
    with. Resolving stacks alone leaves these roots unexamined, and a check
    that examines nothing reports the same result as a clean tree.
    """
    reached = set()
    for entry in entries.values():
        if entry["file"].startswith("templates/stack/"):
            _, ids = _resolve_stack(entry["id"], core_ids, entries)
            reached |= ids
    return sorted(set(entries) - reached)


def _roots_by_kind(core_ids, entries):
    """The two kinds of root a project picks, returned apart.

    A check covering both kinds reports each count rather than their sum.
    One number cannot tell a tree where every root resolved from a
    resolver that stopped enumerating one kind: 37 reads the same whether
    it is 17 and 20 or 37 and 0. Two numbers move independently, so the
    kind that empties takes its own count to zero where a reader sees it.
    """
    stacks = sorted(e["id"] for e in entries.values()
                    if e["file"].startswith("templates/stack/"))
    return stacks, _opt_in_roots(core_ids, entries)


# The directories the template corpus is expected to fill. The corpus itself
# comes from git; this list exists so a renamed or emptied directory is a
# finding rather than a corpus that quietly shrinks.
TEMPLATE_DIRS = [
    "templates/base/core",
    "templates/base/security",
    "templates/base/infra",
    "templates/base/workflow",
    "templates/base/language",
    "templates/base/data",
    "templates/backend",
    "templates/frontend",
    "templates/platform",
    "templates/stack",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def all_template_files():
    """Absolute paths to every template the manifest governs.

    Sourced from git rather than from a walk of TEMPLATE_DIRS. A hardcoded
    directory list defines what the checks reading it can see: a template
    outside the list is invisible to all of them, and the corpus count they
    print cannot move to say so -- a stale count and a correct one read
    alike when the enumerator never looked.
    """
    return [os.path.join(ROOT, p.replace("/", os.sep))
            for p in template_files()]


def missing_template_dirs():
    """Expected directories that contribute no file to the corpus.

    A directory that is not there is a finding, not a skip. Skipping it
    makes a rename silent: every listed directory disappears and the check
    reports the same pass as a clean tree.
    """
    present = template_files()
    return [d for d in TEMPLATE_DIRS
            if not any(p.startswith(d + "/") for p in present)]


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


class Inspected:
    """The inputs a check reached, reported whatever its verdict.

    A check that reports only what it found reads identically when its
    corpus empties and when the tree is clean, so a corpus that quietly
    goes to zero keeps reporting green -- the suite's count of passing
    checks stops meaning what a reader takes it to mean. Every count is
    reported on every run, and a count below its floor is a failure: the
    check answered a question it never asked.
    """

    def __init__(self):
        self._counts = []

    def count(self, label, value, floor=1):
        """Record an input count and return the value it was taken from.

        `value` may be a number or anything with a length, so a call can
        wrap the collection a check is about to iterate.
        """
        n = value if isinstance(value, int) else len(value)
        self._counts.append((label, n, floor))
        return value

    def notes(self):
        return [f"  {label}: {n}" for label, n, _ in self._counts]

    def failures(self):
        return [
            f"  {label}: {n} — below the floor of {floor}; the check reached "
            f"nothing and an empty corpus reports the same result as a clean "
            f"tree"
            for label, n, floor in self._counts if n < floor
        ]


# ---------------------------------------------------------------------------
# DEPENDS ON extraction
# ---------------------------------------------------------------------------
# A DEPENDS ON declaration is only meaningful in the file header, and every
# one in the tree sits on line 2, 3 or 4 -- before the first section heading,
# measured across all template files. Consumer-facing sections legitimately
# quote the directive syntax to explain the composition model, so extracting
# it from the whole file reads that prose as a declaration and fails against
# a file that does not exist, naming a path nobody wrote.

HEADER_END_RE = re.compile(r"^## ")
DEPENDS_RE = re.compile(r"\[DEPENDS ON:\s*([^\]]+)\]")


def depends_on_refs(content):
    """Return the paths declared by the header's DEPENDS ON directive."""
    refs = []
    for line in content.splitlines():
        if HEADER_END_RE.match(line):
            break
        for match in DEPENDS_RE.finditer(line):
            refs.extend(ref.strip() for ref in match.group(1).split(","))
    return refs


# ---------------------------------------------------------------------------
# SYS-01 — DEPENDS ON paths resolve to existing files
# ---------------------------------------------------------------------------

def check_sys_01():
    failures = []
    seen = Inspected()
    refs_checked = 0

    files = seen.count("template files scanned", all_template_files())
    for filepath in files:
        for ref in depends_on_refs(read(filepath)):
            refs_checked += 1
            ref_path = os.path.join(ROOT, ref)
            if not os.path.isfile(ref_path):
                rel = os.path.relpath(filepath, ROOT)
                failures.append(f"  {rel}: DEPENDS ON '{ref}' — file not found")

    seen.count("DEPENDS ON references resolved", refs_checked)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-02 — all section IDs unique across all templates
# ---------------------------------------------------------------------------

def check_sys_02():
    failures = []
    seen = {}
    inspected = Inspected()

    files = inspected.count("template files scanned", all_template_files())
    for filepath in files:
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT)
        for sid, _ in iter_id_declarations(content):
            if sid in seen:
                failures.append(
                    f"  Duplicate ID '{sid}': "
                    f"{seen[sid]} and {rel}"
                )
            else:
                seen[sid] = rel

    inspected.count("section IDs collected", len(seen))
    return inspected.failures() + failures, inspected.notes()


# ---------------------------------------------------------------------------
# TPL-04 — all EXTEND/OVERRIDE refs point to existing IDs
# ---------------------------------------------------------------------------

def check_tpl_04():
    failures = []
    seen = Inspected()
    ref_pattern = re.compile(r'\[(EXTEND|OVERRIDE):\s*([^\]]+)\]')

    declared = set()
    files = seen.count("template files scanned", all_template_files())
    for filepath in files:
        content = read(filepath)
        for sid, _ in iter_id_declarations(content):
            declared.add(sid)
    seen.count("section IDs declared", len(declared))

    directives = 0
    for filepath in files:
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT)
        for match in ref_pattern.finditer(content):
            directives += 1
            directive = match.group(1)
            ref_id = match.group(2).strip()
            if ref_id not in declared:
                failures.append(
                    f"  {rel}: [{directive}: {ref_id}] — ID not declared"
                )

    seen.count("EXTEND/OVERRIDE directives checked", directives)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# MNF-01 — manifest entries reference valid paths and IDs
# ---------------------------------------------------------------------------

def check_mnf_01():
    if not HAS_YAML:
        return [MISSING_YAML]

    manifest_path = os.path.join(ROOT, "templates", "manifest.yaml")
    if not os.path.isfile(manifest_path):
        return ["  manifest.yaml not found"]

    with io.open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    failures = []
    seen = Inspected()
    declared_ids = set()
    entries = []

    for section in manifest.values():
        if isinstance(section, list):
            for entry in section:
                if isinstance(entry, dict):
                    entries.append(entry)
                    if "id" in entry:
                        declared_ids.add(entry["id"])

    seen.count("manifest entries read", len(entries))
    seen.count("IDs declared in the manifest", len(declared_ids))

    for entry in entries:
        path = entry.get("file", "")
        if path and not os.path.isfile(os.path.join(ROOT, path)):
            failures.append(f"  file not found: '{path}' (id: {entry.get('id', '?')})")

    deps_checked = 0
    for entry in entries:
        for dep in entry.get("depends_on", []):
            deps_checked += 1
            if dep not in declared_ids:
                failures.append(
                    f"  depends_on '{dep}' in '{entry.get('id', '?')}' "
                    f"— ID not declared in manifest"
                )

    seen.count("depends_on references checked", deps_checked)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-01 — DEPENDS ON chain from python-fastapi.md is complete
# ---------------------------------------------------------------------------

def _collect_chain(rel_path, visited=None):
    if visited is None:
        visited = set()
    if rel_path in visited:
        return visited
    visited.add(rel_path)
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.isfile(abs_path):
        return visited
    for dep in depends_on_refs(read(abs_path)):
        _collect_chain(dep, visited)
    return visited


def check_tpl_01():
    failures = []
    chain = _collect_chain("templates/stack/python-fastapi.md")
    required = [
        "templates/stack/python-lib.md",
        "templates/stack/python-service.md",
        "templates/base/core/git.md",
        "templates/base/core/docs.md",
        "templates/base/core/quality.md",
        "templates/base/core/config.md",
        "templates/backend/http.md",
        "templates/backend/database.md",
        "templates/backend/observability.md",
        "templates/backend/quality.md",
        "templates/backend/features.md",
        "templates/backend/messaging.md",
    ]
    seen = Inspected()
    seen.count("files in the python-fastapi chain", len(chain))
    seen.count("files required to be in it", len(required))

    for req in required:
        if req not in chain:
            failures.append(f"  python-fastapi.md chain missing: '{req}'")
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-02 — EXTEND adds rules without removing base rules
# ---------------------------------------------------------------------------

def _extract_section(filepath, section_id):
    content = read(filepath)
    lines = content.splitlines()
    result = []
    in_section = False
    tag = f"[ID: {section_id}]"
    extend_tag = f"[EXTEND: {section_id}]"
    override_tag = f"[OVERRIDE: {section_id}]"

    for i, line in enumerate(lines):
        if tag in line or extend_tag in line or override_tag in line:
            in_section = True
            continue
        if in_section:
            has_content = any(l.strip() for l in result)
            if re.match(r'^#{1,4} ', line) and has_content:
                break
            if re.match(r'^\[(ID|EXTEND|OVERRIDE|DEPENDS):', line) and has_content:
                break
            result.append(line)

    return [l for l in result if l.strip()]


def check_tpl_02():
    failures = []
    seen = Inspected()

    base_content = _extract_section(
        os.path.join(ROOT, "templates", "base", "core", "testing.md"), "base-testing"
    )
    if not base_content:
        failures.append("  base/core/testing.md [ID: base-testing] section is empty")

    flask_content = _extract_section(
        os.path.join(ROOT, "templates", "stack", "python-flask.md"), "python-service-testing"
    )
    if not flask_content:
        failures.append(
            "  stack/python-flask.md [EXTEND: python-service-testing] section is empty "
            "— base rules may have been lost"
        )

    seen.count("sections extracted", 2)
    seen.count("lines read from base-testing", len(base_content), floor=0)
    seen.count("lines read from python-service-testing",
               len(flask_content), floor=0)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-03 — OVERRIDE replaces parent section entirely
# ---------------------------------------------------------------------------

def check_tpl_03():
    failures = []
    seen = Inspected()

    original = _extract_section(
        os.path.join(ROOT, "templates", "stack", "go-lib.md"), "go-lib-stack"
    )
    override = _extract_section(
        os.path.join(ROOT, "templates", "stack", "go-service.md"), "go-lib-stack"
    )

    if not original:
        failures.append("  stack/go-lib.md [ID: go-lib-stack] section is empty")
    if not override:
        failures.append(
            "  stack/go-service.md [OVERRIDE: go-lib-stack] section is empty"
        )
    if original and override and original == override:
        failures.append(
            "  [OVERRIDE: go-lib-stack] content is identical to the original "
            "[ID: go-lib-stack] — override has no effect"
        )

    seen.count("sections extracted", 2)
    seen.count("lines read from the original", len(original), floor=0)
    seen.count("lines read from the override", len(override), floor=0)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# MNF-02 — all stacks resolve to valid, non-empty file lists
# ---------------------------------------------------------------------------

def check_mnf_02():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    failures = []
    seen = Inspected()

    stacks = seen.count("stacks resolved", [e for e in entries.values()
                        if e["file"].startswith("templates/stack/")])

    resolved = 0
    for stack in stacks:
        sid = stack["id"]
        files, _ = _resolve_stack(sid, core_ids, entries)

        if not files:
            failures.append(f"  {sid}: resolution produced empty file list")
            continue

        for f in files:
            resolved += 1
            path = os.path.join(ROOT, f)
            if not os.path.isfile(path):
                failures.append(f"  {sid}: resolved file missing: {f}")
            elif os.path.getsize(path) == 0:
                failures.append(f"  {sid}: resolved file empty: {f}")

    seen.count("resolved files inspected", resolved)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# MNF-03 — all resolved chains include core tier files
# ---------------------------------------------------------------------------

def check_mnf_03():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    failures = []
    seen = Inspected()

    stacks = seen.count("stacks resolved", [e for e in entries.values()
                        if e["file"].startswith("templates/stack/")])
    seen.count("core tier IDs required of each", len(core_ids))

    for stack in stacks:
        sid = stack["id"]
        _, resolved_ids = _resolve_stack(sid, core_ids, entries)

        for cid in core_ids:
            if cid not in resolved_ids:
                failures.append(
                    f"  {sid}: core ID '{cid}' missing from "
                    f"resolved chain"
                )

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# MNF-04 — prompt builds for all stacks
# ---------------------------------------------------------------------------

def check_mnf_04():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    failures = []

    output_file = "templates/base/core/agents.md"
    output_path = os.path.join(ROOT, output_file)
    if not os.path.isfile(output_path):
        return [f"  output format missing: {output_file}"]

    output_fmt = read(output_path)
    seen = Inspected()

    stacks = seen.count("stacks resolved", [e for e in entries.values()
                        if e["file"].startswith("templates/stack/")])

    built = 0
    for stack in stacks:
        sid = stack["id"]
        files, _ = _resolve_stack(sid, core_ids, entries)

        try:
            parts = []
            for f in files:
                parts.append(read(os.path.join(ROOT, f)))
            prompt = "\n\n".join(parts) + "\n\n" + output_fmt
        except Exception as e:
            failures.append(f"  {sid}: prompt build failed: {e}")
            continue

        if len(prompt) < 500:
            failures.append(
                f"  {sid}: prompt suspiciously short "
                f"({len(prompt)} chars)"
            )
        built += 1

    seen.count("prompts built", built)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# MNF-05 — resolve.py resolution matches the PyYAML resolution
# ---------------------------------------------------------------------------
# The user-facing tools/resolve.py uses a stdlib-only hand-rolled manifest
# parser; smoke (and the manifest's own semantics) use PyYAML. A divergence
# between the two — e.g. the multi-line depends_on bug, #654 — ships a wrong
# generated/ chain that `resolve.py --check` cannot catch, since it only
# verifies self-consistency against the same parser. This gate resolves every
# stack with BOTH parsers and fails on any mismatch, so the two can never
# silently drift again regardless of which parser is edited next.

def check_mnf_05():
    if not HAS_YAML:
        return [MISSING_YAML]

    tools_dir = os.path.join(ROOT, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import resolve as resolve_tool
    except Exception as e:
        return [f"  cannot import tools/resolve.py: {e}"]

    core_h, entries_h, stacks = resolve_tool.load_manifest()
    core_y, entries_y, _ = _load_manifest()

    failures = []
    seen = Inspected()
    stacks = seen.count("stacks resolved with both parsers", stacks)
    for stack in stacks:
        sid = stack["id"]
        hand = resolve_tool.resolve_chain(sid, core_h, entries_h)
        ref, _ = _resolve_stack(sid, core_y, entries_y)
        if hand == ref:
            continue
        missing = [f for f in ref if f not in hand]
        extra = [f for f in hand if f not in ref]
        parts = []
        if missing:
            parts.append(f"missing from resolve.py: {', '.join(missing)}")
        if extra:
            parts.append(f"extra in resolve.py: {', '.join(extra)}")
        if not parts:
            parts.append("same files, different order")
        failures.append(
            f"  {sid}: resolve.py chain != PyYAML chain — "
            f"{'; '.join(parts)}"
        )

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-06 — EXTEND/OVERRIDE targets reachable in resolved chain
# ---------------------------------------------------------------------------

def check_tpl_06():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    ref_pattern = re.compile(r'\[(EXTEND|OVERRIDE):\s*([^\]]+)\]')
    failures = []
    seen = Inspected()

    stacks = seen.count("stacks resolved", [e["id"] for e in entries.values()
                        if e["file"].startswith("templates/stack/")])

    # A stack is not the only root a project resolves. Extras and the platform
    # are chosen independently of the stack, so what guarantees their EXTEND
    # target is their own chain -- the core tier plus their dependency tree --
    # and not whichever stack they are paired with. Resolving stacks alone
    # left every opt-in template unexamined, which is how two platform files
    # came to extend a section carried by one chain in seventeen.
    opt_in = seen.count("opt-in roots resolved",
                        _opt_in_roots(core_ids, entries))

    directives = 0
    for sid in list(stacks) + list(opt_in):
        chain_files, _ = _resolve_stack(sid, core_ids, entries)

        # Collect all IDs declared in chain files
        chain_ids = set()
        for f in chain_files:
            content = read(os.path.join(ROOT, f))
            for chain_sid, _ in iter_id_declarations(content):
                chain_ids.add(chain_sid)

        # Check EXTEND/OVERRIDE targets in chain files
        for f in chain_files:
            content = read(os.path.join(ROOT, f))
            rel = f.replace("\\", "/")
            for match in ref_pattern.finditer(content):
                directives += 1
                directive = match.group(1)
                ref_id = match.group(2).strip()
                if ref_id not in chain_ids:
                    failures.append(
                        f"  {sid}: {rel} [{directive}: {ref_id}]"
                        f" — target not in resolved chain"
                    )

    seen.count("directives checked in a resolved chain", directives)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-07 — EXTEND sections do not duplicate parent rules
# ---------------------------------------------------------------------------

def _extract_bullets(filepath, section_id):
    """Return list of bullet-point texts from the section tagged with ID."""
    content = read(filepath)
    lines = content.splitlines()
    bullets = []
    in_section = False
    tag = f"[ID: {section_id}]"

    for line in lines:
        if tag in line:
            in_section = True
            continue
        if in_section:
            if re.match(r'^#{1,4} ', line) and bullets:
                break
            if re.match(r'^\[(ID|EXTEND|OVERRIDE|DEPENDS):', line) and bullets:
                break
            stripped = line.strip()
            if stripped.startswith('- '):
                bullets.append(stripped[2:].strip())

    return bullets


def _word_set(text):
    """Return set of lowercase words (3+ chars) from text."""
    return {w.lower() for w in re.findall(r'[a-zA-Z]{3,}', text)}


def check_tpl_07():
    if not HAS_YAML:
        return [MISSING_YAML]

    extend_pattern = re.compile(r'^\[EXTEND:\s*([^\]]+)\]', re.MULTILINE)
    failures = []
    seen = Inspected()

    # Build ID → file map
    id_to_file = {}
    files = seen.count("template files scanned", all_template_files())
    for filepath in files:
        content = read(filepath)
        for sid, _ in iter_id_declarations(content):
            id_to_file[sid] = filepath

    # For each EXTEND, compare child bullets against parent bullets
    compared = 0
    for filepath in files:
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT).replace("\\", "/")
        for match in extend_pattern.finditer(content):
            parent_id = match.group(1).strip()
            parent_file = id_to_file.get(parent_id)
            if not parent_file:
                continue

            parent_bullets = _extract_bullets(parent_file, parent_id)
            if not parent_bullets:
                continue
            compared += 1

            # Find the child section that contains this EXTEND
            child_lines = content.splitlines()
            extend_line = match.start()
            char_count = 0
            extend_lineno = 0
            for i, line in enumerate(child_lines):
                char_count += len(line) + 1
                if char_count > extend_line:
                    extend_lineno = i
                    break

            # Collect child bullets after the EXTEND line
            child_bullets = []
            for line in child_lines[extend_lineno + 1:]:
                if re.match(r'^#{1,4} ', line) and child_bullets:
                    break
                if re.match(r'^\[(ID|EXTEND|OVERRIDE|DEPENDS):', line):
                    break
                stripped = line.strip()
                if stripped.startswith('- '):
                    child_bullets.append(stripped[2:].strip())

            # Compare each child bullet against parent bullets
            for cb in child_bullets:
                cb_words = _word_set(cb)
                if len(cb_words) < 3:
                    continue
                for pb in parent_bullets:
                    pb_words = _word_set(pb)
                    if len(pb_words) < 3:
                        continue
                    intersection = cb_words & pb_words
                    union = cb_words | pb_words
                    if union and len(intersection) / len(union) >= 0.7:
                        failures.append(
                            f"  {rel} [EXTEND: {parent_id}]: "
                            f"possible duplicate — \"{cb[:60]}...\""
                        )
                        break

    seen.count("EXTEND sections compared against a parent", compared)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-03 — every template file has a manifest entry
# ---------------------------------------------------------------------------

def check_sys_03():
    if not HAS_YAML:
        return [MISSING_YAML]

    manifest_path = os.path.join(ROOT, "templates", "manifest.yaml")
    with io.open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    manifest_files = set()
    for section in ("core", "base", "platform", "frontend",
                    "backend", "stacks"):
        for entry in manifest.get(section, []):
            if isinstance(entry, dict) and "file" in entry:
                manifest_files.add(
                    entry["file"].replace("/", os.sep)
                )

    failures = []
    seen = Inspected()
    seen.count("files named in the manifest", len(manifest_files))

    files = seen.count("template files scanned", all_template_files())

    # The corpus comes from git, so an emptied or renamed directory shrinks
    # it silently. Naming the expected directories makes that a finding.
    for d in missing_template_dirs():
        failures.append(
            f"  {d}: expected template directory holds no tracked "
            f"template — the corpus lost a directory it is built to cover"
        )

    for filepath in files:
        rel = os.path.relpath(filepath, ROOT)
        rel_fwd = rel.replace(os.sep, "/")
        if rel_fwd not in {f.replace(os.sep, "/") for f in manifest_files}:
            failures.append(f"  {rel_fwd}: no manifest entry")

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-04 — DEPENDS ON headers match manifest depends_on
# ---------------------------------------------------------------------------

def check_sys_04():
    if not HAS_YAML:
        return [MISSING_YAML]

    manifest_path = os.path.join(ROOT, "templates", "manifest.yaml")
    with io.open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    # Build id→file and file→depends_on(as files) maps
    id_to_file = {}
    for section in ("core", "base", "platform", "frontend",
                    "backend", "stacks"):
        for entry in manifest.get(section, []):
            if isinstance(entry, dict):
                id_to_file[entry["id"]] = entry["file"]

    file_manifest_deps = {}
    for section in ("base", "platform", "frontend",
                    "backend", "stacks"):
        for entry in manifest.get(section, []):
            if isinstance(entry, dict):
                dep_files = set()
                for dep_id in entry.get("depends_on", []):
                    dep_file = id_to_file.get(dep_id)
                    if dep_file:
                        dep_files.add(dep_file)
                file_manifest_deps[entry["file"]] = dep_files

    failures = []
    seen = Inspected()
    seen.count("manifest entries carrying depends_on", len(file_manifest_deps))

    files = seen.count("template files compared", all_template_files())
    for filepath in files:
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        content = read(filepath)

        # Collect file paths from DEPENDS ON headers
        header_files = set(depends_on_refs(content))

        manifest_deps = file_manifest_deps.get(rel, set())

        # Only flag if at least one side is non-empty
        if header_files == manifest_deps:
            continue

        only_header = sorted(header_files - manifest_deps)
        only_manifest = sorted(manifest_deps - header_files)

        parts = []
        if only_header:
            parts.append(f"header only: {', '.join(only_header)}")
        if only_manifest:
            parts.append(f"manifest only: {', '.join(only_manifest)}")
        if parts:
            failures.append(f"  {rel}: {'; '.join(parts)}")

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-08 — every base/core template has at least one [ID:] tag
# ---------------------------------------------------------------------------

# The base tier the check is pointed at. Its files come from git, so a
# template added in a new base subdirectory is inspected without this list
# being edited; the list survives to make an emptied directory a finding.
BASE_PREFIX = "templates/base/"

CORE_DIRS = [
    "templates/base/core",
    "templates/base/security",
    "templates/base/infra",
    "templates/base/workflow",
    "templates/base/language",
    "templates/base/data",
]


def check_tpl_08():
    failures = []
    seen = Inspected()
    seen.count("directories the check is pointed at", len(CORE_DIRS))

    base_files = seen.count("files inspected for an [ID:] tag",
                            template_files(BASE_PREFIX))

    # A directory that is not there is a finding, not a skip. Skipping it
    # makes a rename silent: every listed directory disappears and the
    # check reports the same pass as a clean tree.
    for d in CORE_DIRS:
        if not any(rel.startswith(d + "/") for rel in base_files):
            failures.append(
                f"  {d}: listed directory holds no template — the check "
                f"inspects nothing in it"
            )

    for rel in base_files:
        content = read(os.path.join(ROOT, rel.replace("/", os.sep)))
        if not any(True for _ in iter_id_declarations(content)):
            failures.append(f"  {rel}: missing [ID:] tag")

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# TPL-09 — no empty [ID:] sections
# ---------------------------------------------------------------------------

def check_tpl_09():
    failures = []
    seen = Inspected()
    meta_pattern = re.compile(r'^\[(DEPENDS ON|EXTEND|OVERRIDE):')
    next_id_pattern = re.compile(r'^\s*\[ID:')

    sections = 0
    for filepath in seen.count("template files scanned",
                               all_template_files()):
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        lines = content.splitlines()

        # Map declaration line numbers → section IDs (sole-line only).
        decls = {lineno: sid for sid, lineno in iter_id_declarations(content)}

        for i, line in enumerate(lines):
            section_id = decls.get(i + 1)
            if not section_id:
                continue
            sections += 1

            # Check for any non-blank content before the next [ID:]
            # tag. Skip metadata lines ([DEPENDS ON:], [EXTEND:],
            # [OVERRIDE:]) that accompany this section's [ID:].
            # Sub-headings count as content.
            has_content = False
            for subsequent in lines[i + 1:]:
                stripped = subsequent.strip()
                if not stripped:
                    continue
                if next_id_pattern.match(stripped):
                    break
                if meta_pattern.match(stripped):
                    continue
                has_content = True
                break

            if not has_content:
                failures.append(
                    f"  {rel}: [ID: {section_id}] section is empty"
                )

    seen.count("[ID:] sections inspected", sections)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# ADR-01 — ADR frontmatter schema enforcement
# ---------------------------------------------------------------------------
# Enforces the schema defined in docs/decisions/010-adr-governance.md:
# - frontmatter present and parses as YAML
# - id is 3-digit string matching filename leading digits
# - status in closed set: Proposed | Accepted | Superseded
# - date present in YYYY-MM-DD form
# - category in closed set
# - supersedes / superseded_by present (empty list allowed)
# - reciprocal-link consistency
# - status=Superseded iff superseded_by non-empty

ADR_STATUSES = {"Proposed", "Accepted", "Superseded"}
ADR_CATEGORIES = {"composition", "templates", "tooling", "process", "release"}
ADR_FILENAME = re.compile(r"^(\d{3})-[a-z0-9-]+\.md$")
ADR_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADR_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def _parse_adr(filepath, content):
    """Return (frontmatter dict, list of failures) for a single ADR file."""
    rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
    fm_match = ADR_FRONTMATTER.match(content)
    if not fm_match:
        return None, [f"  {rel}: missing YAML frontmatter block"]
    try:
        data = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as e:
        return None, [f"  {rel}: frontmatter is not valid YAML ({e})"]
    if not isinstance(data, dict):
        return None, [f"  {rel}: frontmatter did not parse as a mapping"]
    return data, []


def check_adr_01():
    if not HAS_YAML:
        return [MISSING_YAML]

    failures = []
    seen = Inspected()
    decisions_dir = os.path.join(ROOT, "docs", "decisions")
    if not os.path.isdir(decisions_dir):
        return ["  docs/decisions/ does not exist — the check inspects nothing"]

    # id (str) -> (rel_path, frontmatter dict)
    parsed = {}

    numbered = 0
    for name in sorted(os.listdir(decisions_dir)):
        m = ADR_FILENAME.match(name)
        if not m:
            # TEMPLATE.md and any non-numbered files are skipped
            continue
        numbered += 1
        filepath = os.path.join(decisions_dir, name)
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        content = read(filepath)

        data, errs = _parse_adr(filepath, content)
        failures.extend(errs)
        if data is None:
            continue

        expected_id = m.group(1)
        adr_id = data.get("id")

        # id MUST be a quoted string in the YAML — otherwise leading-zero
        # values (010) are parsed by YAML 1.1 as octal integers (010 -> 8).
        # Detect this case explicitly so the error message points at the
        # quoting fix, not a confusing numeric mismatch.
        if not isinstance(adr_id, str):
            failures.append(
                f"  {rel}: id {adr_id!r} is not a string — quote it as "
                f"\"{expected_id}\" to avoid YAML octal parsing"
            )
        elif adr_id != expected_id:
            failures.append(
                f"  {rel}: id {adr_id!r} does not match filename leading "
                f"digits ({expected_id})"
            )

        status = data.get("status")
        if status not in ADR_STATUSES:
            failures.append(
                f"  {rel}: status {status!r} not in {sorted(ADR_STATUSES)}"
            )

        date = str(data.get("date") or "")
        if not ADR_DATE.match(date):
            failures.append(
                f"  {rel}: date {data.get('date')!r} is not YYYY-MM-DD"
            )

        category = data.get("category")
        if category not in ADR_CATEGORIES:
            failures.append(
                f"  {rel}: category {category!r} not in {sorted(ADR_CATEGORIES)}"
            )

        for field in ("supersedes", "superseded_by"):
            if field not in data:
                failures.append(f"  {rel}: missing field {field!r}")
            elif not isinstance(data[field], list):
                failures.append(
                    f"  {rel}: {field} must be a list (got {type(data[field]).__name__})"
                )

        supersedes = data.get("superseded_by") or []
        if supersedes and status != "Superseded":
            failures.append(
                f"  {rel}: superseded_by is non-empty but status is "
                f"{status!r} — must be 'Superseded'"
            )

        # Index by expected_id (filename digits) — falls back gracefully if
        # the frontmatter id is wrong, so reciprocal-link checks still run.
        parsed[expected_id] = (rel, data)

    # Reciprocal-link consistency — pass 2 once every ADR is parsed.
    # Supersedes/superseded_by entries MUST also be quoted strings.
    def _normalize_ids(values):
        return [str(v) for v in (values or [])]

    for adr_id, (rel, data) in parsed.items():
        for other_id in _normalize_ids(data.get("supersedes")):
            other = parsed.get(other_id)
            if other is None:
                failures.append(
                    f"  {rel}: supersedes references unknown ADR {other_id!r}"
                )
                continue
            other_rel, other_data = other
            back = _normalize_ids(other_data.get("superseded_by"))
            if adr_id not in back:
                failures.append(
                    f"  {rel}: supersedes {other_id!r} but {other_rel} "
                    f"does not list {adr_id!r} in superseded_by"
                )

        for other_id in _normalize_ids(data.get("superseded_by")):
            other = parsed.get(other_id)
            if other is None:
                failures.append(
                    f"  {rel}: superseded_by references unknown ADR {other_id!r}"
                )
                continue
            other_rel, other_data = other
            forward = _normalize_ids(other_data.get("supersedes"))
            if adr_id not in forward:
                failures.append(
                    f"  {rel}: superseded_by {other_id!r} but {other_rel} "
                    f"does not list {adr_id!r} in supersedes"
                )

    seen.count("decision records with a numbered filename", numbered)
    seen.count("records whose frontmatter parsed", len(parsed))
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# E2E-01 — all cases.py paths resolve to existing files
# ---------------------------------------------------------------------------

def check_e2e_01():
    failures = []
    seen = Inspected()

    interview = os.path.join(ROOT, "templates", "INTERVIEW.md")
    if not os.path.isfile(interview):
        failures.append("  INTERVIEW.md not found: templates/INTERVIEW.md")

    required_fields = ("id", "spec", "stack", "answers", "required")

    seen.count("test cases defined", len(ALL_TESTS))
    validated = 0
    for test in ALL_TESTS:
        if "skip" in test:
            continue

        validated += 1
        tid = test.get("id", "?")

        # Validate required fields
        for field in required_fields:
            if field not in test:
                failures.append(f"  {tid}: missing field: {field!r}")

        if not test.get("required"):
            failures.append(f"  {tid}: required list is empty")

        stack = test.get("stack", "")
        if stack:
            path = os.path.join(ROOT, stack)
            if not os.path.isfile(path):
                failures.append(f"  {tid}: stack file missing: {stack}")
            elif os.path.getsize(path) == 0:
                failures.append(f"  {tid}: stack file empty: {stack}")

        output_file = test.get("output_file", "templates/base/core/agents.md")
        path = os.path.join(ROOT, output_file)
        if not os.path.isfile(path):
            failures.append(f"  {tid}: output_file missing: {output_file}")

        for ef in test.get("extra_files", []):
            path = os.path.join(ROOT, ef)
            if not os.path.isfile(path):
                failures.append(f"  {tid}: extra_file missing: {ef}")

    seen.count("cases validated", validated)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-05 — end-of-session audit rendered faithfully (inline or delegated)
# ---------------------------------------------------------------------------
# A procedural checklist (the scope.md End of session audit) loses steps and
# its enforcement header when a generator condenses it into bullets. The two
# compliant renderings — inline-verbatim and hard-delegation — both keep the
# load-bearing phrase ("execute each item ... do not summarize"); a paraphrase
# drops it. This check asserts that phrase survives in the output spec
# (agents.md §6.3 directive, every output model) and in every example
# CLAUDE.md that declares a session-protocol section. Examples with no such
# section are out of scope (skipped), not failures.

ENFORCE_RE = re.compile(
    r"execute each item|do not summari[sz]e|do not paraphrase",
    re.IGNORECASE,
)


def _section_block(lines, start_index, stop_pattern):
    """Return text from start_index+1 until a line matching stop_pattern."""
    body = []
    for line in lines[start_index + 1:]:
        if stop_pattern.match(line):
            break
        body.append(line)
    return "\n".join(body)


def check_sys_05():
    failures = []
    seen = Inspected()

    # 1) Output spec — every §6.3 directive in agents.md carries the rule.
    agents_path = os.path.join(ROOT, "templates", "base", "core", "agents.md")
    a_lines = read(agents_path).splitlines()
    h63 = re.compile(r"^###\s+6\.3\b")
    stop_spec = re.compile(r"^(#{1,3}\s|```)")
    found = 0
    for i, line in enumerate(a_lines):
        if h63.match(line):
            found += 1
            block = _section_block(a_lines, i, stop_spec)
            if not ENFORCE_RE.search(block):
                failures.append(
                    f"  agents.md:{i + 1}: §6.3 directive must require "
                    f"inline-verbatim or hard-delegation (missing 'execute "
                    f"each item' / 'do not summarize')"
                )
    seen.count("6.3 directives in agents.md", found)
    if not found:
        failures.append("  agents.md: no '### 6.3' directive found")

    # 2) Examples — any CLAUDE.md with a session-protocol section must render
    #    the audit faithfully; examples without one are out of scope.
    examples_dir = os.path.join(ROOT, "examples")
    head = re.compile(r"^#{2,3}\s.*([Ss]ession protocol|[Ee]nd of session)")
    stop_top = re.compile(r"^##\s")
    examples_read = 0
    protocols = 0
    if os.path.isdir(examples_dir):
        for name in sorted(os.listdir(examples_dir)):
            cm = os.path.join(examples_dir, name, "CLAUDE.md")
            if not os.path.isfile(cm):
                continue
            examples_read += 1
            e_lines = read(cm).splitlines()
            start = next((i for i, l in enumerate(e_lines) if head.match(l)),
                         None)
            if start is None:
                continue
            protocols += 1
            block = _section_block(e_lines, start, stop_top)
            if not ENFORCE_RE.search(block):
                failures.append(
                    f"  examples/{name}/CLAUDE.md: session-protocol section "
                    f"neither inlines the audit verbatim nor hard-delegates "
                    f"(missing 'execute each item' / 'do not summarize') — a "
                    f"soft reference or paraphrase drops the wrap-up steps"
                )

    seen.count("example context files read", examples_read)
    seen.count("of those, carrying a session-protocol section", protocols)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-06 — every usable stack's resolved chain carries the MUST sections
# ---------------------------------------------------------------------------
# ADR-017 defines the canonical stack-template section structure. The MUST
# tier — Stack, Commands, Project structure — is the stack-unique
# contribution the core tier cannot supply. Membership is judged on the
# resolved chain, so a derived stack may inherit a MUST section from its
# parent. Pure-library stacks (manifest layer: library) prescribe no
# directory tree and are exempt from Project structure.

_MUST_SECTIONS = ("Stack", "Commands", "Project structure")


def check_sys_06():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    failures = []
    seen = Inspected()

    stacks = seen.count("stacks resolved", [e for e in entries.values()
                        if e["file"].startswith("templates/stack/")])

    asserted = 0
    for stack in sorted(stacks, key=lambda e: e["id"]):
        sid = stack["id"]
        is_lib = stack.get("layer") == "library"
        files, _ = _resolve_stack(sid, core_ids, entries)

        blob = "\n".join(
            read(os.path.join(ROOT, f))
            for f in files
            if os.path.isfile(os.path.join(ROOT, f))
        )

        for section in _MUST_SECTIONS:
            if section == "Project structure" and is_lib:
                continue
            asserted += 1
            heading = re.compile(
                r"^##\s+" + re.escape(section) + r"\s*$", re.MULTILINE)
            if not heading.search(blob):
                failures.append(
                    f"  {sid}: resolved chain missing MUST section "
                    f"'## {section}' (ADR-017)"
                )

    seen.count("MUST sections asserted across those chains", asserted)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-07 — 360 audit reports live only under docs/audits/
# ---------------------------------------------------------------------------
# templates/base/workflow/360.md [ID: 360-tracking] mandates one audit-storage
# convention: each audit is a dated report at docs/audits/YYYY-MM-DD-360.md,
# and the single-file docs/360-audit.md form is prohibited. This guards the
# rule mechanically — no audit report may live outside docs/audits/, and a
# file inside it MUST use the dated YYYY-MM-DD-360.md name.

_AUDIT_DIR = "docs/audits"

# An audit report file: the prohibited single-file form (360-audit*.md) or a
# dated report (*-360.md). The 360.md template itself matches neither.
_AUDIT_NAME = re.compile(r"(?:360-audit.*|.*-360)\.md$")
_DATED_AUDIT_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-360\.md$")
def check_sys_07():
    failures = []
    seen = Inspected()
    reports = 0
    walked = repository_files()
    for rel in walked:
        name = rel.rsplit("/", 1)[-1]
        if _AUDIT_NAME.match(name):
            reports += 1
            if not rel.startswith(_AUDIT_DIR + "/"):
                failures.append(
                    f"  {rel}: 360 audit report outside {_AUDIT_DIR}/ — move "
                    f"it to {_AUDIT_DIR}/YYYY-MM-DD-360.md "
                    f"(360.md [ID: 360-tracking])"
                )
            elif not _DATED_AUDIT_NAME.match(name):
                failures.append(
                    f"  {rel}: audit file must use the YYYY-MM-DD-360.md "
                    f"dated-report name (360.md [ID: 360-tracking])"
                )

    seen.count("repository files read", walked)
    seen.count("audit reports found", reports)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-08 — every showcased stack keeps its example CLAUDE.md
# ---------------------------------------------------------------------------
# SYS-05 only validates examples that already exist, so a committed example
# could be removed or renamed without any structural failure. This gate
# locks in the example->stack mapping (per ADR-016 examples are
# agent-generated, regenerated on material change): each required example
# MUST have a non-empty CLAUDE.md, and the stack it demonstrates MUST exist
# in the manifest. Adding a new example registers it here; two examples may
# map to the same stack (e.g. astro-portfolio and hybrid-astro).

REQUIRED_EXAMPLES = {
    "astro-portfolio": "stack-astro",
    "hybrid-astro": "stack-astro",
    "fastapi-service": "stack-fastapi",
    "order-service": "stack-fastapi",
    "flask-api": "stack-flask",
    "go-service": "stack-go-service",
    "metricshub": "stack-go-echo",
}


def check_sys_08():
    if not HAS_YAML:
        return [MISSING_YAML]

    _, entries, _ = _load_manifest()
    failures = []
    seen = Inspected()
    seen.count("required examples checked", len(REQUIRED_EXAMPLES))
    seen.count("stacks they map to", len(set(REQUIRED_EXAMPLES.values())))

    for example, stack_id in sorted(REQUIRED_EXAMPLES.items()):
        cm = os.path.join(ROOT, "examples", example, "CLAUDE.md")
        if not os.path.isfile(cm):
            failures.append(
                f"  examples/{example}/CLAUDE.md missing — required "
                f"example for stack '{stack_id}' (ADR-016: regenerate, "
                f"do not delete)"
            )
        elif os.path.getsize(cm) == 0:
            failures.append(f"  examples/{example}/CLAUDE.md is empty")
        if stack_id not in entries:
            failures.append(
                f"  {example}: mapped stack '{stack_id}' not in manifest"
            )

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-09 — sync.py --check inspects without writing
# ---------------------------------------------------------------------------
# A gate that repairs what it inspects reports clean on its second run, so
# only its first invocation carries information. This runs against a
# temporary copy and asserts both directions: check mode reports the
# difference and leaves the bytes alone, plain mode writes. Without the
# second assertion a function that did nothing at all would pass.


def check_sys_09():
    import tempfile

    tools_dir = os.path.join(ROOT, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import sync as sync_tool
    except ImportError as error:
        return [f"  tools/sync.py could not be imported: {error}"]

    marker = "demo"
    stale = (
        "before\n"
        f"<!-- generated:{marker} -->\n"
        "STALE CONTENT\n"
        f"<!-- /generated:{marker} -->\n"
        "after\n"
    )
    failures = []
    seen = Inspected()
    assertions = 0

    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "target.md")

        io.open(target, "w", encoding="utf-8").write(stale)
        changed = sync_tool._update_file(target, {marker: "FRESH"}, True)
        after = io.open(target, encoding="utf-8").read()
        assertions += 2
        if not changed:
            failures.append(
                "  sync.py --check did not report a difference it should see"
            )
        if after != stale:
            failures.append(
                "  sync.py --check wrote to the file it was inspecting — the "
                "first invocation repairs the tree and the second reports "
                "clean"
            )

        io.open(target, "w", encoding="utf-8").write(stale)
        sync_tool._update_file(target, {marker: "FRESH"})
        written = io.open(target, encoding="utf-8").read()
        assertions += 1
        if "FRESH" not in written:
            failures.append(
                "  sync.py without --check did not write; the read-only "
                "assertion above would pass on a no-op"
            )

    # The corpus is a fixture this check builds, so what it reports reaching
    # is the assertions it ran against it. A refactor that returns before
    # them leaves the count short rather than reporting a pass.
    seen.count("fixtures written", 2)
    seen.count("assertions run against them", assertions, floor=3)
    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-10 — a quoted DEPENDS ON directive in prose is not a declaration
# ---------------------------------------------------------------------------
# Consumer-facing sections quote the directive syntax to explain the
# composition model, and reading that prose as a declaration fails the tree
# against a file nobody wrote. The extraction is restricted to the header,
# which is where every real declaration in the tree sits. This asserts both
# directions on a synthetic document: the header is read, and a backticked or
# fenced occurrence in the body is not. Without the positive case, an
# extractor that returned nothing at all would pass.


def check_sys_10():
    document = (
        "# Base — Example\n"
        "[ID: base-example]\n"
        "[DEPENDS ON: templates/base/core/git.md]\n"
        "\n"
        "## Composition\n"
        "\n"
        "Governance resolves through `[DEPENDS ON: ...]` in each file.\n"
        "\n"
        "```\n"
        "[DEPENDS ON: templates/does-not-exist.md]\n"
        "```\n"
    )

    refs = depends_on_refs(document)
    failures = []
    seen = Inspected()
    seen.count("synthetic documents inspected", 1)
    seen.count("directive occurrences in the document",
               document.count("[DEPENDS ON:"), floor=3)
    seen.count("occurrences read as a declaration", len(refs))

    if refs != ["templates/base/core/git.md"]:
        failures.append(
            f"  header declaration not read as the only one: {refs!r} — a "
            f"backticked or fenced directive in body prose is documentation, "
            f"not a declaration, and reading it names a file nobody wrote"
        )

    return seen.failures() + failures, seen.notes()


# ---------------------------------------------------------------------------
# SYS-11 — a prose reference to another file's section ID resolves in every
# chain that carries the referencing file
# ---------------------------------------------------------------------------
# TPL-04 and TPL-06 cover EXTEND/OVERRIDE directives. A rule that names
# another section in running prose -- "`base-quality-gates` states which
# categories a project MUST gate" -- is checked by neither, and it costs
# reach: the referencing file and the referenced one sit at different depths
# in the graph, so the reference resolves in the chains that carry both and
# dangles in the rest. A reader of a dangling one is sent to a section their
# context file does not contain.
#
# The failure is invisible from either file. It appears only per chain, which
# is why this check resolves every root a project can pick rather than reading
# the two files.

# What counts as a reference is decided by the IDs the tree declares, not by
# a list of layer prefixes. A prefix list matches file-level IDs, where a
# reference is least likely to dangle -- the section-level IDs the rule is
# actually about are named `quality-gates-layers`, `security-authn`,
# `testing-shared-path-breadth`, and a prefix list is blind to all of them.
# So any backticked token is a candidate and membership in the declared set
# decides, which cannot narrow again as IDs are added.
_BACKTICKED_TOKEN = re.compile(r"`([a-z0-9][a-z0-9-]*)`")

# A token no template declares is a finding only when it is shaped like an
# ID -- `eslint` and `main` are backticked tokens too, and reading every one
# of them as a broken reference makes the check unusable.
_LAYER_SHAPED_ID = re.compile(r"^(?:base|backend|frontend|platform|stack)-[a-z0-9-]+$")


def check_sys_11():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()

    # The third value from _load_manifest is file_to_id, not the stack list.
    # A stack is an entry under templates/stack/, the same selector MNF-02
    # uses -- reading the whole entry table instead resolves layer templates
    # as though they were stacks and inflates every count.
    # A stack is one of two kinds of root. Extras and the platform are picked
    # independently of it, and a file reaching a consumer only that way sits
    # in no stack chain at all -- so restricting the corpus to stacks makes
    # the scan of that file vacuous: it is carried by zero chains, nothing
    # can be missing from zero chains, and the reference passes unread.
    stack_roots, opt_in_roots = _roots_by_kind(core_ids, entries)

    chains = {}
    for root in list(stack_roots) + list(opt_in_roots):
        files, _ = _resolve_stack(root, core_ids, entries)
        chains[root] = set(f.replace(os.sep, "/") for f in files)

    # all_template_files() returns absolute paths; the manifest names files
    # repo-relative, and the chains are built from the manifest. Normalise to
    # the manifest's form or nothing matches and every chain looks empty.
    def rel_of(path):
        return os.path.relpath(path, ROOT).replace(os.sep, "/")

    defined_in = {}
    for path in all_template_files():
        for section_id, _line in iter_id_declarations(read(path)):
            defined_in.setdefault(section_id, set()).add(rel_of(path))

    references = 0
    cited = set()
    failures = []

    for path in all_template_files():
        rel = rel_of(path)
        content = read(path)
        own = set(sid for sid, _line in iter_id_declarations(content))
        for match in sorted(set(_BACKTICKED_TOKEN.findall(content))):
            if match in own:
                continue
            homes = defined_in.get(match)
            if not homes:
                if _LAYER_SHAPED_ID.match(match):
                    failures.append(
                        f"  {rel}: names `{match}`, which no template declares"
                    )
                continue
            references += 1
            cited.add(match)
            carrying = [s for s, f in chains.items() if rel in f]
            missing = [s for s in carrying if not (homes & chains[s])]
            if missing:
                failures.append(
                    f"  {rel}: names `{match}`, declared in "
                    f"{'/'.join(sorted(homes))}, which is absent from "
                    f"{len(missing)} of the {len(carrying)} chains carrying "
                    f"this file ({', '.join(sorted(missing)[:3])}"
                    f"{', ...' if len(missing) > 3 else ''}) — state the "
                    f"substance inline instead of naming a section the "
                    f"reader's context file does not have"
                )

    # An empty result and a check that reached nothing look identical, so the
    # inputs are counted. Zero chains or zero references is a failure.
    # Each kind is asserted on its own. A combined test passes on 17 stacks
    # and no opt-in root, which is the corpus half-empty and reading full.
    if not stack_roots:
        failures.append("  resolved no stack chains — the check reached "
                        "nothing")
    if not opt_in_roots:
        failures.append("  resolved no opt-in roots — every extra and "
                        "platform file went unread, and a reference "
                        "dangling only there passes unseen")
    if references == 0:
        failures.append(
            "  found no cross-file prose ID references — either the pattern "
            "stopped matching or every reference was removed; both need "
            "looking at rather than reading as a pass"
        )

    # The count of IDs the check can see is reported on every run, pass or
    # fail. A pattern that narrows takes this number down with it, and
    # without it in the output the narrowing is silent -- which is how a
    # prefix list stayed blind to two thirds of the declared IDs while the
    # check reported green.
    notes = [
        f"  section IDs declared: {len(defined_in)}",
        f"  named in another file's prose: {len(cited)}",
        f"  cross-file references checked: {references}",
        f"  stacks resolved: {len(stack_roots)}",
        f"  opt-in roots resolved: {len(opt_in_roots)}",
    ]

    return failures, notes


# ---------------------------------------------------------------------------
# SYS-12 — no resolved chain exceeds its recorded ceiling
# ---------------------------------------------------------------------------
# Between v2.1.0 and v2.72.0 the corpus went from 387KB to 782KB and from 359
# RFC-2119 occurrences to 858, while the file count stayed flat at ~75. The
# growth landed inside the files every chain already carries: five of them
# carry 82% of the smallest chain, and all five resolve into 17 of 17.
#
# sync.py measures chain size for the README's model-limitations table and
# --check fails when the table drifts from the tree. That keeps the number
# accurate and never refuses it. A rule added to a 17-chain file updated the
# table and passed every gate, so the cost of an addition was visible only to
# a reader who went looking for it.
#
# The ceilings are frozen at the measured size rather than given a percentage
# band. A band lets a chain grow silently until the band is spent, and the
# point is that the diff states what an addition costs every consumer of that
# chain. Shrinking passes freely; growth requires raising a number in the
# same change, where a reviewer sees it. This is the retrofit ratchet the
# templates already prescribe for a linter, applied to chain size.
#
# Sizes count decoded characters, not bytes on disk: read() opens in text
# mode, so a CRLF working copy and an LF one measure the same tree the same.
# A byte count would make every ceiling depend on the platform that wrote it.

BUDGET_FILE = "tests/chain-budget.txt"


def _measure_chains():
    """Sizes per root, with the two root kinds returned alongside them.

    Both kinds of root: a stack, and an orthogonal template picked
    independently of the stack, which resolves as its own root. Measuring
    stacks alone leaves every opt-in root uncapped, and a fifth of the
    corpus reaches a consumer only that way. The kinds come back separate
    so a caller reports a count per kind rather than their sum.
    """
    core_ids, entries, _ = _load_manifest()
    stacks, opt_in = _roots_by_kind(core_ids, entries)

    sizes = {}
    for root in list(stacks) + list(opt_in):
        files, _ = _resolve_stack(root, core_ids, entries)
        sizes[root] = sum(len(read(os.path.join(ROOT, f))) for f in files)
    return sizes, stacks, opt_in


def _core_tier_files(core_ids, entries):
    """The files the resolver seeds into every chain regardless of what
    any template declares."""
    return [entries[cid]["file"] for cid in core_ids if cid in entries]


def _declared_closure(start_file):
    """Files reachable from `start_file` by following DEPENDS ON alone.

    This is the walk README instructs an adopter to perform by hand, so it
    reads the directives out of the files rather than the manifest's
    depends_on -- a reader following the README has only the files.
    """
    seen, pending = set(), [start_file]
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        path = os.path.join(ROOT, current)
        if not os.path.isfile(path):
            continue
        seen.add(current)
        pending.extend(depends_on_refs(read(path)))
    return seen


def _read_ceilings():
    """Return {root_id: ceiling} from the recorded budget."""
    ceilings = {}
    for line in read(os.path.join(ROOT, BUDGET_FILE)).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) == 2 and parts[1].isdigit():
            ceilings[parts[0]] = int(parts[1])
    return ceilings


def check_sys_12():
    if not HAS_YAML:
        return [MISSING_YAML]

    if not os.path.exists(os.path.join(ROOT, BUDGET_FILE)):
        return [f"  {BUDGET_FILE} is missing — no root carries a ceiling and "
                f"nothing refuses growth"]

    seen = Inspected()
    measured, stacks, opt_in = _measure_chains()

    # Counted per kind, not summed. Each count carries its own floor, so a
    # kind that empties fails here instead of hiding inside a total that
    # still looks close to right.
    seen.count("stacks measured", stacks)
    seen.count("opt-in roots measured", opt_in)
    ceilings = seen.count("ceilings recorded", _read_ceilings())
    failures = list(seen.failures())

    for root in sorted(measured):
        size = measured[root]
        if root not in ceilings:
            failures.append(
                f"  {root}: resolves to {size} characters and has no ceiling "
                f"in {BUDGET_FILE} — add the line `{root} {size}` rather than "
                f"leaving a root to grow unmeasured"
            )
        elif size > ceilings[root]:
            failures.append(
                f"  {root}: {size} characters against a ceiling of "
                f"{ceilings[root]}, {size - ceilings[root]} over. Every "
                f"project on this chain pays it on every turn. If the "
                f"addition is worth that, raise the ceiling in "
                f"{BUDGET_FILE} in this same change so the diff carries "
                f"the cost"
            )

    for root in sorted(ceilings):
        if root not in measured:
            failures.append(
                f"  {root}: carries a ceiling and resolves to no chain — the "
                f"root was renamed or removed and the entry is stale"
            )

    paired = [r for r in measured if r in ceilings]
    notes = seen.notes()
    if measured:
        widest = max(measured, key=measured.get)
        notes.append(f"  largest chain: {widest} at {measured[widest]} characters")
    if paired:
        tightest = min(paired, key=lambda r: ceilings[r] - measured[r])
        notes.append(
            f"  tightest headroom: {ceilings[tightest] - measured[tightest]} "
            f"characters on {tightest}"
        )
    return failures, notes


# ---------------------------------------------------------------------------
# SYS-13 - the instructed manual walk reaches what the resolver carries
# ---------------------------------------------------------------------------
# README tells an adopter without shell access to build a context file by
# reading the manifest and walking DEPENDS ON. That walk is not the
# resolver: the resolver seeds a core tier unconditionally, and no
# DEPENDS ON directive in the tree declares those files. An adopter
# following an instruction that omits them loses whole rules and gets no
# error, because nothing declares what is absent.
#
# So the instruction and the resolver are compared here rather than
# trusted to agree. The comparison runs in both directions: a file the
# resolver carries and the walk cannot reach is a rule the adopter
# silently loses, and a file the walk reaches that the resolver drops is
# an instruction that overshoots.

def check_sys_13():
    if not HAS_YAML:
        return [MISSING_YAML]

    core_ids, entries, _ = _load_manifest()
    seen = Inspected()
    core_files = seen.count("core-tier files seeded",
                            _core_tier_files(core_ids, entries))
    sizes, stacks, opt_in = _measure_chains()
    seen.count("stacks compared", stacks)
    seen.count("opt-in roots compared", opt_in)
    roots = sorted(sizes)
    failures = list(seen.failures())

    # The instruction is half the pair, so a README that stops naming the
    # core tier has to fail here too -- otherwise this check keeps passing
    # against a document that no longer tells anyone to seed it.
    if "core:" not in read(os.path.join(ROOT, "README.md")):
        failures.append(
            "  README.md no longer tells the manual path to load the "
            "manifest's core: list, so the walk it instructs misses every "
            "file the resolver seeds"
        )

    missed_without_core = 0
    for root in roots:
        entry = entries.get(root)
        if entry is None:
            failures.append(
                f"  {root}: resolves as a root and has no manifest entry, "
                f"so the walk has no file to start from"
            )
            continue

        resolved, _ = _resolve_stack(root, core_ids, entries)
        resolved = set(resolved)
        walk = _declared_closure(entry["file"])
        missed_without_core += len(resolved - walk)
        instructed = walk | set(core_files)

        for path in sorted(resolved - instructed):
            failures.append(
                f"  {root}: the resolver carries {path} and the instructed "
                f"walk cannot reach it — an adopter following README loses "
                f"it with no error, because nothing declares what is absent"
            )
        for path in sorted(instructed - resolved):
            failures.append(
                f"  {root}: the instructed walk reaches {path} and the "
                f"resolver does not carry it — the instruction sends an "
                f"adopter to a file their chain does not include"
            )

    notes = seen.notes()
    notes.append(
        f"  files the DEPENDS ON walk alone would miss, summed over roots: "
        f"{missed_without_core}"
    )
    return failures, notes





# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------

# SYS-14 -- resolve.py accounts for every argument it is given
#
# The resolver took args[0] and ignored the rest, so a root that does not
# exist passed silently whenever it followed a valid one and the wrong chain
# resolved at exit 0. Roots do not compose -- ADR-035 has a stack and an
# orthogonal template each resolving as their own root -- so more than one
# root is refused rather than concatenated.
#
# Each case asserts the exit status AND a phrase from the message, because a
# program that exits 1 for the wrong reason reads identical to one that
# exits 1 for the right one.

RESOLVE_CASES = [
    (["stack-flask"], 0, ""),
    (["bogus-root"], 1, "Unknown stack ID"),
    (["stack-flask", "bogus-root"], 1, "Roots resolve independently"),
    (["stack-flask", "platform-github"], 1, "Roots resolve independently"),
    (["--bogus-flag"], 1, "Unknown flag"),

    # Bare invocation is the usage path, not an error -- same as --help.
    ([], 0, "resolve.py"),
]


def check_sys_14():
    seen = Inspected()
    resolver = os.path.join(ROOT, "tools", "resolve.py")
    seen.count("resolve.py argument cases", RESOLVE_CASES)
    failures = []

    for args, want_code, want_phrase in RESOLVE_CASES:
        proc = subprocess.run(
            [sys.executable, resolver] + args,
            capture_output=True, text=True,
        )
        shown = " ".join(args) or "(no arguments)"
        if proc.returncode != want_code:
            failures.append(
                f"  resolve.py {shown}: exit {proc.returncode}, expected "
                f"{want_code}"
            )
            continue
        if want_phrase and want_phrase not in (proc.stdout + proc.stderr):
            failures.append(
                f"  resolve.py {shown}: exit {want_code} as expected, but the "
                f"message does not carry {want_phrase!r}, so the status may "
                f"be right for the wrong reason"
            )
    return seen.failures() + failures, seen.notes()

CHECKS = [
    {"id": "SYS-01", "spec": "SAIT-SMK-SYS-01-001A",
     "title": "DEPENDS ON paths resolve to existing files", "fn": check_sys_01},
    {"id": "SYS-02", "spec": "SAIT-SMK-SYS-02-001A",
     "title": "All section IDs unique across templates", "fn": check_sys_02},
    {"id": "TPL-04", "spec": "SAIT-SMK-TPL-04-001A",
     "title": "All EXTEND/OVERRIDE refs point to existing IDs", "fn": check_tpl_04},
    {"id": "MNF-01", "spec": "SAIT-INT-MNF-01-001A",
     "title": "Manifest entries reference valid paths and IDs", "fn": check_mnf_01},
    {"id": "MNF-02", "spec": "SAIT-INT-MNF-02-001A",
     "title": "All stacks resolve to valid, non-empty file lists", "fn": check_mnf_02},
    {"id": "MNF-03", "spec": "SAIT-INT-MNF-03-001A",
     "title": "All resolved chains include core tier files", "fn": check_mnf_03},
    {"id": "MNF-04", "spec": "SAIT-INT-MNF-04-001A",
     "title": "Prompt builds for all stacks", "fn": check_mnf_04},
    {"id": "MNF-05", "spec": "SAIT-INT-MNF-05-001A",
     "title": "resolve.py resolution matches PyYAML resolution", "fn": check_mnf_05},
    {"id": "TPL-01", "spec": "SAIT-INT-TPL-01-001A",
     "title": "DEPENDS ON chain from python-fastapi.md is complete", "fn": check_tpl_01},
    {"id": "TPL-02", "spec": "SAIT-INT-TPL-02-001A",
     "title": "EXTEND adds rules without removing base rules", "fn": check_tpl_02},
    {"id": "TPL-03", "spec": "SAIT-INT-TPL-03-001A",
     "title": "OVERRIDE replaces parent section with different content", "fn": check_tpl_03},
    {"id": "TPL-06", "spec": "SAIT-INT-TPL-06-001A",
     "title": "EXTEND/OVERRIDE targets reachable in resolved chain", "fn": check_tpl_06},
    {"id": "TPL-07", "spec": "SAIT-INT-TPL-07-001A",
     "title": "EXTEND sections do not duplicate parent rules", "fn": check_tpl_07},
    {"id": "SYS-03", "spec": "SAIT-SMK-SYS-03-001A",
     "title": "Every template file has a manifest entry", "fn": check_sys_03},
    {"id": "SYS-04", "spec": "SAIT-SMK-SYS-04-001A",
     "title": "DEPENDS ON headers match manifest depends_on", "fn": check_sys_04},
    {"id": "SYS-05", "spec": "SAIT-SMK-SYS-05-001A",
     "title": "End-of-session audit inlined verbatim or hard-delegated", "fn": check_sys_05},
    {"id": "SYS-06", "spec": "SAIT-SMK-SYS-06-001A",
     "title": "Every usable stack's chain carries the MUST sections", "fn": check_sys_06},
    {"id": "SYS-07", "spec": "SAIT-SMK-SYS-07-001A",
     "title": "360 audit reports live only under docs/audits/", "fn": check_sys_07},
    {"id": "SYS-08", "spec": "SAIT-SMK-SYS-08-001A",
     "title": "Every showcased stack keeps its example CLAUDE.md", "fn": check_sys_08},
    {"id": "TPL-08", "spec": "SAIT-SMK-TPL-08-001A",
     "title": "Every base template has at least one [ID:] tag", "fn": check_tpl_08},
    {"id": "TPL-09", "spec": "SAIT-SMK-TPL-09-001A",
     "title": "No empty [ID:] sections", "fn": check_tpl_09},
    {"id": "SYS-09", "spec": "SAIT-SMK-SYS-09-001A",
     "title": "sync.py --check inspects without writing", "fn": check_sys_09},
    {"id": "SYS-10", "spec": "SAIT-SMK-SYS-10-001A",
     "title": "A quoted DEPENDS ON in prose is not a declaration",
     "fn": check_sys_10},
    {"id": "SYS-11", "spec": "SAIT-SMK-SYS-11-001A",
     "title": "Prose ID references resolve in every chain carrying the file",
     "fn": check_sys_11},
    {"id": "SYS-12", "spec": "SAIT-SMK-SYS-12-001A",
     "title": "No resolved chain exceeds its recorded ceiling",
     "fn": check_sys_12},
    {"id": "SYS-13", "spec": "SAIT-SMK-SYS-13-001A",
     "title": "The instructed manual walk reaches what the resolver carries",
     "fn": check_sys_13},
    {"id": "SYS-14", "spec": "SAIT-SMK-SYS-14-001A",
     "title": "resolve.py accounts for every argument it is given",
     "fn": check_sys_14},
    {"id": "ADR-01", "spec": "SAIT-SMK-ADR-01-001A",
     "title": "ADR frontmatter matches the ADR-010 schema", "fn": check_adr_01},
    {"id": "E2E-01", "spec": "SAIT-SMK-E2E-01-001A",
     "title": "All cases.py paths resolve to existing files", "fn": check_e2e_01},
]


# ---------------------------------------------------------------------------
# Report renderers
# ---------------------------------------------------------------------------

def _inspected(r):
    """Render what a check reported inspecting, when it reported anything."""
    if not r.get("notes"):
        return []
    return ["**Inspected**:", "", "```"] + r["notes"] + ["```", ""]


def render_pass(r):
    return ([f"### {r['status']}  {r['id']} — {r['title']}", ""]
            + _inspected(r))


def render_fail(r):
    lines = [f"### {r['status']}  {r['id']} — {r['title']}", ""]
    lines.extend(_inspected(r))
    lines.extend(["**Expected**: all assertions pass with no violations", "",
                  "**Observed**:", "", "```"])
    lines.extend(r["failures"])
    lines.extend(["```", ""])
    return lines


def render_err(r):
    return [f"### {r['status']}  {r['id']} — {r['title']}", "",
            f"**Error**: {r['error']}", ""]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

# PyYAML is a precondition of this suite, not a property of the tree the
# suite checks. Fourteen checks read `templates/manifest.yaml` through it,
# and each reports the missing dependency itself -- so an incomplete
# environment reads as fourteen defects in a clean tree, which is what an
# external contributor sees on their first command.
#
# Which checks need it is asked of the checks rather than listed here. A
# hand-kept list duplicates the guards and drifts from them; a guarded
# check returns its one failure before touching the filesystem, so asking
# costs nothing.
def _blocked_on_yaml(checks):
    """Return the IDs of `checks` whose only failure is the missing dependency."""
    blocked = []
    for check in checks:
        try:
            result = check["fn"]()
        except Exception:
            continue
        failures = result[0] if isinstance(result, tuple) else result
        if failures == [MISSING_YAML]:
            blocked.append(check["id"])
    return blocked


def main():
    started_at = datetime.datetime.now()

    args = sys.argv[1:]
    filter_ids = [a for a in args if not a.startswith("--")]

    checks = CHECKS
    if filter_ids:
        checks = [c for c in CHECKS if c["id"] in filter_ids]
        if not checks:
            print(f"No checks matched: {filter_ids}")
            sys.exit(1)

    # Refuse the run rather than reporting the environment as findings.
    # Nothing about the tree has been read at this point, so there is no
    # partial verdict worth printing alongside the refusal.
    if not HAS_YAML:
        blocked = _blocked_on_yaml(checks)
        if blocked:
            print(
                f"PyYAML is not installed, and {len(blocked)} of the "
                f"{len(checks)} selected check(s) read "
                f"templates/manifest.yaml through it:"
            )
            print(f"  {', '.join(blocked)}")
            print("")
            print("  pip install pyyaml")
            print("")
            print(
                "No check has run. This is an incomplete environment, not a "
                "finding about the tree."
            )
            sys.exit(1)

    results = {PASS: 0, FAIL: 0, ERR: 0}
    run_results = []

    print(f"Running {len(checks)} check(s)...\n")

    for check in checks:
        try:
            # A check returns its failures, or (failures, notes) when it
            # reports what it inspected. Both shapes are accepted so a check
            # gains the report without every other one changing.
            result = check["fn"]()
            failures, notes = result if isinstance(result, tuple) else (result, [])

            # A check that would pass while reporting no inputs is the thing
            # this suite is guarding against, so the runner refuses it rather
            # than trusting each check to remember. A failing check has
            # already said something; only a silent pass is rejected here.
            if not failures and not notes:
                failures = [
                    "  the check passed without reporting what it inspected — "
                    "a corpus that empties is indistinguishable from a clean "
                    "tree until the inputs are counted"
                ]
        except Exception as e:
            print(f"  {ERR}  {check['id']}  — {e}")
            results[ERR] += 1
            run_results.append({
                "id": check["id"], "title": check["title"],
                "status": ERR, "failures": [], "error": str(e),
            })
            continue

        if failures:
            print(f"  {FAIL}  {check['id']}")
            for line in notes:
                print(line)
            for line in failures:
                print(line)
            results[FAIL] += 1
            run_results.append({
                "id": check["id"], "title": check["title"],
                "status": FAIL, "failures": failures, "notes": notes,
                "error": None,
            })
        else:
            print(f"  {PASS}  {check['id']}")
            for line in notes:
                print(line)
            results[PASS] += 1
            run_results.append({
                "id": check["id"], "title": check["title"],
                "status": PASS, "failures": [], "notes": notes,
                "error": None,
            })

    elapsed = (datetime.datetime.now() - started_at).total_seconds()
    total = sum(results.values())
    print(
        f"\n{total} checks — "
        f"{results[PASS]} passed  "
        f"{results[FAIL]} failed  "
        f"{results[ERR]} errors"
        f"  ({elapsed:.1f}s)"
    )

    write_report(run_results, started_at, "smoke", {
        PASS: render_pass,
        FAIL: render_fail,
        ERR: render_err,
    })

    sys.exit(0 if results[FAIL] == 0 and results[ERR] == 0 else 1)


if __name__ == "__main__":
    main()
