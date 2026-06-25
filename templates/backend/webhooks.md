# Backend — Inbound Webhook Handling
[ID: backend-webhooks]
[DEPENDS ON: templates/backend/http.md, templates/backend/messaging.md, templates/base/security/security.md, templates/backend/observability.md]

Rules for receiving inbound webhooks (provider callbacks, integration
events) under bursty load. Compose this template on demand for a service
that receives webhooks — it is not part of any stack chain by default.

The generic resilience substrate — idempotency, retry/backoff, DLQ,
debounce/coalesce, backpressure, fairness — is inherited from
messaging.md; this template adds only the HTTP-ingestion-specific surface.

---

## Intake

- Expose a distinct intake URL per provider or connection — never
  multiplex unrelated providers onto one endpoint; per-integration URLs
  isolate failures, scope signature handling, and sharpen observability

## Verify at the edge

- Verify the provider signature before doing any work — reject forged or
  malformed payloads before parsing, persisting, or enqueueing
- Verify against the exact bytes received, not a re-serialised copy, and
  treat the raw body as untrusted until the signature checks out

## Respond fast

- Return 2xx within the provider's timeout budget: acknowledge receipt,
  then process asynchronously — never run heavy work inline on the
  request path
- Persist or enqueue the event before responding so an acknowledged
  event is never lost

## Survive provider retries

- Account for retry amplification — a non-2xx response makes the provider
  resend, so a slow or failing handler multiplies inbound load
- Return 2xx even when intentionally skipping an event (duplicate,
  irrelevant); reserve 5xx strictly for failures where redelivery is wanted
- Deduplicate on the provider's event ID — at-least-once delivery means
  the same event will arrive more than once

---

## Testing
[EXTEND: base-testing]

- Test signature rejection: a tampered body or invalid signature MUST be
  rejected before any side effect occurs
- Test idempotency: deliver the same event twice and assert a single effect
- Test the fast-ack path: the handler returns 2xx without waiting for
  downstream processing to complete
