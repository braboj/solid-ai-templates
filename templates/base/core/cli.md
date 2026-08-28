# Base — CLI and Driver Architecture
[ID: base-cli]
[DEPENDS ON: templates/base/core/quality.md, templates/base/core/config.md]

Applies to any executable entry point — a published CLI, an operational
driver, a maintenance script that outlives the afternoon it was written
in. The rules below are ecosystem-neutral; the concrete argument parser
and exit mechanism are named in the language layer.

A file under the examples directory is outside this scope, even though it
is executable and a reader runs it directly. `base-examples` governs it,
and the two want opposite shapes: the rules below factor shared plumbing
out of a fleet of drivers, which is correct for drivers and wrong for a
directory whose value is that each file is read whole. An example that
grows a shared module, a configuration layer or an `argv` seam has been
made worse at the only job it has. Where a project genuinely promotes an
example to a supported entry point, it moves out of that directory first,
and these rules apply to it there.

## Driver shape
[ID: base-cli-main]

- An entry point MUST be a thin `main(argv) -> int`: parse arguments,
  resolve configuration, call a pure core, write outputs. Anything
  heavier than those four steps belongs in a function the entry point
  calls
- `argv` MUST be a parameter, not read from the global. It is the
  testability seam — a test passes a list instead of mutating process
  state, and the difference is what makes the entry point coverable at
  all
- The return value MUST be the exit code, produced by returning an
  integer rather than exiting from inside the logic. A code path that
  terminates the process cannot be asserted on, so an entry point that
  exits internally is untestable at exactly the points that matter
- Each step MUST be independently callable. A driver whose stages are
  reachable only by running the whole command can be tested end to end
  or not at all, which is the shape that makes a slow suite

## Shared plumbing
[ID: base-cli-plumbing]

- A project with more than one entry point MUST put argument
  registration, configuration resolution, file I/O and output formatting
  in one shared module. Duplicated across drivers, these drift, and the
  drift shows up as two commands disagreeing about the same flag
- Configuration resolution MUST distinguish "no default was given" from
  "the default is empty". A single falsy value cannot carry both, so a
  missing required input reads as an explicit empty one and the run
  proceeds on it. Use a sentinel distinct from every legal value
- Machine-readable output MUST go to stdout, and everything else —
  progress, warnings, diagnostics — MUST go to stderr. A driver that
  interleaves them cannot be piped, and the breakage appears only once
  someone pipes it, usually in an automation nobody is watching
- File handles MUST be closed on every path, including the failing one.
  A driver that writes its output and then raises can leave a truncated
  file that looks complete to whatever reads it next

## Inspecting a run before making it
[ID: base-cli-plan]

- A driver SHOULD accept a flag that prints the steps a run would take
  and returns without taking them. It MUST return before any expensive
  import or connection, so the shape of a run is inspectable in an
  environment that could not perform one
- This is distinct from a dry run that computes and declines to persist.
  One answers "what would this do", the other "what would this produce"
  — a driver MAY offer both, MUST NOT conflate them under one flag, and
  MUST NOT let either write

## A durable result persists by default
[ID: base-cli-persistence]

- A command whose result is expensive to produce MUST persist it by
  default, not only when an output flag is passed. The first time the
  flag is forgotten the whole computation is discarded, and the operator
  sees the printed result and assumes it was saved
- The default destination MUST be derived from the same configuration
  the inputs came from, so a bare invocation writes where its siblings
  write. An output flag overrides *where* the result goes, never
  *whether* it is written
- Print-only MUST be an explicitly requested mode. Silent
  non-persistence is indistinguishable from success until something
  downstream reads the gap, which is usually long after the run is
  cheap to repeat
- Check: run the command with no output flag, then confirm the expected
  file exists and is non-empty. A driver that fails this writes nothing
  on the path every operator takes first
