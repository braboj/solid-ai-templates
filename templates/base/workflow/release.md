# Base — Release Management
[ID: base-release]

## Versioning
- All packages and services MUST follow semantic versioning
  (`MAJOR.MINOR.PATCH`)
- MAJOR — breaking changes
- MINOR — new backward-compatible functionality
- PATCH — backward-compatible bug fixes

## Version bump propagation
A consumer that references an upgraded dependency MUST advance its own version
at least as far:
- Dependency bumps MINOR → consumer MUST bump at least MINOR (not just PATCH)
- Dependency bumps MAJOR → consumer MUST bump MAJOR

> Rationale: If a dependency received a minor bump, declaring only a patch
> change in the consumer would mislead downstream callers — they would assume
> a drop-in replacement when the interface has changed.

## Backward compatibility
- APIs SHOULD remain backward compatible across minor and patch versions
- Never remove or rename a field in a response without a deprecation period
- Communicate breaking changes to all consumers before making them

## Cut-over phases
When a breaking change is unavoidable:

1. Deploy the new version alongside the old one
2. Notify all consumers that the old version is deprecated and set a removal
   date
3. Allow consumers to migrate at their own pace within the deprecation window
4. Remove the old version only after the window has closed

```
Server:   [--- v1 ---|--- v1 + v2 ---|--- v2 ---]
Client A: [--- v1 ---|------ v2 -----]
Client B: [--- v1 ----------|-------- v2 --------]
```

No step above is enforced by anything, and the sequence reads as a
procedure that is. Step 4 is the one to gate first: removing a version a
consumer still calls cannot be corrected after the fact, while the other
three fail visibly and recoverably. Record the removal date from step 2
where a machine can read it — a deprecation header, a manifest field, a
dated entry — and gate the removal on that date having passed. Until
then, mark the step as unenforced where it is written, so the operator's
confidence matches what is actually checked.

## Release gate
- All automated tests MUST pass on the staging environment before any
  production release
- A failing test suite MUST block the release — MUST NOT promote a build
  until every test passes
- The team that owns a downstream service — not the team that made the change —
  is accountable for verifying the integrated system before release
- Each rule above names a condition and not the check that reads it. The
  first two are enforced wherever the pipeline blocks promotion on a red
  suite, and that binding is the project's to declare rather than
  something the rules can assume. The third is enforced by nobody: a
  downstream owner who never verifies produces no signal, so name the
  artifact that records the verification and treat its absence as the
  failure
