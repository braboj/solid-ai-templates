# Backend — Caching
[ID: backend-caching]

Cross-cutting caching rules for any backend service. Applies regardless of
cache technology (Redis, Memcached, in-process).

---

## When to cache

- Cache data that is expensive to compute or retrieve and changes infrequently
- Do NOT cache data that MUST be real-time (e.g. account balances, stock levels)
- Do NOT cache secrets, credentials, tokens, or PII — even temporarily
- Prefer no cache over a stale cache for safety-critical or financial data

---

## Patterns

- **Cache-aside (lazy loading)**: read from cache first; on miss, load from
  source,
  populate cache, return result — default pattern for read-heavy workloads
- **Write-through**: write to cache and source together on every update —
  use when stale reads are unacceptable and write latency is acceptable
- **Write-behind**: write to cache immediately, persist to source asynchronously
  —
  avoid unless throughput requirements justify the added complexity and risk
- Never cache at more than one layer for the same data — multiple caches
  create inconsistency and make invalidation impossible to reason about

---

## Keys

- Namespaced keys: `<service>:<entity>:<id>` — e.g. `users:profile:42`
- Include a version segment when the cached schema changes:
  `users:v2:profile:42`
- Document the key schema — undocumented keys become orphaned entries
- Never construct keys from unvalidated user input — risk of cache poisoning

---

## TTL and expiry

- Every cached entry MUST have a TTL — no indefinite caching
- Set TTL based on acceptable staleness, not convenience
- Use shorter TTLs (seconds–minutes) for frequently changing data;
  longer TTLs (hours–days) for reference data
- Use cache tags or explicit invalidation for data that must expire on write,
  not just on timeout

---

## Invalidation

- Invalidate cache entries on write, not only on TTL expiry
- Invalidation MUST be atomic with the write where consistency matters —
  use transactional outbox or pub/sub if cache and DB are separate systems
- Prefer targeted invalidation (`DEL users:profile:42`) over broad flush
  (`FLUSHDB`) — a cache flush is an outage in disguise
- Document which code path owns invalidation for each cache key

---

## Resilience

- Cache failures MUST NOT crash the application — treat the cache as
  an optional acceleration layer, not a required dependency
- On cache miss or error, fall through to the source of truth
- Use circuit breakers or timeouts on cache calls — a slow cache is
  worse than no cache
- Protect against cache stampede (thundering herd): use probabilistic early
  expiry, a mutex/lock on population, or a background refresh

---

## Observability

- Instrument cache hit rate, miss rate, and eviction rate
- Alert if hit rate drops significantly below baseline — indicates
  misconfigured TTL or an invalidation bug
- Log cache errors at WARN level; log stampede events at INFO

---

## Testing
[EXTEND: base-testing]

- Unit tests for cache key construction and TTL logic MAY use an
  in-memory fake
- Test the fallback path: assert that a cache miss or error still
  returns correct data from the source