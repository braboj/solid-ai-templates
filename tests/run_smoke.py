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
import sys

from lib import ROOT, PASS, FAIL, ERR, write_report
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

TEMPLATE_DIRS = [
    os.path.join("templates", "base", "core"),
    os.path.join("templates", "base", "security"),
    os.path.join("templates", "base", "infra"),
    os.path.join("templates", "base", "workflow"),
    os.path.join("templates", "base", "language"),
    os.path.join("templates", "base", "data"),
    os.path.join("templates", "backend"),
    os.path.join("templates", "frontend"),
    os.path.join("templates", "stack"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def all_template_files():
    files = []
    for d in TEMPLATE_DIRS:
        dirpath = os.path.join(ROOT, d)
        for name in os.listdir(dirpath):
            if name.endswith(".md"):
                files.append(os.path.join(dirpath, name))
    return files


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# SYS-01 — DEPENDS ON paths resolve to existing files
# ---------------------------------------------------------------------------

def check_sys_01():
    failures = []
    pattern = re.compile(r'\[DEPENDS ON:\s*([^\]]+)\]')

    for filepath in all_template_files():
        content = read(filepath)
        for match in pattern.finditer(content):
            refs = [r.strip() for r in match.group(1).split(',')]
            for ref in refs:
                ref_path = os.path.join(ROOT, ref)
                if not os.path.isfile(ref_path):
                    rel = os.path.relpath(filepath, ROOT)
                    failures.append(f"  {rel}: DEPENDS ON '{ref}' — file not found")

    return failures


# ---------------------------------------------------------------------------
# SYS-02 — all section IDs unique across all templates
# ---------------------------------------------------------------------------

def check_sys_02():
    failures = []
    seen = {}

    for filepath in all_template_files():
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

    return failures


# ---------------------------------------------------------------------------
# TPL-04 — all EXTEND/OVERRIDE refs point to existing IDs
# ---------------------------------------------------------------------------

def check_tpl_04():
    failures = []
    ref_pattern = re.compile(r'\[(EXTEND|OVERRIDE):\s*([^\]]+)\]')

    declared = set()
    for filepath in all_template_files():
        content = read(filepath)
        for sid, _ in iter_id_declarations(content):
            declared.add(sid)

    for filepath in all_template_files():
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT)
        for match in ref_pattern.finditer(content):
            directive = match.group(1)
            ref_id = match.group(2).strip()
            if ref_id not in declared:
                failures.append(
                    f"  {rel}: [{directive}: {ref_id}] — ID not declared"
                )

    return failures


# ---------------------------------------------------------------------------
# MNF-01 — manifest entries reference valid paths and IDs
# ---------------------------------------------------------------------------

def check_mnf_01():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

    manifest_path = os.path.join(ROOT, "templates", "manifest.yaml")
    if not os.path.isfile(manifest_path):
        return ["  manifest.yaml not found"]

    with io.open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    failures = []
    declared_ids = set()
    entries = []

    for section in manifest.values():
        if isinstance(section, list):
            for entry in section:
                if isinstance(entry, dict):
                    entries.append(entry)
                    if "id" in entry:
                        declared_ids.add(entry["id"])

    for entry in entries:
        path = entry.get("file", "")
        if path and not os.path.isfile(os.path.join(ROOT, path)):
            failures.append(f"  file not found: '{path}' (id: {entry.get('id', '?')})")

    for entry in entries:
        for dep in entry.get("depends_on", []):
            if dep not in declared_ids:
                failures.append(
                    f"  depends_on '{dep}' in '{entry.get('id', '?')}' "
                    f"— ID not declared in manifest"
                )

    return failures


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
    content = read(abs_path)
    pattern = re.compile(r'\[DEPENDS ON:\s*([^\]]+)\]')
    for match in pattern.finditer(content):
        for dep in [r.strip() for r in match.group(1).split(',')]:
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
    for req in required:
        if req not in chain:
            failures.append(f"  python-fastapi.md chain missing: '{req}'")
    return failures


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

    return failures


# ---------------------------------------------------------------------------
# TPL-03 — OVERRIDE replaces parent section entirely
# ---------------------------------------------------------------------------

def check_tpl_03():
    failures = []

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

    return failures


# ---------------------------------------------------------------------------
# MNF-02 — all stacks resolve to valid, non-empty file lists
# ---------------------------------------------------------------------------

def check_mnf_02():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

    core_ids, entries, _ = _load_manifest()
    failures = []

    stacks = [e for e in entries.values()
              if e["file"].startswith("templates/stack/")]

    for stack in stacks:
        sid = stack["id"]
        files, _ = _resolve_stack(sid, core_ids, entries)

        if not files:
            failures.append(f"  {sid}: resolution produced empty file list")
            continue

        for f in files:
            path = os.path.join(ROOT, f)
            if not os.path.isfile(path):
                failures.append(f"  {sid}: resolved file missing: {f}")
            elif os.path.getsize(path) == 0:
                failures.append(f"  {sid}: resolved file empty: {f}")

    return failures


# ---------------------------------------------------------------------------
# MNF-03 — all resolved chains include core tier files
# ---------------------------------------------------------------------------

def check_mnf_03():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

    core_ids, entries, _ = _load_manifest()
    failures = []

    stacks = [e for e in entries.values()
              if e["file"].startswith("templates/stack/")]

    for stack in stacks:
        sid = stack["id"]
        _, resolved_ids = _resolve_stack(sid, core_ids, entries)

        for cid in core_ids:
            if cid not in resolved_ids:
                failures.append(
                    f"  {sid}: core ID '{cid}' missing from "
                    f"resolved chain"
                )

    return failures


# ---------------------------------------------------------------------------
# MNF-04 — prompt builds for all stacks
# ---------------------------------------------------------------------------

def check_mnf_04():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

    core_ids, entries, _ = _load_manifest()
    failures = []

    output_file = "templates/base/core/agents.md"
    output_path = os.path.join(ROOT, output_file)
    if not os.path.isfile(output_path):
        return [f"  output format missing: {output_file}"]

    output_fmt = read(output_path)

    stacks = [e for e in entries.values()
              if e["file"].startswith("templates/stack/")]

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

    return failures


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
        return ["  PyYAML not installed — run: pip install pyyaml"]

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

    return failures


# ---------------------------------------------------------------------------
# TPL-06 — EXTEND/OVERRIDE targets reachable in resolved chain
# ---------------------------------------------------------------------------

def check_tpl_06():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

    core_ids, entries, _ = _load_manifest()
    ref_pattern = re.compile(r'\[(EXTEND|OVERRIDE):\s*([^\]]+)\]')
    failures = []

    stacks = [e for e in entries.values()
              if e["file"].startswith("templates/stack/")]

    for stack in stacks:
        sid = stack["id"]
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
                directive = match.group(1)
                ref_id = match.group(2).strip()
                if ref_id not in chain_ids:
                    failures.append(
                        f"  {sid}: {rel} [{directive}: {ref_id}]"
                        f" — target not in resolved chain"
                    )

    return failures


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
        return ["  PyYAML not installed — run: pip install pyyaml"]

    extend_pattern = re.compile(r'^\[EXTEND:\s*([^\]]+)\]', re.MULTILINE)
    failures = []

    # Build ID → file map
    id_to_file = {}
    for filepath in all_template_files():
        content = read(filepath)
        for sid, _ in iter_id_declarations(content):
            id_to_file[sid] = filepath

    # For each EXTEND, compare child bullets against parent bullets
    for filepath in all_template_files():
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

    return failures


# ---------------------------------------------------------------------------
# SYS-03 — every template file has a manifest entry
# ---------------------------------------------------------------------------

def check_sys_03():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

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
    for filepath in all_template_files():
        rel = os.path.relpath(filepath, ROOT)
        rel_fwd = rel.replace(os.sep, "/")
        if rel_fwd not in {f.replace(os.sep, "/") for f in manifest_files}:
            failures.append(f"  {rel_fwd}: no manifest entry")

    return failures


# ---------------------------------------------------------------------------
# SYS-04 — DEPENDS ON headers match manifest depends_on
# ---------------------------------------------------------------------------

def check_sys_04():
    if not HAS_YAML:
        return ["  PyYAML not installed — run: pip install pyyaml"]

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

    dep_pattern = re.compile(r'\[DEPENDS ON:\s*([^\]]+)\]')
    failures = []

    for filepath in all_template_files():
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        content = read(filepath)

        # Collect file paths from DEPENDS ON headers
        header_files = set()
        for match in dep_pattern.finditer(content):
            for ref in match.group(1).split(","):
                header_files.add(ref.strip())

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

    return failures


# ---------------------------------------------------------------------------
# TPL-08 — every base/core template has at least one [ID:] tag
# ---------------------------------------------------------------------------

CORE_DIRS = [
    os.path.join("templates", "base", "core"),
    os.path.join("templates", "base", "security"),
    os.path.join("templates", "base", "infra"),
    os.path.join("templates", "base", "workflow"),
    os.path.join("templates", "base", "language"),
    os.path.join("templates", "base", "data"),
]


def check_tpl_08():
    failures = []

    for d in CORE_DIRS:
        dirpath = os.path.join(ROOT, d)
        if not os.path.isdir(dirpath):
            continue
        for name in os.listdir(dirpath):
            if not name.endswith(".md"):
                continue
            filepath = os.path.join(dirpath, name)
            content = read(filepath)
            if not any(True for _ in iter_id_declarations(content)):
                rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
                failures.append(f"  {rel}: missing [ID:] tag")

    return failures


# ---------------------------------------------------------------------------
# TPL-09 — no empty [ID:] sections
# ---------------------------------------------------------------------------

def check_tpl_09():
    failures = []
    meta_pattern = re.compile(r'^\[(DEPENDS ON|EXTEND|OVERRIDE):')
    next_id_pattern = re.compile(r'^\s*\[ID:')

    for filepath in all_template_files():
        content = read(filepath)
        rel = os.path.relpath(filepath, ROOT).replace(os.sep, "/")
        lines = content.splitlines()

        # Map declaration line numbers → section IDs (sole-line only).
        decls = {lineno: sid for sid, lineno in iter_id_declarations(content)}

        for i, line in enumerate(lines):
            section_id = decls.get(i + 1)
            if not section_id:
                continue

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

    return failures


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
        return ["  PyYAML not installed — run: pip install pyyaml"]

    failures = []
    decisions_dir = os.path.join(ROOT, "docs", "decisions")
    if not os.path.isdir(decisions_dir):
        return failures

    parsed = {}  # id (str) -> (rel_path, frontmatter dict)

    for name in sorted(os.listdir(decisions_dir)):
        m = ADR_FILENAME.match(name)
        if not m:
            continue  # TEMPLATE.md and any non-numbered files are skipped
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

    return failures


# ---------------------------------------------------------------------------
# E2E-01 — all cases.py paths resolve to existing files
# ---------------------------------------------------------------------------

def check_e2e_01():
    failures = []

    interview = os.path.join(ROOT, "templates", "INTERVIEW.md")
    if not os.path.isfile(interview):
        failures.append("  INTERVIEW.md not found: templates/INTERVIEW.md")

    required_fields = ("id", "spec", "stack", "answers", "required")

    for test in ALL_TESTS:
        if "skip" in test:
            continue

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

    return failures


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

    # 1) Output spec — every §6.3 directive in agents.md carries the rule.
    agents_path = os.path.join(ROOT, "templates", "base", "core", "agents.md")
    a_lines = read(agents_path).splitlines()
    h63 = re.compile(r"^###\s+6\.3\b")
    stop_spec = re.compile(r"^(#{1,3}\s|```)")
    found = False
    for i, line in enumerate(a_lines):
        if h63.match(line):
            found = True
            block = _section_block(a_lines, i, stop_spec)
            if not ENFORCE_RE.search(block):
                failures.append(
                    f"  agents.md:{i + 1}: §6.3 directive must require "
                    f"inline-verbatim or hard-delegation (missing 'execute "
                    f"each item' / 'do not summarize')"
                )
    if not found:
        failures.append("  agents.md: no '### 6.3' directive found")

    # 2) Examples — any CLAUDE.md with a session-protocol section must render
    #    the audit faithfully; examples without one are out of scope.
    examples_dir = os.path.join(ROOT, "examples")
    head = re.compile(r"^#{2,3}\s.*([Ss]ession protocol|[Ee]nd of session)")
    stop_top = re.compile(r"^##\s")
    if os.path.isdir(examples_dir):
        for name in sorted(os.listdir(examples_dir)):
            cm = os.path.join(examples_dir, name, "CLAUDE.md")
            if not os.path.isfile(cm):
                continue
            e_lines = read(cm).splitlines()
            start = next((i for i, l in enumerate(e_lines) if head.match(l)),
                         None)
            if start is None:
                continue
            block = _section_block(e_lines, start, stop_top)
            if not ENFORCE_RE.search(block):
                failures.append(
                    f"  examples/{name}/CLAUDE.md: session-protocol section "
                    f"neither inlines the audit verbatim nor hard-delegates "
                    f"(missing 'execute each item' / 'do not summarize') — a "
                    f"soft reference or paraphrase drops the wrap-up steps"
                )

    return failures


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
        return ["  PyYAML not installed — run: pip install pyyaml"]

    core_ids, entries, _ = _load_manifest()
    failures = []

    stacks = [e for e in entries.values()
              if e["file"].startswith("templates/stack/")]

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
            heading = re.compile(
                r"^##\s+" + re.escape(section) + r"\s*$", re.MULTILINE)
            if not heading.search(blob):
                failures.append(
                    f"  {sid}: resolved chain missing MUST section "
                    f"'## {section}' (ADR-017)"
                )

    return failures


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
_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".idea", ".claude"}


def check_sys_07():
    failures = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if not _AUDIT_NAME.match(name):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
            rel = rel.replace(os.sep, "/")
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
    return failures


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
        return ["  PyYAML not installed — run: pip install pyyaml"]

    _, entries, _ = _load_manifest()
    failures = []

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

    return failures


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

    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "target.md")

        io.open(target, "w", encoding="utf-8").write(stale)
        changed = sync_tool._update_file(target, {marker: "FRESH"}, True)
        after = io.open(target, encoding="utf-8").read()
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
        if "FRESH" not in written:
            failures.append(
                "  sync.py without --check did not write; the read-only "
                "assertion above would pass on a no-op"
            )

    return failures


# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------

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
    {"id": "ADR-01", "spec": "SAIT-SMK-ADR-01-001A",
     "title": "ADR frontmatter matches the ADR-010 schema", "fn": check_adr_01},
    {"id": "E2E-01", "spec": "SAIT-SMK-E2E-01-001A",
     "title": "All cases.py paths resolve to existing files", "fn": check_e2e_01},
]


# ---------------------------------------------------------------------------
# Report renderers
# ---------------------------------------------------------------------------

def render_pass(r):
    return [f"### {r['status']}  {r['id']} — {r['title']}", ""]


def render_fail(r):
    lines = [f"### {r['status']}  {r['id']} — {r['title']}", "",
             "**Expected**: all assertions pass with no violations", "",
             "**Observed**:", "", "```"]
    lines.extend(r["failures"])
    lines.extend(["```", ""])
    return lines


def render_err(r):
    return [f"### {r['status']}  {r['id']} — {r['title']}", "",
            f"**Error**: {r['error']}", ""]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

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

    results = {PASS: 0, FAIL: 0, ERR: 0}
    run_results = []

    print(f"Running {len(checks)} check(s)...\n")

    for check in checks:
        try:
            failures = check["fn"]()
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
            for line in failures:
                print(line)
            results[FAIL] += 1
            run_results.append({
                "id": check["id"], "title": check["title"],
                "status": FAIL, "failures": failures, "error": None,
            })
        else:
            print(f"  {PASS}  {check['id']}")
            results[PASS] += 1
            run_results.append({
                "id": check["id"], "title": check["title"],
                "status": PASS, "failures": [], "error": None,
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
