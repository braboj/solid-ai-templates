"""Bring an earlier round's trials into a run root, scored and judged as
they were.

Round 2 reuses round 1's `full` and `hand` trials rather than running them
again, as the design's section 12 fixes. This module copies what the report
reads for a trial — its run record, frozen tarball, transcripts, score,
judging and security reading — from the earlier root and scoring area into
the new ones, under the arm's word, and marks each copy with where it came
from. The earlier root is never touched, and nothing copied is scored or
judged again: the scorer, the judge and the security reader skip a trial
whose result is already there.
"""

import argparse
import datetime
import glob
import io
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
from harness import (ARMS, PROMPT, TrialError, arm_name,  # noqa: E402
                     assert_outside_repository, canonical, project_folder,
                     remove_tree, scorable_trials, scoring_area, spellings,
                     write_run)

# The scoring area's per-trial readings, each a JSON file named for the
# trial, that a reused trial brings with it.
READINGS = ("scores", "security-scores")


def existing_file(directory, name):
    """The JSON file a trial's reading is filed under, in either spelling."""
    for spelled in spellings(name):
        path = os.path.join(directory, "%s.json" % spelled)
        if os.path.isfile(path):
            return path
    return None


def select(source, arms):
    """The earlier root's scorable build trials of the given arms, by
    canonical name."""
    offered = scorable_trials(source, task="build")
    chosen = {name: record for name, record in offered.items()
              if arm_name(record.get("arm")) in arms}
    for arm in arms:
        if not any(arm_name(record.get("arm")) == arm
                   for record in chosen.values()):
            raise TrialError("no scorable build trial of arm %s in %s"
                             % (arm, source))
    return chosen


def copy_file(source, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copyfile(source, target)


def annotated(source, target, updates):
    """Copy a JSON reading, with its trial named as the target names it and
    its origin recorded."""
    with io.open(source, encoding="utf-8") as handle:
        data = json.load(handle)
    data.update(updates)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with io.open(target, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def judgings_of(area, name):
    """Every completed judging of a trial in a scoring area, by file."""
    found = {}
    for file in sorted(glob.glob(os.path.join(area, "judge", "T*.json"))):
        with io.open(file, encoding="utf-8") as handle:
            record = json.load(handle)
        try:
            same = canonical(record.get("trial") or "") == name
        except TrialError:
            same = False
        if same and record.get("outcome") == "judged":
            found[file] = record
    return found


def reuse_trial(name, record, source, target):
    """Copy one trial's artifacts into the target root and scoring area.

    Returns the run record to write for it and the blind label its judging
    carries, None where it was never judged.
    """
    tarball = (record.get("frozen") or {}).get("tarball")
    if not tarball or not os.path.isfile(tarball):
        raise TrialError("%s has no frozen tarball at %s" % (name, tarball))
    origin = {"root": os.path.abspath(source),
              "name": os.path.splitext(os.path.basename(tarball))[0],
              "tarball": tarball}

    copied = dict(record)
    copied["arm"] = arm_name(record.get("arm"))
    copied["reused_from"] = origin
    copied["frozen"] = dict(record["frozen"],
                            tarball=os.path.join(target, "%s.tar" % name))
    copy_file(tarball, copied["frozen"]["tarball"])

    # The transcripts, filed under the workspace the trial ran in, which the
    # record keeps naming: the report's re-scan reads them from there.
    if record.get("workspace"):
        folder = project_folder(record["workspace"])
        transcripts = os.path.join(source, "home", ".claude", "projects",
                                   folder)
        if os.path.isdir(transcripts):
            shutil.copytree(transcripts,
                            os.path.join(target, "home", ".claude",
                                         "projects", folder),
                            dirs_exist_ok=True)

    from_area, to_area = scoring_area(source), scoring_area(target)
    updates = {"name": name, "arm": copied["arm"], "reused_from": origin}
    for kind in READINGS:
        found = existing_file(os.path.join(from_area, kind), name)
        if found:
            annotated(found, os.path.join(to_area, kind, "%s.json" % name),
                      updates)

    label = None
    for file, judging in judgings_of(from_area, name).items():
        label = judging.get("blind_id")
        annotated(file, os.path.join(to_area, "judge",
                                     os.path.basename(file)),
                  {"trial": name, "reused_from": origin})
    return copied, label


def read_map(area):
    """The scoring area's unblinding map, empty where there is none."""
    path = os.path.join(area, "judge", "map.json")
    if not os.path.isfile(path):
        return {"blind": {}}
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_map(area, mapping):
    path = os.path.join(area, "judge", "map.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as handle:
        json.dump(mapping, handle, indent=2, sort_keys=True)


def reuse(source, target, arms):
    """Copy the chosen arms' trials from `source` into `target`; return the
    names copied."""
    source, target = os.path.abspath(source), os.path.abspath(target)
    if source == target:
        raise TrialError("the source and the target are the same root")
    assert_outside_repository(target)
    chosen = select(source, arms)

    # A trial the target already offers would then be offered twice, which
    # the scorer refuses; better refused here, before anything is copied.
    try:
        held = scorable_trials(target, task="build")
    except TrialError:
        held = {}
    clash = sorted(set(chosen) & set(held))
    if clash:
        raise TrialError("%s already offers %s" % (target, ", ".join(clash)))

    # One ruler for both rounds: the earlier round's tool lock goes with its
    # trials, and a target already holding a different one is another run.
    from_lock = os.path.join(scoring_area(source), "tool-lock.txt")
    to_lock = os.path.join(scoring_area(target), "tool-lock.txt")
    if os.path.isfile(from_lock):
        if os.path.isfile(to_lock):
            with io.open(from_lock, encoding="utf-8") as handle:
                theirs = handle.read()
            with io.open(to_lock, encoding="utf-8") as handle:
                ours = handle.read()
            if theirs != ours:
                raise TrialError("%s holds a tool lock that differs from %s; "
                                 "the rounds would be measured with two "
                                 "rulers" % (to_lock, from_lock))
        else:
            copy_file(from_lock, to_lock)

    mapping = read_map(scoring_area(target))
    if "seed" not in mapping:
        mapping["seed"] = read_map(scoring_area(source)).get("seed")
    taken = {label: name for name, label in mapping["blind"].items()}
    records, labels = [], {}
    for name in sorted(chosen):
        copied, label = reuse_trial(name, chosen[name], source, target)
        records.append(copied)
        if label:
            if label in taken and taken[label] != name:
                raise TrialError("blind label %s is already %s's in %s"
                                 % (label, taken[label], target))
            labels[name] = label
    mapping["blind"].update(labels)
    if labels:
        write_map(scoring_area(target), mapping)

    started_at = datetime.datetime.now()
    os.makedirs(target, exist_ok=True)
    run_file = os.path.join(target, "run-%s-reused.json"
                            % started_at.strftime("%Y-%m-%dT%H-%M-%S"))
    write_run(run_file, started_at, records, "build", PROMPT)
    return sorted(chosen), run_file


def plant_source(scratch):
    """A source root shaped like round 1's: one trial per letter arm, each
    scored, judged and read for security, with a transcript and a lock."""
    source = os.path.join(scratch, "earlier")
    area = scoring_area(source)
    records = []
    for letter, index in (("A", 1), ("B", 1), ("C", 1)):
        old = "%s%d" % (letter, index)
        workspace = os.path.join(source, old)
        tarball = os.path.join(source, "%s.tar" % old)
        os.makedirs(workspace)
        with io.open(tarball, "wb") as handle:
            handle.write(b"frozen " + old.encode())
        records.append({"arm": letter, "trial": index, "task": "build",
                        "outcome": "completed", "workspace": workspace,
                        "frozen": {"head": "abc", "tarball": tarball}})
        folder = os.path.join(source, "home", ".claude", "projects",
                              project_folder(workspace))
        os.makedirs(folder)
        with io.open(os.path.join(folder, "planted.jsonl"), "w",
                     encoding="utf-8") as handle:
            handle.write("{}\n")
        for kind in READINGS:
            os.makedirs(os.path.join(area, kind), exist_ok=True)
            with io.open(os.path.join(area, kind, "%s.json" % old), "w",
                         encoding="utf-8") as handle:
                json.dump({"name": old, "arm": letter, "trial": index,
                           "suite_revision": "planted"}, handle)
    write_run(os.path.join(source, "run-planted.json"),
              datetime.datetime(2026, 9, 15, 12, 0, 0), records)
    os.makedirs(os.path.join(area, "judge"))
    blind = {"C1": "T1", "B1": "T2", "A1": "T3"}
    for old, label in blind.items():
        with io.open(os.path.join(area, "judge", "%s.json" % label), "w",
                     encoding="utf-8") as handle:
            json.dump({"trial": old, "blind_id": label, "outcome": "judged",
                       "answer": {"rubric": {}}}, handle)
    write_map(area, {"seed": 1, "blind": blind})
    with io.open(os.path.join(area, "tool-lock.txt"), "w",
                 encoding="utf-8") as handle:
        handle.write("ruler==1.0\n")
    return source


def self_test():
    """Prove a reuse copies the chosen arms' trials, and only those, under
    the words, and refuses to offer a trial twice."""
    scratch = os.path.join(os.environ.get("TEMP", "."),
                           "efficacy-reuse-self-test")
    remove_tree(scratch)
    source = plant_source(scratch)
    target = os.path.join(scratch, "later")
    area = scoring_area(target)

    def loaded(*parts):
        with io.open(os.path.join(*parts), encoding="utf-8") as handle:
            return json.load(handle)

    names, run_file = reuse(source, target, ["full", "hand"])
    records = {r["arm"] + "-" + str(r["trial"]): r
               for r in loaded(run_file)["trials"]}
    checks = [
        ("the chosen arms' trials are copied under the words, and no other",
         names == ["full-1", "hand-1"]
         and sorted(os.listdir(target)) == ["full-1.tar", "hand-1.tar",
                                            "home", os.path.basename(run_file)]
         and sorted(records) == ["full-1", "hand-1"]),
        ("each record names the arm's word, its origin and its copied tarball",
         records["full-1"]["arm"] == "full"
         and records["full-1"]["reused_from"]["name"] == "B1"
         and records["full-1"]["frozen"]["tarball"]
         == os.path.join(target, "full-1.tar")
         and io.open(os.path.join(target, "full-1.tar"), "rb").read()
         == b"frozen B1"),
        ("the transcripts come along under the workspace's folder",
         os.path.isfile(os.path.join(
             target, "home", ".claude", "projects",
             project_folder(records["hand-1"]["workspace"]),
             "planted.jsonl"))),
        ("the readings are filed under the word and name their origin",
         all(loaded(area, kind, "%s.json" % name)["name"] == name
             and loaded(area, kind, "%s.json" % name)["reused_from"]["name"]
             == old
             for kind in READINGS
             for name, old in (("full-1", "B1"), ("hand-1", "C1")))
         and not os.path.exists(os.path.join(area, "scores",
                                             "none-1.json"))),
        ("the judgings keep their labels and the map is theirs alone",
         loaded(area, "judge", "T2.json")["trial"] == "full-1"
         and loaded(area, "judge", "T1.json")["trial"] == "hand-1"
         and not os.path.exists(os.path.join(area, "judge", "T3.json"))
         and loaded(area, "judge", "map.json")["blind"]
         == {"full-1": "T2", "hand-1": "T1"}),
        ("the earlier round's tool lock comes along",
         io.open(os.path.join(area, "tool-lock.txt"),
                 encoding="utf-8").read() == "ruler==1.0\n"),
        ("the target offers the copied trials for scoring under the words",
         sorted(scorable_trials(target)) == ["full-1", "hand-1"]),
    ]
    try:
        reuse(source, target, ["full"])
        checks.append(("a trial the target already offers is refused",
                       False))
    except TrialError:
        checks.append(("a trial the target already offers is refused", True))
    try:
        reuse(source, os.path.join(scratch, "other"), ["short"])
        checks.append(("an arm the source never ran is refused", False))
    except TrialError:
        checks.append(("an arm the source never ran is refused", True))

    for label, ok in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED"))
    remove_tree(scratch)
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Bring an earlier round's trials into a run root.")
    parser.add_argument("--from", dest="source",
                        help="the earlier round's run root")
    parser.add_argument("--into", dest="target",
                        help="the run root to copy into; MUST be outside "
                             "this repository")
    parser.add_argument("--arms",
                        help="which arms to bring, as words separated by "
                             "commas: full,hand")
    parser.add_argument("--self-test", action="store_true",
                        help="prove a reuse copies the chosen trials and "
                             "only those; copy nothing")
    return parser.parse_args(argv)


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not (options.source and options.target and options.arms):
        print("--from, --into and --arms are required")
        return 2
    arms = [arm.strip() for arm in options.arms.split(",") if arm.strip()]
    unknown = [arm for arm in arms if arm not in ARMS]
    if not arms or unknown:
        print("--arms names %s; the arms are %s"
              % (", ".join(unknown) if unknown else "nothing",
                 ", ".join(ARMS)))
        return 2
    try:
        names, run_file = reuse(options.source, options.target, arms)
    except TrialError as error:
        print("refused: %s" % error)
        lib.print_verdict(False, "0 trial(s) reused, 1 refused")
        return 1
    for name in names:
        print("%s  reused" % name)
    print("\nRun record: %s" % run_file)
    lib.print_verdict(True, "%d trial(s) reused" % len(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
