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

## Release gate
- All automated tests MUST pass on the staging environment before any
  production release
- A failing test suite MUST block the release — MUST NOT promote a build
  until every test passes
- The team that owns a downstream service — not the team that made the change —
  is accountable for verifying the integrated system before release
