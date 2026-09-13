"""Aggregate scored trials into the report the design's section 6 fixes.

Per metric: the mean per arm, the three paired contrasts, a bias-corrected and
accelerated bootstrap interval over the paired differences, and the verdict
read against that metric's declared direction. Nothing here decides by eye,
and nothing here decides a direction either: both the direction and the
verdict rule were fixed before any trial ran.

Two properties of K = 3 are carried into the output rather than hidden in it.
Every interval is labelled descriptive, because no arrangement of three
paired differences reaches conventional significance. And a metric whose
bootstrap distribution is degenerate — three identical differences — reports
the fallback it used instead of an interval it cannot compute.
"""

import argparse
import datetime
import glob
import io
import json
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
AUDITS = os.path.join(lib.ROOT, "docs", "audits")

RESAMPLES = 10000
CONFIDENCE = 0.95

# The three contrasts, and the question each answers. B - C is the one an
# adopter asks: a large B - A beside an equally large C - A is not a result
# for the templates.
CONTRASTS = (("B", "A"), ("C", "A"), ("B", "C"))

# Declared in the design before the run. "up" improves upward, "down"
# improves downward, "neutral" is reported without a verdict.
UP, DOWN, NEUTRAL = "up", "down", "neutral"

# The primary dimensions the report leads with, owner-declared.
PRIMARY = ("judge_design", "judge_readability", "judge_maintainability")

# The non-inferiority margins, for the claim that a metric was preserved
# rather than merely not shown to differ.
MARGINS = {
    "task_success": ("2 pp", 0.02),
    "adherence": ("5 pp", 0.05),
    "judge_design": ("0.3 points", 0.3),
    "judge_readability": ("0.3 points", 0.3),
    "judge_maintainability": ("0.3 points", 0.3),
}


def path(payload, *keys):
    """Follow a path through nested dicts, answering None at the first gap."""
    cursor = payload
    for key in keys:
        if not isinstance(cursor, dict) or key not in cursor:
            return None
        cursor = cursor[key]
    return cursor


def metric_value(trial, *keys):
    """A metric's value, or None where it was recorded as missing."""
    record = path(trial, "scores", *keys[:1])
    if not isinstance(record, dict) or record.get("missing"):
        return None
    return path(record, "value", *keys[1:]) if len(keys) > 1 else \
        record.get("value")


def per_kloc(trial, key):
    """A finding count per thousand source lines the tool actually saw."""
    count = metric_value(trial, key)
    lines = path(trial, "scores", key, "seen", "lines")
    if count is None or not lines:
        return None
    return round(count / (lines / 1000.0), 2)


def task_success(trial):
    """The hidden suite's pass rate, and zero where nothing installed.

    The design fixes this: a trial whose agent produced no installable
    workspace scores zero on task success rather than missing, because that is
    an outcome of the run and not a gap in the measurement.
    """
    rate = metric_value(trial, "hidden_suite")
    if rate is not None:
        return rate
    if metric_value(trial, "install") is False:
        return 0.0
    return None


def boolean(trial, *keys):
    value = metric_value(trial, *keys)
    return None if value is None else (1.0 if value else 0.0)


def extension_points(trial):
    axes = metric_value(trial, "structure", "extension_points")
    if not isinstance(axes, dict) or not axes:
        return None
    return sum(1 for present in axes.values() if present)


def structure_count(trial, key):
    value = metric_value(trial, "structure", key)
    return None if value is None else len(value)


def judge_score(trial, dimension):
    return path(trial, "judge", "answer", "rubric", dimension, "score")


def pattern_count(trial, verdict):
    patterns = path(trial, "judge", "answer", "patterns")
    if not isinstance(patterns, list):
        return None
    return sum(1 for entry in patterns if entry.get("verdict") == verdict)


# Every metric, its direction and where its number comes from. The direction
# column is the design's, declared before the run; an interval is read against
# it and never against "bigger is better".
METRICS = (
    ("judge_design", "Design (SOLID and patterns), 1-5", UP,
     lambda t: judge_score(t, "design")),
    ("judge_readability", "Readability, 1-5", UP,
     lambda t: judge_score(t, "readability")),
    ("judge_maintainability", "Maintainability, 1-5", UP,
     lambda t: judge_score(t, "maintainability")),

    ("task_success", "Task success, hidden suite pass rate", UP, task_success),
    ("install", "Installs in a clean environment", UP,
     lambda t: boolean(t, "install")),
    ("adherence", "Adherence checklist fraction", UP,
     lambda t: metric_value(t, "adherence")),

    ("judge_srp", "SRP, 1-5", UP, lambda t: judge_score(t, "srp")),
    ("judge_ocp", "OCP, 1-5", UP, lambda t: judge_score(t, "ocp")),
    ("judge_lsp", "LSP, 1-5", UP, lambda t: judge_score(t, "lsp")),
    ("judge_isp", "ISP, 1-5", UP, lambda t: judge_score(t, "isp")),
    ("judge_dip", "DIP, 1-5", UP, lambda t: judge_score(t, "dip")),
    ("judge_naming", "Naming and abstraction, 1-5", UP,
     lambda t: judge_score(t, "naming_and_abstraction")),
    ("judge_errors", "Error design, 1-5", UP,
     lambda t: judge_score(t, "error_design")),
    ("judge_tests", "Test quality, 1-5", UP,
     lambda t: judge_score(t, "test_quality")),

    ("patterns_warranted", "Patterns warranted", UP,
     lambda t: pattern_count(t, "warranted")),
    ("patterns_over_engineered", "Patterns over-engineered", DOWN,
     lambda t: pattern_count(t, "over_engineered")),
    ("patterns_missed", "Patterns missed", DOWN,
     lambda t: pattern_count(t, "missed")),

    ("coverage", "Line coverage of the trial's own tests, %", UP,
     lambda t: metric_value(t, "coverage", "line")),
    ("docstrings", "Docstring coverage, %", UP,
     lambda t: metric_value(t, "docstrings")),

    ("ruff_per_kloc", "Lint findings per KLOC", DOWN,
     lambda t: per_kloc(t, "ruff")),
    ("ruff_total", "Lint findings", DOWN, lambda t: metric_value(t, "ruff")),
    ("unformatted", "Files the formatter would change", DOWN,
     lambda t: metric_value(t, "ruff_format")),
    ("mypy_errors", "Type errors under --strict", DOWN,
     lambda t: metric_value(t, "mypy")),
    ("bandit_serious", "Security findings, high and medium", DOWN,
     lambda t: metric_value(t, "bandit")),
    ("complexity_max", "Highest cognitive complexity", DOWN,
     lambda t: metric_value(t, "complexity", "max")),
    ("complexity_over_15", "Functions over complexity 15", DOWN,
     lambda t: metric_value(t, "complexity", "over_15")),
    ("mean_cc", "Mean cyclomatic complexity", DOWN,
     lambda t: metric_value(t, "radon", "mean_cc")),
    ("min_mi", "Lowest maintainability index", NEUTRAL,
     lambda t: metric_value(t, "radon", "min_mi")),
    ("unused", "Unused names", DOWN, lambda t: metric_value(t, "unused")),

    ("extension_points", "Extension axes present, of three", UP,
     extension_points),
    ("layering_violations", "Domain modules reaching Flask or the database",
     DOWN, lambda t: structure_count(t, "layering_violations")),
    ("money_in_routes", "Routes doing pricing arithmetic", DOWN,
     lambda t: structure_count(t, "money_in_routes")),
    ("bool_parameters", "Boolean parameters", DOWN,
     lambda t: structure_count(t, "bool_parameters")),
    ("kind_ladders", "Conditional ladders over rule kinds", DOWN,
     lambda t: structure_count(t, "kind_ladders")),
    ("surface_extra", "Public names beyond the specification", DOWN,
     lambda t: len(metric_value(t, "structure", "surface", "extra") or [])
     if metric_value(t, "structure", "surface") else None),
    ("surface_missing", "Specified names missing", DOWN,
     lambda t: len(metric_value(t, "structure", "surface", "missing") or [])
     if metric_value(t, "structure", "surface") else None),
    ("mutual_imports", "Mutually importing module pairs", DOWN,
     lambda t: metric_value(t, "structure", "graph", "mutual_import_pairs")),
    ("instability", "Mean instability of domain modules", NEUTRAL,
     lambda t: metric_value(t, "structure", "graph", "mean_instability")),

    ("xss_inert", "Stored payload renders inert", UP,
     lambda t: boolean(t, "web", "xss_inert")),
    ("csrf_refused", "A post without a token is refused", UP,
     lambda t: boolean(t, "web", "csrf_refused_without_token")),
    ("axe_violations", "Accessibility violations", DOWN,
     lambda t: path(t, "scores", "web", "accessibility", "value")),
    ("html_invalid", "HTML validity errors", DOWN,
     lambda t: path(t, "scores", "web", "html_validity", "value")),
    ("builder_bytes", "Invoice builder response size, bytes", DOWN,
     lambda t: metric_value(t, "web", "builder_bytes")),
    ("builder_subrequests", "Invoice builder subrequests", DOWN,
     lambda t: metric_value(t, "web", "builder_subrequests")),

    ("output_tokens", "Output tokens", DOWN,
     lambda t: metric_value(t, "cost", "output_tokens")),
    ("turns", "Turns", DOWN, lambda t: metric_value(t, "cost", "turns")),
    ("wall_seconds", "Wall time, seconds", DOWN,
     lambda t: metric_value(t, "cost", "elapsed_s")),
    ("cost_usd", "Cost, USD", DOWN,
     lambda t: metric_value(t, "cost", "cost_usd")),
    ("source_lines", "Source lines", DOWN,
     lambda t: metric_value(t, "scope", "source_lines")),
    ("tracked_files", "Files", DOWN,
     lambda t: metric_value(t, "scope", "tracked_files")),
    ("unasked_artifacts", "Artifacts nobody asked for", DOWN,
     lambda t: metric_value(t, "scope", "unasked_artifacts")),
)


def bca_interval(differences, seed):
    """A bias-corrected and accelerated bootstrap interval over K differences.

    Returns the interval and, where the method cannot be applied, the reason
    and the fallback used. Three identical differences make the bootstrap
    distribution a point mass: the bias correction is then infinite, and
    reporting a percentile interval with that stated is honest where
    reporting a computed BCa interval would not be.
    """
    count = len(differences)
    if count < 2:
        return {"low": None, "high": None,
                "method": "not computed: fewer than two paired differences"}
    observed = statistics.fmean(differences)
    shuffler = random.Random(seed)
    replicates = []
    for _ in range(RESAMPLES):
        sample = [differences[shuffler.randrange(count)] for _ in range(count)]
        replicates.append(statistics.fmean(sample))
    replicates.sort()

    if replicates[0] == replicates[-1]:
        return {"low": observed, "high": observed,
                "method": "degenerate: every paired difference is identical, "
                          "so every resample has the same mean"}

    normal = statistics.NormalDist()
    below = sum(1 for value in replicates if value < observed)
    share = below / RESAMPLES
    if share <= 0 or share >= 1:
        low = replicates[int((1 - CONFIDENCE) / 2 * RESAMPLES)]
        high = replicates[min(RESAMPLES - 1,
                              int((1 + CONFIDENCE) / 2 * RESAMPLES))]
        return {"low": low, "high": high,
                "method": "percentile: the bias correction is undefined "
                          "because no resample fell on one side of the mean"}

    bias = normal.inv_cdf(share)

    # Jackknife acceleration. With every difference equal the denominator is
    # zero, which the degenerate branch above has already taken.
    jackknife = [statistics.fmean(differences[:i] + differences[i + 1:])
                 for i in range(count)]
    centre = statistics.fmean(jackknife)
    deviations = [centre - value for value in jackknife]
    denominator = 6 * (sum(d * d for d in deviations) ** 1.5)
    acceleration = (sum(d ** 3 for d in deviations) / denominator
                    if denominator else 0.0)

    bounds = []
    for tail in ((1 - CONFIDENCE) / 2, (1 + CONFIDENCE) / 2):
        z = normal.inv_cdf(tail)
        adjusted = bias + (bias + z) / (1 - acceleration * (bias + z))
        position = normal.cdf(adjusted)
        index = min(RESAMPLES - 1, max(0, int(position * RESAMPLES)))
        bounds.append(replicates[index])
    return {"low": bounds[0], "high": bounds[1],
            "method": "BCa, %d resamples, %d%%" % (RESAMPLES,
                                                   int(100 * CONFIDENCE))}


def verdict(interval, direction):
    """Better, worse, or no improvement shown — read against the direction."""
    low, high = interval.get("low"), interval.get("high")
    if low is None or high is None:
        return "not computed"
    if direction == NEUTRAL:
        return "reported without a verdict"
    if low <= 0 <= high:
        return "no improvement shown"
    improving = (low > 0) if direction == UP else (high < 0)
    return "better" if improving else "worse"


def non_inferior(key, interval, direction):
    """Whether a metric can be claimed preserved, not merely not-shown-worse.

    An interval containing zero is absence of evidence. The claim that nothing
    got worse needs the whole degradation side of the interval inside the
    margin the design fixes.
    """
    if key not in MARGINS:
        return None
    label, margin = MARGINS[key]
    low, high = interval.get("low"), interval.get("high")
    if low is None or high is None:
        return None
    degradation = -low if direction == UP else high
    return {"margin": label, "within": degradation <= margin}


def load(root):
    """Every scored trial, with its judging attached where one exists."""
    trials = {}
    for file in sorted(glob.glob(os.path.join(root, "scores", "*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            scores = json.load(handle)
        trials[scores["name"]] = {"scores": scores, "judge": None}

    for file in sorted(glob.glob(os.path.join(root, "judge", "T*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            judging = json.load(handle)
        name = judging.get("trial")
        if name in trials:
            trials[name]["judge"] = judging
    return trials


def arm_of(name):
    return name[0]


def index_of(name):
    return int(name[1:])


def collect(trials):
    """Metric values by metric, arm and trial index."""
    table = {}
    for key, label, direction, accessor in METRICS:
        row = {}
        for name, trial in sorted(trials.items()):
            try:
                value = accessor(trial)
            except (TypeError, KeyError, ValueError):
                value = None
            row.setdefault(arm_of(name), {})[index_of(name)] = value
        table[key] = {"label": label, "direction": direction, "values": row}
    return table


def contrasts(table, seed):
    """The paired differences, their intervals and their verdicts."""
    results = {}
    for key, entry in table.items():
        per_contrast = {}
        for treatment, baseline in CONTRASTS:
            left = entry["values"].get(treatment, {})
            right = entry["values"].get(baseline, {})
            pairs = []
            for index in sorted(set(left) & set(right)):
                if left[index] is None or right[index] is None:
                    continue
                pairs.append(left[index] - right[index])
            label = "%s-%s" % (treatment, baseline)
            if not pairs:
                per_contrast[label] = {
                    "pairs": [], "mean": None,
                    "interval": {"low": None, "high": None,
                                 "method": "no complete pair was measured"},
                    "verdict": "not computed", "non_inferior": None}
                continue
            interval = bca_interval(pairs, seed)
            per_contrast[label] = {
                "pairs": pairs,
                "mean": round(statistics.fmean(pairs), 4),
                "interval": interval,
                "verdict": verdict(interval, entry["direction"]),
                "non_inferior": non_inferior(key, interval, entry["direction"]),
            }
        results[key] = per_contrast
    return results


def number(value):
    """One rendering of a number, so the tables line up."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value == int(value):
            return "%d" % int(value)
        return "%.3f" % value if abs(value) < 1000 else "%.1f" % value
    return str(value)


def judge_agreement(root, trials):
    """Agreement between the judge and the owner's holdout, where it exists.

    Reported as the share of scores the judge lands on or within one point of,
    never as a correlation: nine non-independent points do not support a
    coefficient.
    """
    sheet = os.path.join(root, "judge", "holdout-scores.json")
    if not os.path.exists(sheet):
        return {"status": "unvalidated: no holdout scores have been recorded"}
    with io.open(sheet, encoding="utf-8") as handle:
        human = json.load(handle)
    exact_or_adjacent, total, disagreements = 0, 0, []
    for blind, scores in sorted(human.items()):
        trial = next((t for t in trials.values()
                      if path(t, "judge", "blind_id") == blind), None)
        if trial is None:
            continue
        for dimension, given in sorted(scores.items()):
            key = "judge_%s" % dimension
            model = judge_score(trial, dimension)
            if model is None or given is None:
                continue
            total += 1
            gap = abs(model - given)
            if gap <= 1:
                exact_or_adjacent += 1
            if gap >= 2:
                disagreements.append([blind, dimension, given, model, key])
    if not total:
        return {"status": "unvalidated: no holdout score matched a judging"}
    return {"status": "validated" if not disagreements else
            "unvalidated: the judge differs by two or more on a primary "
            "dimension",
            "share": round(exact_or_adjacent / total, 3),
            "scores": total, "disagreements": disagreements}


def generation_record(root):
    """Arm B's generation record, which carries its brief and token scan."""
    found = sorted(glob.glob(os.path.join(root, "arm-b-generation-*.json")))
    if not found:
        return None
    with io.open(found[-1], encoding="utf-8") as handle:
        return json.load(handle)


def write_report(root, trials, table, results, seed, agreement,
                 out_dir=AUDITS):
    """The report the design names, under `docs/audits/`.

    The directory is an argument so a shakedown of the writer can render into
    a scratch directory. A fabricated run must not be able to leave a file
    among the real audits, where its date alone would read as a result.
    """
    names = sorted(trials)
    arms = sorted({arm_of(name) for name in names})
    k = max((index_of(name) for name in names), default=0)
    any_scores = trials[names[0]]["scores"] if names else {}
    generation = generation_record(root)

    lines = []
    lines.append("# Efficacy benchmark — %s"
                 % datetime.date.today().isoformat())
    lines.append("")
    lines.append("Does a generated context file improve the result? The "
                 "question, the verdict rule and the metric directions were "
                 "fixed before any trial ran, in "
                 "`docs/design/efficacy-benchmark.md`.")
    lines.append("")
    lines.append("**Every interval below is descriptive.** At K = %d no "
                 "arrangement of paired differences reaches conventional "
                 "significance, which the design states and this report "
                 "repeats rather than footnotes." % k)
    lines.append("")

    lines.append("## What produced these numbers")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| Trials | %d, arms %s, K = %d |"
                 % (len(names), ", ".join(arms), k))
    lines.append("| Generator | `%s` |" % any_scores.get("model", "unknown"))
    judgings = [t["judge"] for t in trials.values() if t["judge"]]
    if judgings:
        lines.append("| Judge | `%s` at effort `%s`, %s |"
                     % (judgings[0].get("model"), judgings[0].get("effort"),
                        judgings[0].get("cli")))
        lines.append("| Blinding | condition markers stripped, order shuffled "
                     "at seed %s |" % judgings[0].get("seed"))
    else:
        lines.append("| Judge | not run |")
    lines.append("| Templates revision | `%s` |"
                 % any_scores.get("templates_tree", "unknown"))
    lines.append("| Hidden suite | `%s` |"
                 % any_scores.get("suite_revision", "unknown"))
    lines.append("| Bootstrap | %d resamples, %d%%, seed %s |"
                 % (RESAMPLES, int(100 * CONFIDENCE), seed))
    if generation:
        lines.append("| Arm B's file | generated %s, %s lines, leak scan: %s |"
                     % (generation.get("started_at", "unknown"),
                        generation.get("output_lines", "?"),
                        "clean" if not (generation.get("output_leak") or {})
                        .get("hits") else "HITS"))
    else:
        lines.append("| Arm B's file | generation record not in this run "
                     "root |")
    lines.append("")

    lines.append("## Primary dimensions")
    lines.append("")
    lines.append("The report leads with these three, owner-declared in the "
                 "design. Task success and cost follow.")
    lines.append("")
    lines.extend(contrast_table(table, results, PRIMARY))
    lines.append("")

    lines.append("## Task success, adherence and cost")
    lines.append("")
    lines.extend(contrast_table(table, results,
                                ("task_success", "install", "adherence",
                                 "output_tokens", "turns", "wall_seconds",
                                 "cost_usd")))
    lines.append("")

    lines.append("## Every other metric")
    lines.append("")
    rest = [key for key, _, _, _ in METRICS
            if key not in PRIMARY and key not in
            ("task_success", "install", "adherence", "output_tokens", "turns",
             "wall_seconds", "cost_usd")]
    lines.extend(contrast_table(table, results, rest))
    lines.append("")

    lines.append("## Raw numbers, per trial")
    lines.append("")
    lines.append("| Metric | %s |" % " | ".join(names))
    lines.append("|---|%s" % ("---|" * len(names)))
    for key, label, direction, _ in METRICS:
        row = table[key]["values"]
        cells = [number(row.get(arm_of(name), {}).get(index_of(name)))
                 for name in names]
        lines.append("| %s | %s |" % (label, " | ".join(cells)))
    lines.append("")

    lines.append("## Trials, and what was measured on them")
    lines.append("")
    lines.append("| Trial | Outcome | Metrics flagged as not measured |")
    lines.append("|---|---|---|")
    for name in names:
        scores = trials[name]["scores"]
        flagged = scores.get("flagged") or []
        lines.append("| %s | %s | %s |"
                     % (name,
                        (scores.get("cost") or {}).get("value", {})
                        .get("outcome", "unknown")
                        if (scores.get("cost") or {}).get("value") else
                        "no cost record",
                        ", ".join(flagged) if flagged else "none"))
    lines.append("")

    lines.append("## The judge, and whether anyone checked it")
    lines.append("")
    lines.append("| Trial | Blind id | Evidence lines found in the tree |")
    lines.append("|---|---|---|")
    for name in names:
        judging = trials[name]["judge"]
        if not judging:
            lines.append("| %s | — | not judged |" % name)
            continue
        share = path(judging, "evidence", "share")
        lines.append("| %s | %s | %s |"
                     % (name, judging.get("blind_id"),
                        "%.0f%%" % (100 * share) if share is not None
                        else "—"))
    lines.append("")
    lines.append("Holdout: %s" % agreement.get("status"))
    if agreement.get("share") is not None:
        lines.append("")
        lines.append("The judge landed on the owner's number or within one "
                     "point of it on %.0f%% of %d scores."
                     % (100 * agreement["share"], agreement["scores"]))
    lines.append("")

    lines.append("## Verdict vector")
    lines.append("")
    lines.append("The whole vector, as the design requires: no single "
                 "headline number.")
    lines.append("")
    lines.append("| Metric | B−A | C−A | B−C |")
    lines.append("|---|---|---|---|")
    for key, label, direction, _ in METRICS:
        cells = [results[key]["%s-%s" % pair]["verdict"] for pair in CONTRASTS]
        lines.append("| %s | %s |" % (label, " | ".join(cells)))
    lines.append("")

    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "%s-efficacy.md"
                          % datetime.date.today().isoformat())
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return target


def contrast_cell(contrast):
    """One contrast, as the mean, its interval, its verdict and its method.

    All three contrasts are printed for every metric, because B − C is the one
    an adopter asks and a table showing only B − A cannot answer it: a large
    B − A beside an equally large C − A is not a result for the templates.

    A method other than BCa is marked in the cell rather than left to a
    companion file. Three identical paired differences give a point mass, and
    an interval of zero width printed as though it were computed would be the
    most confident-looking row in the report and the least informative.
    """
    interval = contrast["interval"]
    if interval.get("low") is None:
        return interval.get("method")
    body = "%s (%s, %s)" % (number(contrast["mean"]),
                            number(interval["low"]),
                            number(interval["high"]))
    method = interval.get("method") or ""
    if not method.startswith("BCa"):
        body += " ‡"
    verdict_text = contrast["verdict"]
    inferiority = contrast.get("non_inferior")
    if inferiority and verdict_text == "no improvement shown":
        verdict_text += (", preserved within %s" % inferiority["margin"]
                         if inferiority["within"] else
                         ", not preserved within %s" % inferiority["margin"])
    return "%s — %s" % (body, verdict_text)


def contrast_table(table, results, keys):
    """One table of contrasts: every metric against all three comparisons."""
    lines = ["| Metric | Direction | A | B | C | B−A | C−A | B−C |",
             "|---|---|---|---|---|---|---|---|"]
    degenerate = False
    for key in keys:
        entry = table[key]
        means = {}
        for arm in ("A", "B", "C"):
            values = [v for v in entry["values"].get(arm, {}).values()
                      if v is not None]
            means[arm] = statistics.fmean(values) if values else None
        cells = []
        for treatment, baseline in CONTRASTS:
            contrast = results[key]["%s-%s" % (treatment, baseline)]
            cell = contrast_cell(contrast)
            degenerate = degenerate or "‡" in cell
            cells.append(cell)
        lines.append("| %s | %s | %s | %s | %s | %s |"
                     % (entry["label"], entry["direction"], number(means["A"]),
                        number(means["B"]), number(means["C"]),
                        " | ".join(cells)))
    if degenerate:
        lines.append("")
        lines.append("‡ the interval was not computed by BCa: the paired "
                     "differences were identical, or the bias correction was "
                     "undefined. `aggregate.json` carries the method per row.")
    return lines


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Aggregate scored efficacy trials into the report.")
    parser.add_argument("--root", help="the harness's run root")
    parser.add_argument("--seed", type=int, default=20260912,
                        help="bootstrap seed, recorded in the report")
    parser.add_argument("--out-dir", default=AUDITS,
                        help="where the report is written; default is "
                             "docs/audits/")
    parser.add_argument("--self-test", action="store_true",
                        help="check the verdict rule against worked cases; "
                             "read no run")
    return parser.parse_args(argv)


# The design's own worked table, which is what the verdict rule has to
# reproduce. The third row is the one an earlier draft read wrongly: three
# differences that all improve cannot produce an interval containing zero,
# however much the raw columns overlap.
WORKED = (
    ("every pairing improves by the same amount", [0.33, 0.33, 0.34], UP,
     "better"),
    ("every pairing improves, unstably", [0.03, 0.10, 0.12], UP, "better"),
    ("the differences change sign", [0.13, -0.06, 0.04], UP,
     "no improvement shown"),
    ("a downward metric that fell", [-12.0, -9.0, -20.0], DOWN, "better"),
    ("a downward metric that rose", [12.0, 9.0, 20.0], DOWN, "worse"),
    ("three identical differences", [0.2, 0.2, 0.2], UP, "better"),
)


def self_test(seed):
    """Check the verdict rule against the design's worked cases."""
    checks = []
    for label, differences, direction, expected in WORKED:
        interval = bca_interval(list(differences), seed)
        got = verdict(interval, direction)
        checks.append(("%s -> %s" % (label, expected), got == expected, got))
    for label, ok, got in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED, got %r" % got))
    passed = sum(1 for _, ok, _ in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d verdict-rule checks passed"
                      % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test(options.seed)
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    trials = load(options.root)
    if not trials:
        print("no scores under %s; score.py writes them" % options.root)
        return 2
    table = collect(trials)
    results = contrasts(table, options.seed)
    agreement = judge_agreement(options.root, trials)
    target = write_report(options.root, trials, table, results, options.seed,
                          agreement, options.out_dir)

    with io.open(os.path.join(options.root, "aggregate.json"), "w",
                 encoding="utf-8") as handle:
        json.dump({"seed": options.seed, "table": table, "results": results,
                   "agreement": agreement}, handle, indent=2, sort_keys=True)
    print("Report: %s" % target)
    judged = sum(1 for trial in trials.values() if trial["judge"])
    lib.print_verdict(True, "%d trial(s) aggregated, %d judged"
                      % (len(trials), judged))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
