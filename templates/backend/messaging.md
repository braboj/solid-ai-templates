# Backend — Messaging
[ID: backend-messaging]

Cross-cutting rules for asynchronous messaging in backend services.
Applies regardless of message broker (Kafka, RabbitMQ, SQS, or equivalent).

---

## When to use async messaging

- Use messaging when the producer does not need an immediate response
- Use messaging for workloads that must survive producer restarts — fire-and-forget
  with durability
- Use messaging to decouple services that scale independently
- Do NOT use messaging when the caller needs a synchronous result — use HTTP or
  gRPC instead
- Do NOT replace a simple job queue within one service with a broker — use
  `templates/backend/jobs.md` instead

### Broker selection guide

| Broker | Best for |
|--------|----------|
| **Kafka** | High-throughput event streaming, ordered logs, replay, analytics pipelines |
| **RabbitMQ** | Task queues, work distribution, complex routing, RPC-over-messaging |
| **SQS** | AWS-native workloads, simple queues, no broker management overhead |
| **SQS + SNS** | Fan-out from one publisher to multiple independent consumers |

---

## Producer rules

- Validate message schema before publishing — the producer is responsible for
  schema correctness; the consumer should not be the first line of defence
- Every message MUST carry a correlation ID (trace ID or request ID) in its
  headers so consumers can link it to the originating request
- Use deterministic message IDs where the broker supports them — allows
  broker-level deduplication on producer retry
- Do not publish inside a database transaction without the transactional outbox
  pattern — a commit/publish race will cause lost or phantom messages
- Outbox pattern: write the message to an `outbox` table in the same transaction
  as the domain write; a relay process publishes from the outbox asynchronously

---

## Consumer rules

- Design all consumers to be **idempotent** — at-least-once delivery is the
  default; the same message will arrive more than once under failure conditions
- ACK only after the message has been fully processed — never ACK at receipt
- On processing failure: NACK or leave unacknowledged so the broker requeues
  or routes to the dead-letter queue (DLQ); never silently discard
- Apply exponential backoff on retries — tight retry loops amplify downstream
  failures
- Move messages to the DLQ after a configurable maximum retry count —
  the DLQ is the primary alerting surface for consumer failures
- Keep consumer handlers thin — delegate logic to a service function, exactly
  as HTTP handlers delegate to services

---

## Load and backpressure

- Decouple receive from process under load: acknowledge or enqueue the
  message fast, then do the work in a worker you pace — never run heavy
  processing inline on the receive path
- Coalesce bursts: debounce repeated events for the same resource into a
  single unit of work after a short quiet period, instead of processing
  every duplicate
- Apply backpressure when the queue saturates: bound the queue and slow
  or shed intake so the system degrades gracefully — an unbounded intake
  amplifies a downstream slowdown into an outage
- Enforce per-key or per-tenant fairness: cap in-flight work per source
  so one noisy producer cannot starve the rest (head-of-line blocking)
- Load-test the consumer at volume: watch queue depth and consumer lag,
  not the receive endpoint's latency, to find the real saturation point
- For bounded worker concurrency see `templates/backend/concurrency.md`;
  idempotency, retry/backoff, and the DLQ are covered in Consumer rules
  above

---

## Schema and contracts

- Define message schemas explicitly — JSON Schema, Avro, or Protobuf
- Schema changes MUST be backward-compatible: add fields, never remove or
  rename required fields without a versioning strategy
- Use a schema registry (Confluent Schema Registry, AWS Glue, or equivalent)
  for Kafka-based systems — prevents schema drift across teams
- Version the schema on breaking changes: encode the version in the topic name
  (`orders.v2`) or as a `schema_version` field in the payload

---

## Observability

- Log at consumer entry: message ID, topic/queue name, correlation ID, consumer group
- Log at consumer exit: processing duration, outcome (success / retry / DLQ)
- Track per topic/queue:
  - Consumer lag (Kafka) or queue depth (RabbitMQ / SQS)
  - Processing time (p50 / p95 / p99)
  - Error rate and DLQ depth
- Alert when:
  - Consumer lag grows continuously for > N minutes
  - DLQ depth exceeds a threshold
  - Consumer processing time exceeds the defined SLA

---

## Testing
[EXTEND: base-testing]

- Unit-test consumer business logic independently of the broker —
  pass a constructed message object directly to the handler function
- Test the DLQ path: publish a message designed to fail processing
  and assert it reaches the DLQ after the expected retry count
- Test idempotency: publish the same message twice and assert the
  consumer produces the same result with no unintended side effects