"""Generate derived sections in README.md, INTERVIEW.md, and SPEC.md
from manifest.yaml.

Usage:
    py tools/sync.py           # update all targets
    py tools/sync.py --check   # exit 1 if any file would change
"""

import io
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


# pyyaml is not required — use a minimal yaml subset parser
# since manifest.yaml only uses simple scalars and lists.

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "templates" / "manifest.yaml"


# ---- minimal YAML parser (no pyyaml dependency) ----

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

        # top-level key like "base:" or "stacks:"
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

        if current_section is None:
            continue

        # top-level scalar like version: "1.0"
        m = re.match(r'^(\w[\w-]*):\s+"?([^"]+)"?\s*$', raw_line)
        if m and not raw_line.startswith(" "):
            continue

        # list item start: "  - id: xxx"
        m = re.match(r"^\s+-\s+id:\s+(.+)$", stripped)
        if stripped.startswith("- id:"):
            current_entry = {"id": stripped.split(":", 1)[1].strip()}
            sections[current_section].append(current_entry)
            list_key = None
            continue

        if current_entry is None:
            continue

        # inline list: depends_on: [a, b, c]
        m = re.match(r"^(\w[\w_]*):\s+\[(.+)\]$", stripped)
        if m:
            key = m.group(1)
            vals = [v.strip() for v in m.group(2).split(",")]
            current_entry[key] = vals
            list_key = None
            continue

        # key: value
        m = re.match(r"^(\w[\w_]*):\s*(.+)$", stripped)
        if m and not stripped.startswith("-"):
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                # start of a block list
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

        # block list item: "      - value"
        if stripped.startswith("- ") and list_key:
            current_entry[list_key].append(stripped[2:].strip())
            continue

    return sections


# ---- generators ----

def _tree(entries, dirname):
    """Generate a directory tree listing."""
    lines = [f"{dirname}/"]
    for i, e in enumerate(entries):
        fname = Path(e["file"]).name
        desc = e.get("description", "")
        prefix = "└──" if i == len(entries) - 1 else "├──"
        pad = " " * max(1, 16 - len(fname))
        lines.append(f"{prefix} {fname}{pad}# {desc}")
    return "\n".join(lines)


def _base_tree(entries):
    """Generate base/ tree with subfolder grouping."""
    from collections import OrderedDict
    groups = OrderedDict()
    for e in entries:
        # file: templates/base/<subfolder>/<name>.md
        parts = Path(e["file"]).parts
        # parts: ('templates', 'base', '<subfolder>', '<name>.md')
        subfolder = parts[2] if len(parts) > 3 else ""
        groups.setdefault(subfolder, []).append(e)

    lines = ["base/"]
    group_keys = list(groups.keys())
    for gi, subfolder in enumerate(group_keys):
        group = groups[subfolder]
        is_last_group = gi == len(group_keys) - 1
        if subfolder:
            g_prefix = "└──" if is_last_group else "├──"
            lines.append(f"{g_prefix} {subfolder}/")
            for i, e in enumerate(group):
                fname = Path(e["file"]).name
                desc = e.get("description", "")
                is_last = i == len(group) - 1
                if is_last_group:
                    c_prefix = "    └──" if is_last else "    ├──"
                else:
                    c_prefix = "│   └──" if is_last else "│   ├──"
                pad = " " * max(1, 16 - len(fname))
                lines.append(f"{c_prefix} {fname}{pad}# {desc}")
        else:
            for i, e in enumerate(group):
                fname = Path(e["file"]).name
                desc = e.get("description", "")
                prefix = "└──" if is_last_group and i == len(group) - 1 else "├──"
                pad = " " * max(1, 16 - len(fname))
                lines.append(f"{prefix} {fname}{pad}# {desc}")
    return "\n".join(lines)


def _spec_sections(manifest):
    """Generate SPEC.md directory listings."""
    parts = []
    # base gets special subfolder treatment
    base_entries = manifest.get("base", [])
    if base_entries:
        parts.append("```\n" + _base_tree(base_entries) + "\n```")
    for section, dirname in [
        ("platform", "platform"),
        ("frontend", "frontend"),
        ("backend", "backend"),
    ]:
        entries = manifest.get(section, [])
        if entries:
            parts.append("```\n" + _tree(entries, dirname) + "\n```")
    # stacks get a simpler listing
    stacks = manifest.get("stacks", [])
    lines = ["stack/"]
    for i, e in enumerate(stacks):
        fname = Path(e["file"]).name
        desc = e.get("description", "")
        prefix = "└──" if i == len(stacks) - 1 else "├──"
        pad = " " * max(1, 28 - len(fname))
        lines.append(f"{prefix} {fname}{pad}# {desc}")
    parts.append("```\n" + "\n".join(lines) + "\n```")
    return "\n\n".join(parts)


def _readme_stacks(manifest):
    """Generate README.md supported stacks table."""
    stacks = manifest.get("stacks", [])
    lines = [
        "| Template | Layer | Description |",
        "|----------|-------|-------------|",
    ]
    for e in stacks:
        f = f"`{e['file']}`"
        layer = e.get("layer", "")
        desc = e.get("description", "")
        lines.append(f"| {f} | {layer} | {desc} |")
    return "\n".join(lines)


def _interview_stacks(manifest):
    """Generate INTERVIEW.md stack selection table."""
    stacks = manifest.get("stacks", [])
    lines = [
        "| If the project is... | Use... | What it covers |",
        "|----------------------|--------|----------------|",
    ]
    for e in stacks:
        label = e.get("label", e["id"])
        f = f"`{e['file']}`"
        desc = e.get("description", "")
        lines.append(f"| {label} | {f} | {desc} |")
    return "\n".join(lines)


# ---- file update ----

MARKER_RE = re.compile(
    r"(<!-- generated:(\S+) -->\n)"
    r"(.*?)"
    r"(<!-- /generated:\2 -->)",
    re.DOTALL,
)


def _update_file(path, replacements):
    """Replace content between markers. Returns True if changed."""
    text = io.open(path, encoding="utf-8").read()
    original = text

    for marker_id, content in replacements.items():
        pattern = re.compile(
            r"(<!-- generated:"
            + re.escape(marker_id)
            + r" -->\n)"
            r"(.*?)"
            r"(<!-- /generated:"
            + re.escape(marker_id)
            + r" -->)",
            re.DOTALL,
        )
        text = pattern.sub(
            r"\g<1>" + content + "\n" + r"\3",
            text,
        )

    if text != original:
        io.open(path, "w", encoding="utf-8").write(text)
        return True
    return False


# ---- main ----

def main():
    check_mode = "--check" in sys.argv

    manifest_text = io.open(MANIFEST, encoding="utf-8").read()
    manifest = _parse_manifest(manifest_text)

    spec_content = _spec_sections(manifest)
    readme_content = _readme_stacks(manifest)
    interview_content = _interview_stacks(manifest)

    targets = [
        (ROOT / "docs" / "SPEC.md", {"spec-directories": spec_content}),
        (ROOT / "README.md", {"readme-stacks": readme_content}),
        (ROOT / "templates" / "INTERVIEW.md", {"interview-stacks": interview_content}),
    ]

    changed = []
    for path, replacements in targets:
        if not path.exists():
            print(f"  SKIP  {path.name} (not found)")
            continue
        if _update_file(path, replacements):
            changed.append(path.name)
            print(f"  SYNC  {path.name}")
        else:
            print(f"  OK    {path.name}")

    # Check generated/ files via resolve.py
    from resolve import load_manifest as _load, check_generated, generate_all
    core_ids, entries, stacks = _load()
    stale = check_generated(core_ids, entries, stacks)
    if stale:
        if check_mode:
            print(f"  STALE {len(stale)} generated file(s)")
            changed.append("generated/")
        else:
            generate_all(core_ids, entries, stacks)
            changed.append("generated/")

    if check_mode and changed:
        print(f"\n{len(changed)} file(s) out of sync.")
        sys.exit(1)
    elif changed:
        print(f"\n{len(changed)} file(s) updated.")
    else:
        print("\nAll files in sync.")


if __name__ == "__main__":
    main()
