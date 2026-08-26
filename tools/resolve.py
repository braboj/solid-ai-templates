"""Resolve dependency chain for a stack template.

Uses the same minimal YAML parser as sync.py — no external
dependencies required.

Usage:
    py tools/resolve.py <stack-id>            # print resolved file list
    py tools/resolve.py <stack-id> --concat   # print concatenated content
    py tools/resolve.py --generate            # cache all stacks to generated/
    py tools/resolve.py --list                # list available stack IDs

The resolution algorithm follows ADR-004:
  1. Add all core tier IDs
  2. Recursively resolve the stack's depends_on tree
  3. Append extras (if any)
"""

import io
import os
import re
import sys
from pathlib import Path
# Set the output encoding at the boundary rather than inheriting the
# console default, which mangles any non-ASCII this program prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "templates" / "manifest.yaml"
GENERATED = ROOT / "generated"


# ---- minimal YAML parser (shared with sync.py) ----

def _parse_manifest(text):
    """Parse manifest.yaml into {section: [entries]}."""
    sections = {}
    current_section = None
    current_entry = None
    list_key = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = re.match(r"^(\w[\w-]*):\s*$", raw_line)
        if m and not raw_line.startswith(" "):
            key = m.group(1)
            if key == "version":
                continue
            current_section = key
            sections.setdefault(current_section, [])
            current_entry = None
            list_key = None
            continue

        # top-level inline list: core: [a, b, c]
        m = re.match(r"^(\w[\w-]*):\s+\[(.+)\]$", raw_line)
        if m and not raw_line.startswith(" "):
            key = m.group(1)
            sections[key] = [v.strip() for v in m.group(2).split(",")]
            continue

        m = re.match(r'^(\w[\w-]*):\s+"?([^"]+)"?\s*$', raw_line)
        if m and not raw_line.startswith(" "):
            continue

        if current_section is None:
            continue

        if stripped.startswith("- id:"):
            current_entry = {"id": stripped.split(":", 1)[1].strip()}
            sections[current_section].append(current_entry)
            list_key = None
            continue

        if current_entry is None:
            continue

        m = re.match(r"^(\w[\w_]*):\s+\[(.+)\]$", stripped)
        if m:
            key = m.group(1)
            vals = [v.strip() for v in m.group(2).split(",")]
            current_entry[key] = vals
            list_key = None
            continue

        m = re.match(r"^(\w[\w_]*):\s*(.*)$", stripped)
        if m and not stripped.startswith("-"):
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                list_key = key
                current_entry[key] = []
            else:
                current_entry[key] = val
                list_key = None
            continue

        # bracketed continuation after an empty "key:" line:
        #   depends_on:
        #     [a, b, c]
        if (
            list_key
            and stripped.startswith("[")
            and stripped.endswith("]")
        ):
            inner = stripped[1:-1]
            current_entry[list_key] = [
                v.strip() for v in inner.split(",") if v.strip()
            ]
            list_key = None
            continue

        if stripped.startswith("- ") and list_key:
            current_entry[list_key].append(stripped[2:].strip())
            continue

    return sections


# ---- resolution engine ----

def load_manifest():
    """Load and parse manifest.yaml.

    Returns (core_ids, entries_by_id, stacks).
    """
    text = io.open(MANIFEST, encoding="utf-8").read()
    manifest = _parse_manifest(text)

    entries = {}
    for section in ("base", "platform", "frontend", "backend", "stacks"):
        for entry in manifest.get(section, []):
            entries[entry["id"]] = entry

    core_ids = manifest.get("core", [])

    stacks = manifest.get("stacks", [])
    return core_ids, entries, stacks


def resolve_chain(stack_id, core_ids, entries):
    """Resolve full dependency chain for a stack.

    Returns ordered list of file paths (relative to repo root).
    """
    resolved = set()
    files = []

    def add(eid):
        if eid in resolved:
            return
        resolved.add(eid)
        entry = entries.get(eid)
        if entry and "file" in entry:
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
    return files


def read_file(rel_path):
    """Read a file relative to the repo root."""
    return io.open(ROOT / rel_path, encoding="utf-8").read()


BANNER = (
    "<!-- Generated by `py tools/resolve.py --generate`. Edit the\n"
    "     source templates under templates/, not this file. Run\n"
    "     `py tools/resolve.py --check` to verify the committed\n"
    "     files are up to date. -->\n"
)


def concat_chain(files):
    """Read and concatenate all files in the chain."""
    parts = []
    for f in files:
        content = read_file(f)
        parts.append(f"<!-- {f} -->\n{content}")
    return BANNER + "\n" + "\n\n".join(parts)


def generate_all(core_ids, entries, stacks):
    """Generate cached resolved files for all stacks."""
    GENERATED.mkdir(exist_ok=True)
    count = 0
    for stack in stacks:
        sid = stack["id"]
        files = resolve_chain(sid, core_ids, entries)
        content = concat_chain(files)
        out = GENERATED / f"{sid}.md"
        io.open(out, "w", encoding="utf-8").write(content)
        print(f"  {sid} -> {out.relative_to(ROOT)}  ({len(files)} files)")
        count += 1
    print(f"\n{count} file(s) generated.")


def check_generated(core_ids, entries, stacks):
    """Check that generated/ files match current resolution.

    Returns list of stale stack IDs.
    """
    stale = []
    for stack in stacks:
        sid = stack["id"]
        out = GENERATED / f"{sid}.md"
        if not out.exists():
            stale.append(sid)
            continue
        files = resolve_chain(sid, core_ids, entries)
        expected = concat_chain(files)
        actual = io.open(out, encoding="utf-8").read()
        if expected != actual:
            stale.append(sid)
    return stale


# ---- CLI ----

def main():
    args = sys.argv[1:]

    if not args or args == ["--help"]:
        print(__doc__)
        sys.exit(0)

    core_ids, entries, stacks = load_manifest()

    if "--list" in args:
        for s in stacks:
            label = s.get("label", "")
            print(f"  {s['id']:<30s} {label}")
        sys.exit(0)

    if "--generate" in args:
        generate_all(core_ids, entries, stacks)
        sys.exit(0)

    if "--check" in args:
        stale = check_generated(core_ids, entries, stacks)
        if stale:
            print(f"{len(stale)} stale file(s):")
            for sid in stale:
                print(f"  {sid}")
            sys.exit(1)
        else:
            print("All generated files up to date.")
            sys.exit(0)

    stack_id = args[0]
    do_concat = "--concat" in args

    if stack_id not in entries:
        print(f"Unknown stack ID: {stack_id}")
        print("Run with --list to see available IDs.")
        sys.exit(1)

    files = resolve_chain(stack_id, core_ids, entries)

    if do_concat:
        print(concat_chain(files))
    else:
        for f in files:
            print(f)


if __name__ == "__main__":
    main()
