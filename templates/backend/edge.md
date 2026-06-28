# Backend — Edge / Reverse Proxy
[ID: backend-edge]
[DEPENDS ON: templates/backend/http.md, templates/base/security/security.md, templates/backend/observability.md]

Rules for the edge tier — the reverse proxy, load balancer, or gateway
that sits in front of the application (nginx, Envoy, Caddy, HAProxy, a
cloud ALB, or a CDN). Compose this template on demand for a service
exposed to untrusted networks — it is not part of any stack chain by
default.

The edge is infrastructure, not a service: it terminates TLS, routes,
and shields the application tier. Keep business logic out of it — that
belongs in the application layer. API-gateway routing inside a service
mesh is covered by `microservices.md`.

---

## TLS termination

- Terminate TLS at the edge and redirect all plain HTTP to HTTPS — the
  application MUST NOT be reachable over cleartext
- Serve only TLS 1.2+; disable legacy protocol and cipher versions
- Set HSTS (`Strict-Transport-Security`) at the edge so browsers refuse
  to downgrade
- Re-encrypt to upstreams (mTLS or TLS) when traffic crosses an
  untrusted segment; plaintext to upstreams is acceptable only on a
  trusted private network

## Forwarded headers and client identity

- Forward the originating client over `Forwarded` (RFC 7239) or the
  de-facto `X-Forwarded-For` / `X-Forwarded-Proto` / `X-Forwarded-Host`
- Strip inbound forwarded headers from external callers before
  appending your own — never trust a client-supplied `X-Forwarded-For`
- Configure the application's trusted-proxy list so it reads the real
  client IP only from hops you control — an over-broad trust list lets
  callers spoof their address and defeat IP rate limits
- Propagate or originate a correlation/request ID at the edge so a
  request is traceable end to end (see `observability.md`)

## Routing and upstreams

- Route by host and path to upstream pools; keep routing declarative,
  not code
- Gate traffic on upstream health checks — remove failing instances
  from rotation and add them back only after they pass readiness
- Balance across instances (round-robin or least-connections) and
  spread upstreams across availability zones
- Drain connections on deploy — stop sending new requests to an
  instance before it shuts down so in-flight work completes

## Limits, timeouts, and buffering

- Set explicit connect, read, and write timeouts to every upstream —
  an unbounded proxy timeout turns one slow upstream into edge
  exhaustion
- Cap request body size at the edge to reject oversized payloads before
  they reach the application
- Bound concurrent connections and enforce per-client rate limits at
  the edge; return `429` with `Retry-After` when a client exceeds them
- Set keep-alive and idle timeouts so abandoned connections free their
  slots

## Edge security

- Enforce rate limiting, IP/geo allow-or-deny, and WAF rules at the
  edge — shed abusive traffic before it reaches the application
- Do not leak upstream identity: strip `Server`, `X-Powered-By`, and
  internal hostnames from responses
- Restrict admin, metrics, and health endpoints to internal networks —
  never expose them through the public edge

---

## Testing
[EXTEND: base-testing]

- Test that plain HTTP redirects to HTTPS and that HSTS is present
- Test that a client-supplied `X-Forwarded-For` is overwritten, not
  trusted, for callers outside the trusted-proxy list
- Test that an oversized body and an over-rate client are rejected at
  the edge (`413` / `429`) without reaching the application
- Test that a failing upstream is removed from rotation by the health
  check and that deploys drain in-flight connections
