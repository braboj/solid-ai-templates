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



ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "templates" / "manifest.yaml"


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

    # The id column is what the instructions above the table consume:
    # both `resolve.py <stack-id>` and `generated/<stack-id>.md` take the
    # id, and most of the ids are not derivable from the filename beside
    # them. Generated from the manifest with the rest of the row, so the
    # two cannot disagree.
    lines = [
        "| If the project is... | Use... | Stack id | What it covers |",
        "|----------------------|--------|----------|----------------|",
    ]
    for e in stacks:
        label = e.get("label", e["id"])
        f = f"`{e['file']}`"
        desc = e.get("description", "")
        lines.append(f"| {label} | {f} | `{e['id']}` | {desc} |")
    return "\n".join(lines)


# Worked resolved-chain examples in SPEC.md, as (heading, stack id) pairs.
# Generated rather than hand-maintained: each block is resolver output, so a
# hand-written copy drifts silently whenever a dependency edge moves and the
# staleness gate reports the file in sync over it.
SPEC_CHAIN_EXAMPLES = [
    ("static-site-astro", "stack-astro"),
    ("python-flask", "stack-flask"),
]

NEWLINE = "\n"


def _spec_chain_examples():
    """Render SPEC.md's worked chain examples from the resolver itself."""
    from resolve import load_manifest as _load, resolve_chain

    core_ids, entries, stacks = _load()
    known = set(entry["id"] for entry in stacks)
    blocks = []

    for heading, stack_id in SPEC_CHAIN_EXAMPLES:
        if stack_id not in known:
            raise SystemExit("sync: unknown stack in examples: " + stack_id)
        files = resolve_chain(stack_id, core_ids, entries)

        # An empty chain would render an empty fence that reads as a real
        # result, which is the drift this generator exists to prevent.
        if not files:
            raise SystemExit("sync: empty chain for " + stack_id)
        body = NEWLINE.join(files)
        blocks.append(
            "### Example: " + heading + NEWLINE * 2
            + "```bash" + NEWLINE
            + "py tools/resolve.py " + stack_id + NEWLINE
            + "```" + NEWLINE * 2
            + "```" + NEWLINE + body + NEWLINE + "```"
        )

    return (NEWLINE * 2).join(blocks)


# A resolved chain is the prompt an adopter actually sends, so the sizes in
# README's model table are measured from it. Hand-maintained, the table
# drifts every time a base template grows, and the number it gives is the
# one thing the reader cannot check before the first attempt truncates.

# Markdown carrying tables, fenced code and hyphenated identifiers tokenizes
# worse than prose. The figure is deliberately below the four-per-token rule
# of thumb: a window chosen from an optimistic estimate does not fit.
CHARS_PER_TOKEN = 3.5

# The chain is not the whole context. The interview goes in with it and the
# generated file comes back out; a window sized to the prompt alone holds
# the question and has no room for the answer.
OVERHEAD_TOKENS = 18000

# What a project can actually buy. A floor landing between two of these
# names a window nobody sells, so the next real one up is the answer.
CONTEXT_WINDOWS = [32000, 64000, 128000, 200000, 256000, 512000, 1000000]


def _window_label(size):
    """Render a context window the way a model card names it."""
    if size >= 1000000:
        return "%gM" % (size / 1000000.0)
    return "%dK" % (size // 1000)


def _readme_model_limits():
    """Render README.md's model table from the resolved chains themselves."""
    from resolve import load_manifest as _load, resolve_chain, concat_chain

    core_ids, entries, stacks = _load()

    # Concatenated here rather than read from generated/: this runs before
    # that directory is refreshed, so reading it would measure the previous
    # revision of every chain the table exists to describe.
    by_layer = {}
    for stack in stacks:
        chain = concat_chain(resolve_chain(stack["id"], core_ids, entries))
        layer = stack.get("layer", "unclassified")
        by_layer.setdefault(layer, []).append((len(chain), stack["id"]))

    if not by_layer:
        raise SystemExit("sync: no stacks to measure")

    lines = [
        "| Stack category | Stacks | Largest chain | Prompt | Min context |",
        "|----------------|--------|---------------|--------|-------------|",
    ]
    for layer in sorted(by_layer):
        chars, largest = sorted(by_layer[layer])[-1]
        tokens = chars / CHARS_PER_TOKEN
        needed = tokens + OVERHEAD_TOKENS
        window = next((w for w in CONTEXT_WINDOWS if w >= needed), None)

        # A chain outgrowing every window a model sells is a finding about
        # the chain. Rendering the largest one anyway would print a floor
        # that does not hold the prompt it is quoted for.
        if window is None:
            raise SystemExit(
                "sync: %s needs ~%dK tokens, beyond every listed window"
                % (layer, round(needed / 1000.0))
            )

        lines.append(
            "| %s | %d | `%s` — %dK chars | ~%dK tokens | %s |"
            % (layer, len(by_layer[layer]), largest, round(chars / 1000.0),
               round(tokens / 1000.0), _window_label(window))
        )
    return NEWLINE.join(lines)


# ---- file update ----

MARKER_RE = re.compile(
    r"(<!-- generated:(\S+) -->\n)"
    r"(.*?)"
    r"(<!-- /generated:\2 -->)",
    re.DOTALL,
)


def _update_file(path, replacements, check_mode=False):
    """Replace content between markers. Returns True if the file differs.

    In check mode the comparison is made and nothing is written. A gate
    that repairs what it inspects reports clean on its second run, so
    only the first invocation would carry information.
    """
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

        # A function replacement, not a template string: generated
        # content is data, and a backslash in it would otherwise be
        # read as a group reference and silently rewrite the block.
        text, hits = pattern.subn(
            lambda m, c=content: m.group(1) + c + NEWLINE + m.group(3),
            text,
        )

        # A marker the file does not carry substitutes nothing, so the
        # document keeps whatever was written there by hand and the gate
        # reports it in sync. Deleting a pair of comments would then
        # freeze a generated table and turn the check green over it.
        if not hits:
            raise SystemExit(
                "sync: %s carries no marker for %s; generated content has "
                "nowhere to go and the staleness gate cannot see it"
                % (path.name, marker_id)
            )

    if text != original:
        if not check_mode:
            io.open(path, "w", encoding="utf-8").write(text)
        return True
    return False


# ---- main ----

def main():
    check_mode = "--check" in sys.argv

    manifest_text = io.open(MANIFEST, encoding="utf-8").read()

    # One parser, not two. resolve.py's is the implementation MNF-05
    # cross-validates against PyYAML; a second copy here drifted from it
    # silently, dropping the core tier and every block-list depends_on.
    from resolve import parse_manifest

    manifest = parse_manifest(manifest_text)

    spec_content = _spec_sections(manifest)
    chain_examples = _spec_chain_examples()
    readme_content = _readme_stacks(manifest)
    model_limits = _readme_model_limits()
    interview_content = _interview_stacks(manifest)

    targets = [
        (
            ROOT / "docs" / "SPEC.md",
            {
                "spec-directories": spec_content,
                "spec-chain-examples": chain_examples,
            },
        ),
        (
            ROOT / "README.md",
            {
                "readme-stacks": readme_content,
                "readme-model-limits": model_limits,
            },
        ),
        (ROOT / "templates" / "INTERVIEW.md", {"interview-stacks": interview_content}),
    ]

    changed = []
    for path, replacements in targets:
        if not path.exists():
            print(f"  SKIP  {path.name} (not found)")
            continue
        if _update_file(path, replacements, check_mode):
            changed.append(path.name)
            print(f"  {'STALE' if check_mode else 'SYNC '} {path.name}")
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
