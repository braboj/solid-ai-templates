# Backend — Concurrency
[ID: backend-concurrency]

Universal rules for multi-threading, multi-processing, and async I/O.
Language-specific rules belong in the stack template via [EXTEND:
backend-concurrency].

---

## When to use what

| Workload | Recommended model | Avoid |
|---|---|---|
| I/O-bound (network, disk, DB) | Async / non-blocking I/O or thread pool | Blocking the main thread |
| CPU-bound (compute, encoding) | Separate processes | Threads in runtimes with a GIL |
| Mixed I/O + CPU | Async for I/O, process pool for CPU | Single-threaded blocking |
| True parallelism required | Language with native threading (e.g. Go) or multiprocessing | Green threads for CPU work |

Default to async for I/O-bound services. Reach for processes only when
CPU-bound work cannot be offloaded to a background job or worker process.

---

## Shared state

- Avoid shared mutable state — prefer immutable data structures or
  message passing (queues, channels)
- If shared state is unavoidable, protect every access with a lock;
  document which lock guards which data
- Never hold a lock while performing I/O — risk of deadlock and contention
- Prefer fine-grained locks over a single global lock

---

## Structured concurrency

- Never start a thread, goroutine, or async task without a clear owner
  and a clear shutdown path
- Use structured concurrency primitives (e.g. `errgroup`, `asyncio.TaskGroup`,
  `ExecutorService`) over fire-and-forget
- Propagate cancellation explicitly — pass a cancellation token or context
  as the first argument to any function that may block
- On shutdown, cancel all in-flight work and wait for it to finish before
  the process exits — do not rely on OS cleanup

---

## Pitfalls

- **Deadlock**: two threads each waiting for a lock the other holds —
  always acquire locks in a consistent order
- **Livelock**: threads repeatedly yielding to each other without making
  progress — add backoff or a tiebreaker
- **Race condition**: outcome depends on scheduling order —
  use a race detector during testing (e.g. `go test -race`, ThreadSanitizer)
- **Starvation**: low-priority work never gets scheduled —
  bound queue sizes and use fair scheduling where possible
- **Thread-local state leakage**: in thread-pool or async contexts,
  context (e.g. request ID, user identity) must be explicitly passed,
  not stored in thread-locals

---

## Observability

- Log the concurrency model in use at service startup (thread pool size,
  event loop policy, worker count)
- Track thread/goroutine/task count as a metric — an unbounded growth
  indicates a leak
- Alert on deadlock symptoms: requests timing out uniformly across all
  endpoints with no error in logs

---

## Testing

- Run tests with the race detector enabled in CI — do not rely on
  code review alone to catch data races
- Write stress tests for any code that shares state: run N goroutines /
  threads concurrently and assert invariants hold
- Test cancellation paths: assert that cancelling a context or token
  terminates the operation promptly and cleans up resources