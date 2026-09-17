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
import shutil
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
from generate_arm_b import RECORD as ARM_B_RECORD  # noqa: E402
from harness import (K_CEILING, K_PRIMARY, SCORABLE,  # noqa: E402
                     reach, read_transcripts, scoring_area)

HERE = os.path.dirname(os.path.abspath(__file__))
AUDITS = os.path.join(lib.ROOT, "docs", "audits")

# Metrics withdrawn after grading, each for the grader revision found to
# measure something other than the metric. Keyed by revision rather than by
# run, so every run that grader scored loses the metric and a corrected grader
# does not.
WITHDRAWN = os.path.join(HERE, "withdrawn.json")

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

# How a margin is measured: in the metric's own units, or as a share of the
# baseline arm's mean, so that it scales with the metric.
ABSOLUTE, RELATIVE = "absolute", "relative"

# The static-analysis counts reported per KLOC, which the design's section
# 1.2 holds to one relative margin between them.
STATIC_PER_KLOC = ("ruff_per_kloc", "unformatted_per_kloc", "mypy_per_kloc",
                   "bandit_per_kloc", "complexity_over_15_per_kloc",
                   "unused_per_kloc")

# The non-inferiority margins, for the claim that a metric was preserved
# rather than merely not shown to differ.
MARGINS = {
    "task_success": ("2 pp", 0.02, ABSOLUTE),
    "adherence": ("5 pp", 0.05, ABSOLUTE),
    "judge_design": ("0.3 points", 0.3, ABSOLUTE),
    "judge_readability": ("0.3 points", 0.3, ABSOLUTE),
    "judge_maintainability": ("0.3 points", 0.3, ABSOLUTE),
    "churn_files": ("15 % relative", 0.15, RELATIVE),
    "churn_lines": ("15 % relative", 0.15, RELATIVE),
}
MARGINS.update((key, ("10 % relative", 0.10, RELATIVE))
               for key in STATIC_PER_KLOC)

# The practical thresholds of the design's section 1.2 that can owe the one
# escalation to K = 5. Only a primary dimension triggers it, so no other
# metric's threshold is carried here, where something could come to read it.
PRACTICAL = {key: ("0.5 points", 0.5) for key in PRIMARY}


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


def per_kloc(trial, *keys):
    """A finding count per thousand source lines the tool actually saw."""
    count = metric_value(trial, *keys)
    lines = path(trial, "scores", keys[0], "seen", "lines")
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
    ("unformatted_per_kloc", "Files the formatter would change, per KLOC",
     DOWN, lambda t: per_kloc(t, "ruff_format")),
    ("mypy_errors", "Type errors under --strict", DOWN,
     lambda t: metric_value(t, "mypy")),
    ("mypy_per_kloc", "Type errors under --strict, per KLOC", DOWN,
     lambda t: per_kloc(t, "mypy")),
    ("bandit_serious", "Security findings, high and medium", DOWN,
     lambda t: metric_value(t, "bandit")),
    ("bandit_per_kloc", "Security findings, high and medium, per KLOC", DOWN,
     lambda t: per_kloc(t, "bandit")),
    ("complexity_max", "Highest cognitive complexity", DOWN,
     lambda t: metric_value(t, "complexity", "max")),
    ("complexity_over_15", "Functions over complexity 15", DOWN,
     lambda t: metric_value(t, "complexity", "over_15")),
    ("complexity_over_15_per_kloc", "Functions over complexity 15, per KLOC",
     DOWN, lambda t: per_kloc(t, "complexity", "over_15")),
    ("mean_cc", "Mean cyclomatic complexity", DOWN,
     lambda t: metric_value(t, "radon", "mean_cc")),
    ("min_mi", "Lowest maintainability index", NEUTRAL,
     lambda t: metric_value(t, "radon", "min_mi")),
    ("unused", "Unused names", DOWN, lambda t: metric_value(t, "unused")),
    ("unused_per_kloc", "Unused names per KLOC", DOWN,
     lambda t: per_kloc(t, "unused")),

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

    ("change_success", "Change task, acceptance pass rate", UP,
     lambda t: change_success(t)),
    ("change_regression", "Change task, build suite pass rate after it", UP,
     lambda t: change_value(t, "build_suite")),
    ("churn_files", "Change task, files touched", DOWN,
     lambda t: change_value(t, "churn", "files")),
    ("churn_lines", "Change task, lines changed", DOWN,
     lambda t: change_value(t, "churn", "lines")),
    ("change_cost_usd", "Change task, cost, USD", DOWN,
     lambda t: change_value(t, "cost", "cost_usd")),
)

# The change task's rows, in the order the report prints them.
CHANGE = ("change_success", "change_regression", "churn_files", "churn_lines",
          "change_cost_usd")


def security_value(trial, key):
    """A security check's value, or None where it was not taken."""
    return metric_value({"scores": trial.get("security") or {}}, key)


# Security checks declared after a run and before any trial was read for them.
# Their directions were declared with them. They are kept out of METRICS so no
# verdict, escalation or verdict-vector row can come from a check chosen after
# the results were seen.
POSTHOC = (
    ("security_secret_key", "Hard-coded secret keys", DOWN,
     lambda t: security_value(t, "secret_key")),
    ("security_debug", "Debug enabled", DOWN,
     lambda t: security_value(t, "debug")),
    ("security_sql_strings", "SQL statements built from strings", DOWN,
     lambda t: security_value(t, "sql_strings")),
    ("security_vulnerable", "Known vulnerabilities in installed dependencies",
     DOWN, lambda t: security_value(t, "vulnerable_dependencies")),
    ("security_cookies", "Session cookie flags set, of three", UP,
     lambda t: security_value(t, "cookie_flags")),
    ("security_headers", "Security headers on /, of four", UP,
     lambda t: security_value(t, "security_headers")),
    ("security_leaks", "Malformed requests answered with a stack trace, of "
     "five", DOWN, lambda t: security_value(t, "error_leakage")),
)


def change_value(trial, *keys):
    """A change-task metric's value, or None where it was not measured."""
    return metric_value({"scores": trial.get("change") or {}}, *keys)


def change_success(trial):
    """The change suite's pass rate, and zero where the changed tree broke."""
    rate = change_value(trial, "change_suite")
    if rate is not None:
        return rate
    if change_value(trial, "install") is False:
        return 0.0
    return None


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


def non_inferior(key, interval, direction, baseline_mean=None):
    """Whether a metric can be claimed preserved, not merely not-shown-worse.

    An interval containing zero is absence of evidence. The claim that nothing
    got worse needs the whole degradation side of the interval inside the
    margin the design fixes.
    """
    if key not in MARGINS:
        return None
    label, margin, kind = MARGINS[key]
    low, high = interval.get("low"), interval.get("high")
    if low is None or high is None:
        return None

    # A relative margin is a share of the baseline arm's mean. Without a
    # baseline, or against a zero one, there is nothing to take a share of.
    if kind == RELATIVE:
        if not baseline_mean:
            return None
        margin = margin * abs(baseline_mean)
    degradation = -low if direction == UP else high
    return {"margin": label, "within": degradation <= margin}


def load(root):
    """Every scored trial, with its judging attached where one exists."""
    area = scoring_area(root)
    trials = {}
    for file in sorted(glob.glob(os.path.join(area, "scores", "*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            scores = json.load(handle)
        trials[scores["name"]] = {"scores": scores, "judge": None,
                                  "change": None, "security": None}

    for file in sorted(glob.glob(os.path.join(area, "judge", "T*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            judging = json.load(handle)
        name = judging.get("trial")
        if name in trials:
            trials[name]["judge"] = judging

    # A change task sits beside its own build trial, so one whose build trial
    # was never scored has nothing to pair with and is left out.
    for file in sorted(glob.glob(os.path.join(area, "scores-change",
                                              "*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            change = json.load(handle)
        if change.get("name") in trials:
            trials[change["name"]]["change"] = change

    for file in sorted(glob.glob(os.path.join(area, "security-scores",
                                              "*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            security = json.load(handle)
        if security.get("name") in trials:
            trials[security["name"]]["security"] = security
    return trials


def arm_of(name):
    return name[0]


def index_of(name):
    return int(name[1:])


def collect(trials, metrics=METRICS):
    """Metric values by metric, arm and trial index."""
    table = {}
    for key, label, direction, accessor in metrics:
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
            observed = [value for value in right.values() if value is not None]
            per_contrast[label] = {
                "pairs": pairs,
                "mean": round(statistics.fmean(pairs), 4),
                "interval": interval,
                "verdict": verdict(interval, entry["direction"]),
                "non_inferior": non_inferior(
                    key, interval, entry["direction"],
                    statistics.fmean(observed) if observed else None),
            }
        results[key] = per_contrast
    return results


def withdrawals(trials, path=WITHDRAWN):
    """Each withdrawn metric whose grader revision scored any of these trials.

    One trial graded by the withdrawn revision withdraws the metric for the
    run, because the contrasts pair trials and a pair measured by two graders
    compares the graders.
    """
    if not os.path.exists(path):
        return {}
    with io.open(path, encoding="utf-8") as handle:
        records = json.load(handle)
    withdrawn = {}
    for record in records:
        part = "change" if record["metric"] in CHANGE else "scores"
        graded = {(trial.get(part) or {}).get("suite_revision")
                  for trial in trials.values()}
        if record["suite_revision"] in graded:
            withdrawn[record["metric"]] = record
    return withdrawn


def withdraw(withdrawn, table, *result_sets):
    """Blank each withdrawn metric's values, intervals and verdicts in place."""
    for key in withdrawn:

        # A number left in the raw table still reads as a result, so the
        # values go as well as the verdict.
        if key in table:
            table[key]["values"] = {arm: dict.fromkeys(row) for arm, row
                                    in table[key]["values"].items()}
        for results in result_sets:
            if key in results:
                results[key] = {"%s-%s" % pair: {
                    "pairs": [], "mean": None,
                    "interval": {"low": None, "high": None,
                                 "method": "withdrawn, see Withdrawn "
                                           "measurements"},
                    "verdict": "withdrawn", "non_inferior": None}
                    for pair in CONTRASTS}


def escalation_triggers(results):
    """The rows that owe the escalation to K = 5, in one set of contrasts.

    A row owes it where a primary dimension's interval contains zero while its
    mean paired difference exceeds that dimension's practical threshold.
    """
    triggers = []
    for key in PRIMARY:
        label, threshold = PRACTICAL[key]
        for treatment, baseline in CONTRASTS:
            name = "%s-%s" % (treatment, baseline)
            contrast = results[key][name]
            low = contrast["interval"].get("low")
            high = contrast["interval"].get("high")
            if low is None or high is None or not contrast["pairs"]:
                continue

            # Read by size in either direction, as the design's section 1.1
            # fixes: an escalation owed only to a favourable effect would lean
            # the stopping rule toward "better".
            effect = statistics.fmean(contrast["pairs"])
            if low <= 0 <= high and abs(effect) > threshold:
                triggers.append({"metric": key, "contrast": name,
                                 "mean": round(effect, 4), "low": low,
                                 "high": high, "threshold": label})
    return triggers


def assess_escalation(trials, results, seed, withdrawn=None):
    """Whether the escalation to K = 5 is owed, and whether it was run.

    A run past K = 3 is judged on its first three blocks alone, because that is
    the vector which had to owe the escalation. Their contrasts are kept, so
    the report prints the K = 3 vector beside the K = 5 one, with `withdrawn`
    blanked from them as it is from `results`.
    """
    k = max((index_of(name) for name in trials), default=0)
    if k < K_PRIMARY:
        return {"k": k, "state": "not assessed", "owed": None, "triggers": []}
    if k == K_PRIMARY:
        triggers = escalation_triggers(results)
        return {"k": k, "state": "assessed", "owed": bool(triggers),
                "triggers": triggers}
    first = {name: trial for name, trial in trials.items()
             if index_of(name) <= K_PRIMARY}
    earlier = contrasts(collect(first), seed)
    withdraw(withdrawn or {}, {}, earlier)
    triggers = escalation_triggers(earlier)
    return {"k": k,
            "state": "escalated" if k == K_CEILING else "part-escalated",
            "owed": bool(triggers), "triggers": triggers,
            "results_k3": earlier}


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


def generation_record():
    """Arm B's generation record, committed beside the file it produced."""
    if not os.path.exists(ARM_B_RECORD):
        return None
    with io.open(ARM_B_RECORD, encoding="utf-8") as handle:
        return json.load(handle)


def run_records(root):
    """Every trial record in the root's run records, in time order."""
    sequence = []
    for file in sorted(glob.glob(os.path.join(root, "run-*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            sequence.extend(json.load(handle).get("trials", []))
    return sequence


def name_of(record):
    """A trial record's name, marking a change task apart from its build."""

    # A change task shares its build trial's name, so the task tells them
    # apart; a record written before tasks existed is a build trial.
    name = "%s%s" % (record.get("arm"), record.get("trial"))
    if record.get("task", "build") == "change":
        name += " (change task)"
    return name


def started(record):
    """When a trial record's trial started, as a timestamp, or None."""

    # Recorded to the second and before the CLI launched, so it never falls
    # after a transcript the trial itself wrote.
    try:
        moment = datetime.datetime.fromisoformat(record["started_at"])
    except (KeyError, TypeError, ValueError):
        return None
    return moment.timestamp()


def reaches(root):
    """Every scorable trial's transcript scan, as name and hits.

    Scanned here under the current rule wherever the run root still holds the
    transcripts, so a record scanned under an earlier, narrower rule is read
    again. A trial whose transcripts are gone keeps its record's own scan.
    """
    home = os.path.join(root, "home")
    scans = []
    for record in run_records(root):
        if record.get("outcome") not in SCORABLE:
            continue
        workspace = record.get("workspace") or ""
        files, calls = read_transcripts(home, workspace, started(record))
        if files:
            scan = reach(files, calls, workspace, record.get("temp"))
        else:
            scan = record.get("reach") or reach(files, calls)
        scans.append({"name": name_of(record), "hits": scan["hits"]})
    return scans


def reach_section(root):
    """The report's lines naming every trial that reached past its own
    workspace."""
    lines = ["## Trials that reached past their own workspace",
             "",
             "The shell keeps its network and the file system is not fenced, "
             "so a trial could fetch this repository or read the hidden "
             "suite, the scoring area, or another trial's workspace, tarball "
             "or transcript. Every transcript is scanned for a tool call "
             "naming any of them.",
             ""]
    scans = reaches(root)
    flagged = [scan for scan in scans if scan["hits"]]
    if flagged:
        lines.append("| Trial | Tool | Names | Call |")
        lines.append("|---|---|---|---|")
        for scan in flagged:
            for hit in scan["hits"]:
                call = " ".join(hit["call"].split()).replace("|", "/")
                lines.append("| %s | %s | `%s` | %s |"
                             % (scan["name"], hit["tool"], hit["term"],
                                call[:160]))
    else:
        lines.append("None: no scanned transcript names any of them.")
    unscanned = [scan["name"] for scan in scans if scan["hits"] is None]
    if unscanned:
        lines.append("")
        lines.append("Not scanned, having no transcript: %s."
                     % ", ".join(unscanned))
    return lines


def lost_trials(root):
    """Every trial the harness voided, with the outcome of what replaced it."""

    # Every run record in time order, because a voided trial is re-run either
    # in its place or by a later run started `--from` it.
    sequence = run_records(root)

    lost = []
    for index, record in enumerate(sequence):
        if record.get("outcome") != "blocked":
            continue
        later = next((other for other in sequence[index + 1:]
                      if name_of(other) == name_of(record)), None)
        lost.append({"name": name_of(record),
                     "started_at": record.get("started_at"),
                     "reason": record.get("reason"),
                     "kept": path(record, "void", "dir"),
                     "rerun": later.get("outcome") if later else None})
    return lost


def write_report(root, trials, table, results, seed, escalation,
                 out_dir=AUDITS, posthoc=None, withdrawn=None):
    """The report the design names, under `docs/audits/`.

    The directory is an argument so a shakedown of the writer can render into
    a scratch directory. A fabricated run must not be able to leave a file
    among the real audits, where its date alone would read as a result.
    `posthoc` is the table and contrasts of the checks declared after the
    run, printed in their own section and nowhere else. `withdrawn` maps each
    withdrawn metric to its record, already blanked from `table` and `results`.
    """
    names = sorted(trials)
    arms = sorted({arm_of(name) for name in names})
    k = max((index_of(name) for name in names), default=0)
    any_scores = trials[names[0]]["scores"] if names else {}
    generation = generation_record()

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
        lines.append("| Arm B's file | no generation record beside it |")
    lines.append("")

    if withdrawn:
        lines.extend(withdrawn_section(withdrawn))
        lines.append("")

    lines.append("## Primary dimensions")
    lines.append("")
    lines.append("The report leads with these three, owner-declared in the "
                 "design. Task success and cost follow.")
    lines.append("")
    lines.extend(contrast_table(table, results, PRIMARY))
    lines.append("")

    lines.extend(escalation_section(escalation))
    lines.append("")

    lines.append("## Task success, adherence and cost")
    lines.append("")
    lines.extend(contrast_table(table, results,
                                ("task_success", "install", "adherence",
                                 "output_tokens", "turns", "wall_seconds",
                                 "cost_usd")))
    lines.append("")

    lines.append("## The change task")
    lines.append("")
    lines.append("How far each design had to be disturbed to take a change it "
                 "was not built for, read beside whether the change works and "
                 "whether the build still passes after it.")
    lines.append("")
    lines.extend(contrast_table(table, results, CHANGE))
    lines.append("")

    lines.append("## Every other metric")
    lines.append("")
    rest = [key for key, _, _, _ in METRICS
            if key not in PRIMARY and key not in CHANGE and key not in
            ("task_success", "install", "adherence", "output_tokens", "turns",
             "wall_seconds", "cost_usd")]
    lines.extend(contrast_table(table, results, rest))
    lines.append("")

    if posthoc:
        lines.extend(posthoc_section(*posthoc))
        lines.append("")

    lines.append("## Raw numbers, per trial")
    lines.append("")
    lines.append("| Metric | %s |" % " | ".join(names))
    lines.append("|---|%s" % ("---|" * len(names)))
    raw = [(table, METRICS)] + ([(posthoc[0], POSTHOC)] if posthoc else [])
    for source, metrics in raw:
        for key, label, direction, _ in metrics:
            row = source[key]["values"]
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

    lines.append("## Trials lost to the provider or the harness")
    lines.append("")
    lost = lost_trials(root)
    if not lost:
        lines.append("None: no trial was voided.")
    else:
        lines.append("Each was voided and re-run once in its own place, as "
                     "the design's failure handling fixes. A voided "
                     "workspace is kept and never scored.")
        lines.append("")
        lines.append("| Trial | Started | Why | Kept at | Re-run |")
        lines.append("|---|---|---|---|---|")
        for entry in lost:
            reason = " ".join((entry["reason"] or "—").split())
            lines.append("| %s | %s | %s | %s | %s |"
                         % (entry["name"], entry["started_at"] or "—",
                            reason.replace("|", "/")[:160],
                            "`%s`" % entry["kept"] if entry["kept"]
                            else "not moved",
                            entry["rerun"] or "not re-run"))
    lines.append("")

    lines.extend(reach_section(root))
    lines.append("")

    lines.append("## The judge, and how it is checked")
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
    lines.append("No person scores the judge. Each score it gives quotes an "
                 "evidence line, and the share of those lines found in the "
                 "tree they were quoted from is the only check on it.")
    lines.append("")

    lines.append("## Verdict vector")
    lines.append("")
    lines.append("The whole vector, as the design requires: no single "
                 "headline number.")
    lines.append("")

    # A run that escalated reports both vectors, as the design requires, so
    # each contrast at K = 5 sits beside the same contrast over the first
    # three blocks rather than in a second table a reader has to line up.
    earlier = escalation.get("results_k3")
    header = []
    for treatment, baseline in CONTRASTS:
        column = "%s−%s" % (treatment, baseline)
        header.extend(["%s, K = %d" % (column, K_PRIMARY),
                       "%s, K = %d" % (column, k)] if earlier else [column])
    lines.append("| Metric | %s |" % " | ".join(header))
    lines.append("|---|%s" % ("---|" * len(header)))
    for key, label, direction, _ in METRICS:
        cells = []
        for pair in CONTRASTS:
            name = "%s-%s" % pair
            if earlier:
                cells.append(earlier[key][name]["verdict"])
            cells.append(results[key][name]["verdict"])
        lines.append("| %s | %s |" % (label, " | ".join(cells)))
    lines.append("")

    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "%s-efficacy.md"
                          % datetime.date.today().isoformat())
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return target


def posthoc_section(table, results):
    """The report's lines on the security checks declared after the run."""
    lines = ["## Security, read with checks declared after the results",
             "",
             "The run's own security checks passed on every trial and "
             "separated nothing. These were declared after the run and before "
             "any trial was read for them, so each row gives the means and the "
             "interval and no verdict, and none of them reaches the verdict "
             "vector or the escalation.",
             ""]
    lines.extend(contrast_table(table, results,
                                [key for key, _, _, _ in POSTHOC],
                                verdicts=False))
    return lines


def withdrawn_section(withdrawn):
    """The report's lines on each metric withdrawn from this run, and why."""
    labels = {key: label for key, label, _, _ in METRICS}
    lines = ["## Withdrawn measurements",
             "",
             "Each metric below was found, after grading, to measure something "
             "other than what it names on the grader revision given. It prints "
             "no number, interval or verdict anywhere in this report.",
             "",
             "| Metric | Grader revision | Decided | Why |",
             "|---|---|---|---|"]
    for key, record in sorted(withdrawn.items()):
        lines.append("| %s | `%s` | %s | %s |"
                     % (labels.get(key, key), record["suite_revision"][:12],
                        record.get("decided") or "—",
                        " ".join((record.get("reason") or "—").split())
                        .replace("|", "/")))
    return lines


def escalation_section(escalation):
    """The report's lines on the one escalation to K = 5 the design permits."""
    k = escalation["k"]
    lines = ["## The escalation to K = %d" % K_CEILING,
             "",
             "Fixed before the run: one escalation is owed where a primary "
             "dimension's interval contains zero while its mean paired "
             "difference exceeds 0.5 points in either direction, on any "
             "contrast. K never exceeds %d." % K_CEILING,
             ""]
    state, owed = escalation["state"], escalation["owed"]
    if state == "not assessed":
        lines.append("Not assessed: the run holds K = %d, and the rule reads "
                     "K = %d." % (k, K_PRIMARY))
        return lines
    if state == "assessed" and owed:
        lines.append("**Owed.** Run blocks %d to %d with `--k %d --from A%d`, "
                     "then report again. A row still containing zero at K = "
                     "%d is reported as no improvement shown."
                     % (K_PRIMARY + 1, K_CEILING, K_CEILING, K_PRIMARY + 1,
                        K_CEILING))
    elif state == "assessed":
        lines.append("**Not owed.** No primary dimension's row meets the "
                     "rule, so K stays %d." % K_PRIMARY)
    elif not owed:
        lines.append("**Run without a trigger.** The first %d blocks owed no "
                     "escalation, so every block past them was sampled outside "
                     "the design's rule. Read the K = %d vector; the K = %d "
                     "rows are not evidence." % (K_PRIMARY, K_PRIMARY, k))
    elif state == "part-escalated":
        lines.append("**Part-run.** The first %d blocks owed it and the run "
                     "holds K = %d, so block %d is still owed before the K = "
                     "%d vector is read." % (K_PRIMARY, k, K_CEILING,
                                             K_CEILING))
    else:
        lines.append("**Run.** The first %d blocks owed it, on the rows "
                     "below. No further escalation is permitted: a row still "
                     "containing zero at K = %d is reported as no improvement "
                     "shown." % (K_PRIMARY, K_CEILING))
    if escalation["triggers"]:
        labels = {key: label for key, label, _, _ in METRICS}
        lines.append("")
        lines.append("| Metric | Contrast | Mean difference | Interval "
                     "| Threshold |")
        lines.append("|---|---|---|---|---|")
        for row in escalation["triggers"]:
            lines.append("| %s | %s | %s | (%s, %s) | %s |"
                         % (labels[row["metric"]],
                            row["contrast"].replace("-", "−"),
                            number(row["mean"]), number(row["low"]),
                            number(row["high"]), row["threshold"]))
    return lines


def contrast_cell(contrast, verdicts=True):
    """One contrast, as the mean, its interval, its verdict and its method.

    Without `verdicts` the cell stops at the interval, for a row that may
    describe a run but not decide it.

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
    if not verdicts:
        return body
    verdict_text = contrast["verdict"]
    inferiority = contrast.get("non_inferior")
    if inferiority and verdict_text == "no improvement shown":
        verdict_text += (", preserved within %s" % inferiority["margin"]
                         if inferiority["within"] else
                         ", not preserved within %s" % inferiority["margin"])
    return "%s — %s" % (body, verdict_text)


def contrast_table(table, results, keys, verdicts=True):
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
            cell = contrast_cell(contrast, verdicts)
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


def reach_checks():
    """The report names a trial whose scan hit, and no other."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-reach-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    hit = {"tool": "Bash", "term": "solid-ai-templates",
           "call": "curl https://github.com/braboj/solid-ai-templates"}
    planted = [
        {"arm": "B", "trial": 1, "outcome": "completed",
         "reach": {"transcripts": ["planted"], "hits": [hit]}},
        {"arm": "A", "trial": 1, "outcome": "completed",
         "reach": {"transcripts": ["planted"], "hits": []}},
        {"arm": "C", "trial": 1, "outcome": "completed",
         "workspace": os.path.join(scratch, "C1")},
        {"arm": "A", "trial": 2, "outcome": "blocked",
         "reach": {"transcripts": ["planted"], "hits": [hit]}},
    ]
    with io.open(os.path.join(scratch, "run-planted.json"), "w",
                 encoding="utf-8") as handle:
        json.dump({"trials": planted}, handle)

    lines = reach_section(scratch)
    rows = [line for line in lines
            if line.startswith("| ") and not line.startswith("| Trial")]
    checks = [("the planted run record is read",
               len(run_records(scratch)) == len(planted)),
              ("a trial whose scan hit is named",
               [row.split(" | ")[0] for row in rows] == ["| B1"]),
              ("a trial with no transcript is not scanned",
               "Not scanned, having no transcript: C1." in lines)]
    shutil.rmtree(scratch, ignore_errors=True)
    return checks


def rescan_checks():
    """A record scanned under an earlier rule is read again from its
    transcript."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-rescan-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    workspace = os.path.join(scratch, "A2")
    os.makedirs(workspace)
    os.makedirs(os.path.join(scratch, "B1"))
    folder = "".join(char if char.isalnum() else "-"
                     for char in os.path.abspath(workspace))
    projects = os.path.join(scratch, "home", ".claude", "projects", folder)
    os.makedirs(projects)
    entry = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash",
         "input": {"command": "cat ../B1/src/tariff/pricing.py"}}]}}
    with io.open(os.path.join(projects, "planted.jsonl"), "w",
                 encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

    # Scanned clean when it ran, as the narrower rule would have left it.
    planted = [{"arm": "A", "trial": 2, "outcome": "completed",
                "workspace": workspace,
                "reach": {"transcripts": ["planted"], "hits": []}}]
    with io.open(os.path.join(scratch, "run-planted.json"), "w",
                 encoding="utf-8") as handle:
        json.dump({"trials": planted}, handle)

    # The plant landed: the transcript is found and carries the one call.
    landed = len(read_transcripts(os.path.join(scratch, "home"),
                                  workspace)[1]) == 1
    terms = [hit["term"] for scan in reaches(scratch)
             for hit in scan["hits"] or []]
    shutil.rmtree(scratch, ignore_errors=True)
    return [("the planted transcript carries one call", landed),
            ("its record's clean scan is read again and flagged",
             terms == ["../b1"])]


# One row on each side of the escalation rule. The interval is planted beside
# its pairs, so each case turns on the rule rather than on the bootstrap.
ESCALATING = (
    ("a crossing interval with an effect of 0.67 owes it", "judge_design",
     "B-A", [2.0, -1.0, 1.0], -1.0, 2.0, True),
    ("the same row on C-A owes it", "judge_readability", "C-A",
     [2.0, -1.0, 1.0], -1.0, 2.0, True),
    ("an effect of 0.67 the other way owes it", "judge_maintainability",
     "B-C", [-2.0, 1.0, -1.0], -2.0, 1.0, True),
    ("an effect of exactly 0.5 does not", "judge_design", "B-A",
     [1.5, -1.0, 1.0], -1.0, 1.5, False),
    ("an interval clear of zero does not", "judge_design", "B-A",
     [1.0, 1.0, 1.0], 1.0, 1.0, False),
    ("a row outside the primary dimensions does not", "task_success", "B-A",
     [2.0, -1.0, 1.0], -1.0, 2.0, False),
    ("an interval not computed does not", "judge_design", "B-A", [2.0],
     None, None, False),
)


def planted_results(key, name, pairs, low, high):
    """Contrasts with one planted row, every other row measured nothing."""
    results = {metric: {"%s-%s" % pair: {"pairs": [],
                                         "interval": {"low": None,
                                                      "high": None}}
                        for pair in CONTRASTS}
               for metric, _, _, _ in METRICS}
    results[key][name] = {"pairs": pairs,
                          "interval": {"low": low, "high": high}}
    return results


def escalation_checks(seed):
    """The escalation rule on planted rows, and a planted K = 5 run rendered."""
    checks = []
    for label, key, name, pairs, low, high, expected in ESCALATING:
        triggers = escalation_triggers(planted_results(key, name, pairs, low,
                                                       high))
        checks.append((label, bool(triggers) == expected, triggers))

    # Five blocks of judged trials. The first three alone must decide the
    # escalation, and the report must print their vector beside the fifth's.
    design = {"A": [3, 3, 3, 3, 3], "B": [5, 2, 4, 4, 4], "C": [3, 3, 3, 3, 3]}
    trials = {"%s%d" % (arm, index): {
        "scores": {}, "change": None,
        "judge": {"answer": {"rubric": {"design": {"score": score}}}}}
        for arm, scores in design.items()
        for index, score in enumerate(scores, 1)}
    table = collect(trials)
    results = contrasts(table, seed)
    escalation = assess_escalation(trials, results, seed)
    earlier = escalation.get("results_k3") or {}
    checks.append(("a K = 5 run is judged on its first three blocks",
                   escalation["state"] == "escalated"
                   and len(path(earlier, "judge_design", "B-A", "pairs")
                           or []) == K_PRIMARY
                   and len(results["judge_design"]["B-A"]["pairs"])
                   == K_CEILING, escalation["state"]))

    first = {name: trial for name, trial in trials.items()
             if index_of(name) <= K_PRIMARY}
    state = assess_escalation(first, contrasts(collect(first), seed),
                              seed)["state"]
    checks.append(("a K = 3 run is assessed on its own vector",
                   state == "assessed", state))

    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-escalation-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    target = write_report(scratch, trials, table, results, seed,
                          escalation, out_dir=scratch)
    with io.open(target, encoding="utf-8") as handle:
        text = handle.read()
    shutil.rmtree(scratch, ignore_errors=True)
    checks.append(("the report carries the escalation section",
                   "## The escalation to K = 5" in text, None))
    checks.append(("an escalated report prints both vectors",
                   "| Metric | B−A, K = 3 | B−A, K = 5 |" in text, None))
    checks.append(("the judge is checked by its evidence, not a person",
                   "No person scores the judge." in text
                   and "holdout" not in text.lower(), None))
    return checks


def posthoc_checks(seed):
    """Checks declared after a run are printed, and decide nothing."""
    keys = {key for key, _, _, _ in POSTHOC}
    checks = [("no after-the-results check is a verdict metric",
               not keys & {key for key, _, _, _ in METRICS}, sorted(keys))]

    # Arm B sets every header on every trial and arm A none, so the row would
    # read "better" if a verdict were ever computed for it.
    headers = {"A": 0, "B": 4, "C": 2}
    trials = {"%s%d" % (arm, index): {
        "scores": {}, "change": None, "judge": None,
        "security": {"security_headers": {"value": value, "missing": None}}}
        for arm, value in headers.items() for index in range(1, K_PRIMARY + 1)}
    table = collect(trials)
    results = contrasts(table, seed)
    posthoc_table = collect(trials, POSTHOC)
    posthoc = (posthoc_table, contrasts(posthoc_table, seed))
    checks.append(("the planted row would read better",
                   posthoc[1]["security_headers"]["B-A"]["verdict"]
                   == "better", posthoc[1]["security_headers"]["B-A"]))

    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-posthoc-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    target = write_report(scratch, trials, table, results, seed,
                          assess_escalation(trials, results, seed),
                          out_dir=scratch, posthoc=posthoc)
    with io.open(target, encoding="utf-8") as handle:
        text = handle.read()
    shutil.rmtree(scratch, ignore_errors=True)

    label = "Security headers on /, of four"
    heading = "## Security, read with checks declared after the results"
    section = text.split(heading)[1].split("\n## ")[0] if heading in text \
        else ""
    row = [line for line in section.splitlines() if line.startswith(
        "| " + label)]
    vector = text.split("## Verdict vector")[-1]
    checks.append(("the report prints the section", bool(row), None))
    checks.append(("its row carries no verdict",
                   bool(row) and not any(word in row[0] for word in
                                         ("better", "worse", "improvement")),
                   row))
    checks.append(("its row is not in the verdict vector",
                   label not in vector, None))
    return checks


def planted_change_run(revision):
    """K = 3 change tasks graded at `revision`, arm B ahead on every row."""
    rates = {"A": 0.25, "B": 0.75, "C": 0.5}
    lines = {"A": 300, "B": 200, "C": 250}

    def change(arm, index):
        return {"suite_revision": revision,
                "change_suite": {"value": rates[arm] + index / 100.0,
                                 "missing": None},
                "churn": {"value": {"files": 10, "lines": lines[arm] - index},
                          "missing": None}}

    return {"%s%d" % (arm, index): {"scores": {}, "judge": None,
                                    "security": None,
                                    "change": change(arm, index)}
            for arm in rates for index in range(1, K_PRIMARY + 1)}


def rendered(trials, seed, withdrawn):
    """The report a planted run renders, withdrawn metrics blanked first."""
    table = collect(trials)
    results = contrasts(table, seed)
    before = results["change_success"]["B-A"]["verdict"]
    withdraw(withdrawn, table, results)
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-withdrawal-render")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    target = write_report(scratch, trials, table, results, seed,
                          assess_escalation(trials, results, seed, withdrawn),
                          out_dir=scratch, withdrawn=withdrawn)
    with io.open(target, encoding="utf-8") as handle:
        text = handle.read()
    shutil.rmtree(scratch, ignore_errors=True)
    return before, table, text


def section_rows(text, heading, label):
    """The rows of one report section that start with a metric's label."""
    section = text.split(heading)[1].split("\n## ")[0] if heading in text \
        else ""
    return [line for line in section.splitlines()
            if line.startswith("| %s |" % label)]


def withdrawal_checks(seed):
    """A withdrawn metric prints only its withdrawal, and only on runs graded
    by the revision it was withdrawn for."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-report-withdrawal-self-test")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch)
    record = os.path.join(scratch, "withdrawn.json")
    with io.open(record, "w", encoding="utf-8") as handle:
        json.dump([{"metric": "change_success",
                    "suite_revision": "planted-revision",
                    "decided": "2026-09-17", "reason": "planted reason"}],
                  handle)

    graded = planted_change_run("planted-revision")
    withdrawn = withdrawals(graded, record)
    other = planted_change_run("other-revision")
    spared = withdrawals(other, record)
    shutil.rmtree(scratch, ignore_errors=True)

    label = "Change task, acceptance pass rate"
    before, table, text = rendered(graded, seed, withdrawn)
    values = [value for row in table["change_success"]["values"].values()
              for value in row.values()]
    change = section_rows(text, "## The change task", label)
    raw = section_rows(text, "## Raw numbers, per trial", label)
    vector = section_rows(text, "## Verdict vector", label)
    listed = section_rows(text, "## Withdrawn measurements", label)
    churn = section_rows(text, "## The change task",
                         "Change task, lines changed")

    checks = [
        ("a record on the grading revision is read",
         sorted(withdrawn) == ["change_success"], sorted(withdrawn)),
        ("the planted row read better before withdrawal", before == "better",
         before),
        ("withdrawal blanks every value of the row",
         len(values) == 3 * K_PRIMARY
         and all(value is None for value in values), values),
        ("its change-task row prints no number or verdict",
         len(change) == 1 and "withdrawn" in change[0] and not any(
             word in change[0] for word in ("0.", "better", "worse")), change),
        ("its raw row prints no value",
         len(raw) == 1 and not any(char.isdigit() for char in raw[0]), raw),
        ("its verdict vector row reads withdrawn",
         vector == ["| %s | withdrawn | withdrawn | withdrawn |" % label],
         vector),
        ("the withdrawal section names it and why",
         len(listed) == 1 and "planted reason" in listed[0], listed),
        ("a metric not withdrawn keeps its verdict",
         len(churn) == 1 and "better" in churn[0], churn),
        ("a run graded by another revision withdraws nothing", spared == {},
         sorted(spared)),
    ]

    _, _, text = rendered(other, seed, spared)
    kept = section_rows(text, "## Verdict vector", label)
    checks.append(("that run's row keeps its verdict",
                   kept == ["| %s | better | better | better |" % label]
                   and "## Withdrawn measurements" not in text, kept))
    return checks


def self_test(seed):
    """Check the verdict rule, the relative margin, the escalation rule, the
    withdrawal of a metric and the reach section."""
    checks = []
    for label, differences, direction, expected in WORKED:
        interval = bca_interval(list(differences), seed)
        got = verdict(interval, direction)
        checks.append(("%s -> %s" % (label, expected), got == expected, got))

    # A relative margin is a share of the baseline arm's mean: 15 % of a
    # baseline of 100 lines admits 10 lines more churn and refuses 20, and
    # 10 % of 20 type errors per KLOC admits 1.5 more and refuses 3.
    margins = (
        ("10 more lines on 100 is preserved", "churn_lines",
         {"low": -5.0, "high": 10.0}, 100.0, True),
        ("20 more lines on 100 is not", "churn_lines",
         {"low": 5.0, "high": 20.0}, 100.0, False),
        ("no baseline makes no relative claim", "churn_lines",
         {"low": -5.0, "high": 10.0}, None, None),
        ("1.5 more per KLOC on 20 is preserved", "mypy_per_kloc",
         {"low": -1.0, "high": 1.5}, 20.0, True),
        ("3 more per KLOC on 20 is not", "mypy_per_kloc",
         {"low": 0.5, "high": 3.0}, 20.0, False),
    )
    for label, key, interval, baseline, expected in margins:
        answer = non_inferior(key, interval, DOWN, baseline)
        got = None if answer is None else answer["within"]
        checks.append((label, got == expected, got))

    # Every per-KLOC row is a static-analysis count, so each carries the one
    # margin section 1.2 gives them; a row added without it fails here.
    per_kloc_rows = {key for key, _, _, _ in METRICS
                     if key.endswith("_per_kloc")}
    covered = all(MARGINS.get(key, (None,))[0] == "10 % relative"
                  for key in per_kloc_rows)
    checks.append(("every per-KLOC row carries the static margin",
                   covered and per_kloc_rows == set(STATIC_PER_KLOC),
                   sorted(per_kloc_rows)))

    # A nested count divides by the lines its own tool saw.
    planted = {"scores": {"complexity": {"value": {"over_15": 3},
                                         "missing": None,
                                         "seen": {"lines": 1500}}}}
    got = per_kloc(planted, "complexity", "over_15")
    checks.append(("a nested count is taken per KLOC", got == 2.0, got))
    checks.extend(escalation_checks(seed))
    checks.extend(posthoc_checks(seed))
    checks.extend(withdrawal_checks(seed))
    checks.extend((label, ok, ok) for label, ok in reach_checks())
    checks.extend((label, ok, ok) for label, ok in rescan_checks())
    for label, ok, got in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED, got %r" % got))
    passed = sum(1 for _, ok, _ in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed"
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
        print("no scores under %s; score.py writes them"
              % scoring_area(options.root))
        return 2

    # The design escalates once, to K = 5, and never further, so a run past
    # the ceiling is refused rather than reported as though the bound held.
    k = max(index_of(name) for name in trials)
    if k > K_CEILING:
        print("refused: the run holds K = %d, past the design's ceiling of "
              "K = %d" % (k, K_CEILING))
        return 2
    table = collect(trials)
    results = contrasts(table, options.seed)
    withdrawn = withdrawals(trials)
    withdraw(withdrawn, table, results)
    escalation = assess_escalation(trials, results, options.seed, withdrawn)
    posthoc = None
    if any(trial["security"] for trial in trials.values()):
        posthoc_table = collect(trials, POSTHOC)
        posthoc = (posthoc_table, contrasts(posthoc_table, options.seed))
    target = write_report(options.root, trials, table, results, options.seed,
                          escalation, options.out_dir, posthoc,
                          withdrawn)

    with io.open(os.path.join(scoring_area(options.root), "aggregate.json"),
                 "w", encoding="utf-8") as handle:
        json.dump({"seed": options.seed, "table": table, "results": results,
                   "escalation": escalation,
                   "withdrawn": withdrawn,
                   "posthoc": {"table": posthoc[0], "results": posthoc[1]}
                   if posthoc else None},
                  handle, indent=2, sort_keys=True)
    print("Report: %s" % target)
    judged = sum(1 for trial in trials.values() if trial["judge"])
    lib.print_verdict(True, "%d trial(s) aggregated, %d judged"
                      % (len(trials), judged))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
