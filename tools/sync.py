"""Generate derived sections in README.md, INTERVIEW.md, and SPEC.md
from manifest.yaml.

Usage:
    py tools/sync.py           # update all targets
    py tools/sync.py --check   # exit 1 if any file would change
"""

import io
import re
import sys
import textwrap
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
DOCS_TEMPLATE = ROOT / "templates" / "base" / "core" / "docs.md"


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


def _readme_extras(core_ids, entries, stacks):
    """Generate the README table of roots a project picks beside its stack.

    A stack is one of two kinds of root. The platform and every extra are
    picked independently and resolve as their own root, so a table built
    from the manifest's stacks: key alone leaves a fifth of the catalogue
    off the page that describes the catalogue.
    """
    from resolve import opt_in_roots

    lines = [
        "| Template | Kind | Description |",
        "|----------|------|-------------|",
    ]
    for root in opt_in_roots(core_ids, entries, stacks):
        entry = entries[root]
        parts = entry["file"].split("/")

        # templates/platform/x.md and templates/backend/x.md name their kind
        # in the second segment; templates/base/<kind>/x.md in the third.
        kind = parts[2] if parts[1] == "base" else parts[1]
        lines.append("| `%s` | %s | %s |"
                     % (entry["file"], kind, entry.get("description", "")))
    return "\n".join(lines)


def _readme_root_counts(core_ids, entries, stacks):
    """Generate the README's measured statement of the root model.

    Written by hand these counts sit outside every gate: rewriting
    "20 orthogonal templates" to "99" left sync --check clean and smoke
    at 29/29, because nothing reads a number in prose. Generated here,
    the same edit fails --check. The file span is measured too -- an
    extra resolving to the core tier plus one file is the smallest case,
    not the only one, and the prose said otherwise for half the roots.
    """
    from resolve import opt_in_roots, resolve_chain

    extras = opt_in_roots(core_ids, entries, stacks)
    beyond = []
    for root in extras:
        resolved = resolve_chain(root, core_ids, entries)
        files = resolved[0] if isinstance(resolved, tuple) else resolved
        beyond.append(len(files) - len(core_ids))
    low, high = min(beyond), max(beyond)
    span = ("%d" % low) if low == high else ("%d to %d" % (low, high))
    sentence = (
        "Measured: %d stacks and %d orthogonal templates, %d roots in all. "
        "An extra resolves to the %d core-tier files plus %s of its own."
        % (len(stacks), len(extras), len(stacks) + len(extras),
           len(core_ids), span)
    )

    # Wrapped here rather than left as one long line: the width rule the
    # project declares applies to the README like any other document, and
    # a generated block that violates it makes the gate report a defect
    # no author can fix by editing the file.
    return NEWLINE.join(textwrap.wrap(sentence, 76))


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

def _readme_agents():
    """Render the agent-to-output mapping the templates already state.

    The mapping is written once, in base-docs. The README's copy is
    generated so the two cannot disagree; `--check` fails when it drifts.
    """
    text = io.open(DOCS_TEMPLATE, encoding="utf-8").read()
    section = text.split("## Output file by agent", 1)
    if len(section) != 2:
        raise SystemExit(
            "sync: base-docs has no 'Output file by agent' section; the "
            "README's agent table has no source to render from"
        )

    rows = []
    for line in section[1].splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 2 or set(cells[0]) <= set("- "):
            continue
        if cells[0] == "Agent":
            continue
        rows.append((cells[0], cells[1]))

    if not rows:
        raise SystemExit(
            "sync: the 'Output file by agent' table parsed to zero rows; "
            "refusing to write an empty README mapping"
        )

    out = ["| Agent | Output file |", "|-------|-------------|"]
    out += ["| %s | %s |" % (agent, path) for agent, path in rows]
    return "\n".join(out)


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

    # load_manifest() re-reads the file parse_manifest already produced, but
    # it is the resolver's own entry point and returns the core tier and the
    # stack list the root split needs. Reusing it keeps one definition of
    # what an opt-in root is.
    from resolve import load_manifest

    core_ids, entries, stacks = load_manifest()
    readme_extras = _readme_extras(core_ids, entries, stacks)
    readme_root_counts = _readme_root_counts(core_ids, entries, stacks)
    model_limits = _readme_model_limits()
    agent_outputs = _readme_agents()
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
                "readme-extras": readme_extras,
                "readme-root-counts": readme_root_counts,
                "readme-model-limits": model_limits,
                "readme-agents": agent_outputs,
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
