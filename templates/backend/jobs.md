# Backend — Background Jobs
[ID: backend-jobs]

Rules for background job processing, task queues, and scheduled work.
Applies regardless of technology (Celery, asynq, Sidekiq, BullMQ, etc.).

---

## When to use background jobs

- Offload any work that does not need to complete within the HTTP request cycle
- Use jobs for: email delivery, report generation, image processing,
  webhook fanout, long-running data imports
- Do NOT use jobs for work that the caller needs the result of immediately —
  use async/await or streaming instead
- Do NOT use jobs to paper over a slow synchronous path — fix the root cause
  first

---

## Idempotency

- Every job MUST be idempotent — safe to execute more than once with the
  same input and produce the same outcome
- Use a deduplication key (e.g. `job_id`, `event_id`) to detect and skip
  duplicate executions
- Design for at-least-once delivery — the queue may deliver a message more
  than once, especially after a worker crash

---

## Retry and failure handling

- All jobs MUST have a retry limit — infinite retries will fill the queue
- Use exponential backoff with jitter between retries
- After the retry limit is exhausted, move the job to a dead-letter queue (DLQ)
  — never silently drop failed jobs
- Alert on DLQ depth — a growing DLQ is a silent production incident
- Log the job ID, attempt number, and error on every failure

---

## Separation of concerns

- Job handlers MUST be thin — delegate all business logic to service functions
- Service functions used by jobs SHOULD be the same ones used by HTTP handlers —
  no parallel logic paths
- No direct database access in job handlers — go through the service layer
- No HTTP calls in job handlers unless the job's explicit purpose is an
  outbound webhook

---

## Scheduling

- Scheduled jobs (cron-style) MUST be defined in code, not configured manually
  in the infrastructure — schedule-as-code
- Document the expected frequency and maximum acceptable latency for each
  scheduled job
- Ensure only one instance of a scheduled job runs at a time —
  use a distributed lock or a leader-election mechanism

---

## Observability

- Emit a structured log entry at job start (INFO) and job completion (INFO)
- Log failures at ERROR with full context (job type, ID, payload summary,
  error message, stack trace)
- Track job duration, queue depth, and failure rate as metrics
- Alert if queue depth exceeds a threshold that indicates worker starvation

---

## Testing
[EXTEND: base-testing]

- Unit test the service function the job delegates to — not the job
  handler itself
- Integration test the happy path end-to-end: enqueue → execute →
  assert side effect
- Test the retry path: assert that a transient failure triggers a retry
- Test the DLQ path: assert that a permanent failure ends up in the DLQ