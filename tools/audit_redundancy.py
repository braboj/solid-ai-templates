"""Audit redundant rules across resolved template chains.

Reports rule lines that appear in two or more active sections within a
single resolved stack chain. Duplicates that the override model
legitimately produces are excluded: when one section supersedes another
via `[OVERRIDE: id]` (directly or transitively), a shared rule between
them is the replacement working as designed, not redundancy.

A sibling duplicate IS reported: two sections that both `[EXTEND: x]`
the same parent, or two unrelated sections, that state the same rule —
the agent loads it twice with neither marked as authoritative.

Limitations: fingerprints the first line of each bullet, so a rule whose
wording diverges only after a line wrap may slip past exact matching;
use `--near` for paraphrases. Judgment still required — a duplicate is
not always wrong (see docs/meta/template-content-quality.md).

`--check` is a CI ratchet: it fails only on exact duplicates NOT in the
BASELINE below, so new redundancy is blocked while known dups are worked
off through their owning issues. Remove a BASELINE entry once its dup is
resolved; `--check` reports any baseline entry that no longer applies.

Usage:
    py tools/audit_redundancy.py            # exact in-chain duplicates
    py tools/audit_redundancy.py --near     # also show near-duplicates
    py tools/audit_redundancy.py --check    # exit 1 on NEW exact dups
"""

import io
import re
import sys
from difflib import SequenceMatcher

from resolve import load_manifest, resolve_chain, read_file

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

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
TAG = re.compile(r"^\[(ID|OVERRIDE|EXTEND):\s*([^\]]+)\]\s*$")
BULLET = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)$")
MIN_LEN = 30
NEAR_THRESHOLD = 0.87

# Known in-chain exact duplicates accepted for now. `--check` ignores
# these and fails only on NEW duplicates. Each key is
# (fingerprint, (fileA, fileB)) with files sorted; the value is the
# reason / owning issue. Remove an entry once its duplicate is resolved.
# Currently empty — `--check` enforces a true zero.
BASELINE = {}


def normalize(text):
    """Reduce a rule line to a comparable fingerprint."""
    t = re.sub(r"`[^`]*`", " ", text)
    t = re.sub(r"\*\*([^*]*)\*\*", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def parse_sections(rel_path):
    """Split a template file into sections with their tags and rules.

    Returns a list of dicts: {file, heading, ids, overrides, rules}
    where rules is {fingerprint: original_line}.
    """
    sections = []
    current = None
    in_fence = False

    for raw in read_file(rel_path).splitlines():
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        m = HEADING.match(raw)
        if m:
            current = {
                "file": rel_path,
                "heading": m.group(2).strip(),
                "ids": [],
                "overrides": [],
                "rules": {},
            }
            sections.append(current)
            continue

        if current is None:
            continue

        m = TAG.match(raw.strip())
        if m:
            kind, value = m.group(1), m.group(2).strip()
            if kind == "ID":
                current["ids"].append(value)
            elif kind == "OVERRIDE":
                current["overrides"].append(value)
            continue

        # skip table rows
        if "|" in raw:
            continue
        m = BULLET.match(raw)
        if m:
            fp = normalize(m.group(1))
            if len(fp) >= MIN_LEN:
                current["rules"].setdefault(fp, m.group(1).strip())

    return sections


def chain_sections(stack_id, core_ids, entries):
    """All sections across a stack's resolved chain, plus a supersedes
    relation derived from [OVERRIDE] tags (transitive closure)."""
    files = resolve_chain(stack_id, core_ids, entries)
    sections = []
    for f in files:
        sections.extend(parse_sections(f))

    id_to_idx = {}
    for i, s in enumerate(sections):
        for sid in s["ids"]:
            id_to_idx[sid] = i

    # direct: idx -> set of section indices it overrides
    direct = {i: set() for i in range(len(sections))}
    for i, s in enumerate(sections):
        for target in s["overrides"]:
            if target in id_to_idx:
                direct[i].add(id_to_idx[target])

    # transitive closure
    supersedes = {i: set() for i in range(len(sections))}
    for i in range(len(sections)):
        stack = list(direct[i])
        while stack:
            j = stack.pop()
            if j not in supersedes[i]:
                supersedes[i].add(j)
                stack.extend(direct[j])

    return sections, supersedes


def related(a, b, supersedes):
    """True if section a and b are in an override relationship."""
    return b in supersedes[a] or a in supersedes[b]


def find_exact(sections, supersedes):
    """Yield (fingerprint, original, idx_a, idx_b) for exact in-chain
    duplicates across non-override section pairs."""
    by_fp = {}
    for i, s in enumerate(sections):
        for fp, original in s["rules"].items():
            by_fp.setdefault(fp, []).append((i, original))
    for fp, hits in by_fp.items():
        for a in range(len(hits)):
            for b in range(a + 1, len(hits)):
                ia, original = hits[a]
                ib, _ = hits[b]
                if sections[ia]["file"] == sections[ib]["file"]:
                    continue
                if related(ia, ib, supersedes):
                    continue
                yield fp, original, ia, ib


def find_near(sections, supersedes):
    """Yield (ratio, fp_a, fp_b, idx_a, idx_b) for near-duplicate rules
    across non-override section pairs in different files. Candidate pairs
    are prefiltered to those sharing a token of length >= 6, keeping the
    comparison count tractable on large chains."""

    # (fp, idx)
    rules = []
    for i, s in enumerate(sections):
        for fp in s["rules"]:
            rules.append((fp, i))

    token_index = {}
    for idx, (fp, _) in enumerate(rules):
        for tok in set(t for t in fp.split() if len(t) >= 6):
            token_index.setdefault(tok, []).append(idx)

    candidates = set()
    for hits in token_index.values():
        # skip ubiquitous tokens
        if len(hits) > 80:
            continue
        for a in range(len(hits)):
            for b in range(a + 1, len(hits)):
                candidates.add((hits[a], hits[b]))

    seen = set()
    for ra, rb in candidates:
        fa, ia = rules[ra]
        fb, ib = rules[rb]
        if ia == ib or fa == fb:
            continue
        if sections[ia]["file"] == sections[ib]["file"]:
            continue
        if abs(len(fa) - len(fb)) > 30 or related(ia, ib, supersedes):
            continue
        key = tuple(sorted([fa, fb]))
        if key in seen:
            continue
        ratio = SequenceMatcher(None, fa, fb).ratio()
        if ratio >= NEAR_THRESHOLD:
            seen.add(key)
            yield ratio, fa, fb, ia, ib


def collect(core_ids, entries, stacks, want_near=False):
    """Run exact (and optionally near) detection over every stack,
    aggregating each unique finding to the set of chains it affects."""

    # key -> {"original", "sites", "chains"}
    exact = {}
    near = {}
    for stack in stacks:
        sid = stack["id"]
        sections, supersedes = chain_sections(sid, core_ids, entries)

        for fp, original, ia, ib in find_exact(sections, supersedes):
            files = tuple(sorted(
                [sections[ia]["file"], sections[ib]["file"]]
            ))
            sites = tuple(sorted([
                f"{sections[ia]['file']} §{sections[ia]['heading']}",
                f"{sections[ib]['file']} §{sections[ib]['heading']}",
            ]))
            key = (fp, sites)
            rec = exact.setdefault(
                key,
                {"original": original, "sites": sites, "fp": fp,
                 "files": files, "chains": set()},
            )
            rec["chains"].add(sid)

        if not want_near:
            continue
        for ratio, fa, fb, ia, ib in find_near(sections, supersedes):
            sites = tuple(sorted([
                f"{sections[ia]['file']} §{sections[ia]['heading']}",
                f"{sections[ib]['file']} §{sections[ib]['heading']}",
            ]))
            key = tuple(sorted([fa, fb])) + (sites,)
            rec = near.setdefault(
                key,
                {"ratio": ratio, "a": fa, "b": fb, "sites": sites,
                 "chains": set()},
            )
            rec["chains"].add(sid)
    return exact, near


def main():
    args = sys.argv[1:]
    if "--help" in args:
        print(__doc__)
        sys.exit(0)

    core_ids, entries, stacks = load_manifest()
    exact, near = collect(core_ids, entries, stacks, want_near="--near" in args)

    print("=" * 70)
    print("EXACT in-chain rule duplicates")
    print("(override-superseded pairs excluded)")
    print("=" * 70)
    for rec in sorted(exact.values(), key=lambda r: -len(r["chains"])):
        chains = sorted(rec["chains"])
        reason = BASELINE.get((rec["fp"], rec["files"]))
        tag = f"  [baselined: {reason}]" if reason else ""
        print(f"\n* {len(chains)} chain(s): {', '.join(chains)}{tag}")
        for site in rec["sites"]:
            print(f"    {site}")
        print(f"    rule: {rec['original'][:84]}")
    n_base = sum(1 for r in exact.values()
                 if (r["fp"], r["files"]) in BASELINE)
    print(f"\n>>> {len(exact)} exact in-chain duplicate(s) "
          f"({n_base} baselined)")

    if "--near" in args:
        print("\n" + "=" * 70)
        print(f"NEAR in-chain duplicates (>= {NEAR_THRESHOLD})")
        print("=" * 70)
        for rec in sorted(near.values(),
                          key=lambda r: (-len(r["chains"]), -r["ratio"])):
            chains = sorted(rec["chains"])
            print(f"\n~{rec['ratio']:.2f} | {len(chains)} chain(s): "
                  f"{', '.join(chains)}")
            for site in rec["sites"]:
                print(f"    {site}")
            print(f"    A: {rec['a'][:80]}")
            print(f"    B: {rec['b'][:80]}")
        print(f"\n>>> {len(near)} near in-chain duplicate(s)")

    if "--check" in args:
        present = set()
        new_dups = []
        for rec in exact.values():
            bkey = (rec["fp"], rec["files"])
            if bkey in BASELINE:
                present.add(bkey)
            else:
                new_dups.append(rec)

        resolved = set(BASELINE) - present
        if resolved:
            print("\nBaseline entries no longer present "
                  "(remove from BASELINE):")
            for fp, files in sorted(resolved):
                print(f"  {fp[:56]}  {files}")

        if new_dups:
            print(f"\nFAIL: {len(new_dups)} new exact in-chain "
                  f"duplicate(s) beyond the baseline:")
            for rec in new_dups:
                print(f"  rule: {rec['original'][:70]}")
                for site in rec["sites"]:
                    print(f"      {site}")
            print("\nFix the duplicate, or add it to BASELINE in "
                  "tools/audit_redundancy.py with its owning issue.")
            sys.exit(1)

        print(f"\nOK: no new exact in-chain duplicates "
              f"({len(present)} baselined).")
        sys.exit(0)


if __name__ == "__main__":
    main()
