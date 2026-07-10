# Backend — API Design
[ID: backend-api]
[DEPENDS ON: templates/backend/http.md]

## API-first
- Software MUST be designed API-first — the public contract MUST be agreed
  upon and documented before implementation begins
- Any deviation from API-first design MUST be recorded in an Architecture
  Decision Record (ADR) with a stated justification
- Benefits: client teams (web, mobile, third-party) can work in parallel,
  the API is testable independently of any frontend, and the contract becomes
  a product in its own right

## Protocol selection
[ID: backend-api-protocols]

| Protocol  | Use when                                                                                            |
|-----------|-----------------------------------------------------------------------------------------------------|
| REST      | Default. External APIs, browser/mobile clients, third-party integrations, ops/admin endpoints       |
| gRPC      | Internal service-to-service, performance-critical paths, streaming, polyglot teams sharing a schema |
| GraphQL   | Frontend-facing APIs where clients need flexible querying and over-fetching is a real problem       |
| WebSocket | Real-time push, bidirectional streams where HTTP polling is not viable                              |
| Messaging | Async, fire-and-forget, event-driven                                                                        |

- Start with REST — only deviate with a stated reason in an ADR
- REST + gRPC is valid: REST for external/ops endpoints, gRPC for internal hot
  paths
- Never use gRPC as the primary interface for browser clients
- GraphQL and REST in the same service require strong justification — dual
  surfaces double the maintenance burden
- SOAP and other legacy protocols require a per-case ADR

## OpenAPI specification
- Every API MUST have an OpenAPI specification
- The spec MUST be kept up to date — a stale spec is worse than no spec
- Include: all resources, methods, parameters, response schemas, error
  responses,
  and authentication requirements
- Provide a changelog documenting API changes across versions
- Prefer design-first: hand-author the spec as the single source of
  truth and serve it verbatim — the published spec is the same file the
  team edits, not one generated from code annotations
- Pin the spec to code: assert that enums, routes, and error codes in
  code match the spec so any drift fails a test, not a consumer
- Contract-test the running API against the spec — generate cases from
  the spec and run them against a live instance (e.g. Schemathesis) so
  the implementation provably conforms to the published contract
- The spec document's own version field (OpenAPI `info.version`) is a
  separate axis from the package / release version — maintain it on its
  own cadence and do NOT bump it on a routine package release that does
  not change the contract. Where a drift test guards it, assert the
  field is PRESENT (the spec requires it), not that it equals the
  package version

## Versioning
- APIs in a given version MUST maintain backward compatibility
- Version the API in the URI path prefix: `/v1/`, `/v2/`
- Start versioning from `v1`; introduce `v2` only when breaking changes are
  unavoidable
- Alternatively, use a custom request header: `Api-Version: 2`
- MUST NOT use media type to control API versions

## Backward compatibility
A new major version is required whenever a breaking change is introduced.

**Breaking changes** — any of the following constitutes a break:
- Removing or renaming a response field or object
- Changing the type of an existing field
- Switching the authentication scheme
- Modifying an existing HTTP verb or URI path
- Changing the wire protocol or Content-Type
- Altering business logic in a way that changes observable results

**Non-breaking changes** — these MUST NOT require a version bump:
- Adding a new optional field or object to a response
- Adding a new endpoint or HTTP verb
- Adding new optional query parameters

## Deprecation strategy
When a breaking change is introduced:

1. Deploy the new version alongside the old one
2. Add the `Deprecation` header to all responses from the old version with
   the Unix timestamp of when deprecation started:
   `Deprecation: @<unix-timestamp>`
3. Optionally add the `Sunset` header with the planned removal date:
   `Sunset: <HTTP-date>`
4. Notify all consumers and agree on a migration timeline
5. Remove the old version only after the sunset date has passed

```
Deprecation: @<unix-timestamp>
Sunset: <HTTP-date>
```

## Statelessness
[ID: backend-api-statelessness]
- APIs MUST be stateless — no client context stored on the server between
  requests
- All information needed to process a request MUST be in the request itself
- Session state belongs in the client or a dedicated session store, not in the
  API service

## Pagination
- Collection endpoints MUST be paginated — never return unbounded lists
- Use `limit` and `offset` (or cursor-based) pagination
- Include navigation links (`next`, `prev`) in the response per HATEOAS
