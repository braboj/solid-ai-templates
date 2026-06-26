# Backend — Authentication and Authorization
[ID: backend-auth]
[DEPENDS ON: templates/base/security/security.md, templates/backend/http.md]

Rules for identity verification (authn) and access control (authz).
Applies to any backend service that has protected resources.
Extends `security-authn` and `security-sessions` from the base
security template with backend-specific depth.

---

## General principles

- Authentication (who are you?) and authorization (what can you do?) are
  separate concerns — keep them in separate layers
- Never implement your own cryptographic primitives — use well-audited libraries
- Fail closed: deny access by default; grant explicitly
- Centralise auth logic — no scattered permission checks across route handlers

---

## Authentication
[EXTEND: security-authn]

- Prefer delegating authentication to an identity provider (IdP) via
  OAuth 2.0 / OIDC (e.g. Auth0, Keycloak, Cognito) over rolling your own
- If issuing tokens directly, use short-lived JWTs (access token ≤ 15 minutes)
  with a separate refresh token (≤ 7 days, rotated on use)
- Validate every JWT: signature, `exp`, `iss`, `aud` — reject tokens missing
  any required claim
- Store refresh tokens server-side (database or cache) so they can be revoked —
  stateless refresh tokens cannot be invalidated before expiry

---

## Token transport
[ID: backend-auth-token-transport]

- Access tokens MUST be sent in the `Authorization: Bearer <token>` header
- Do NOT accept tokens in query parameters — they appear in server logs and
  browser history
- Refresh tokens MUST be stored in `httpOnly`, `Secure`, `SameSite=Strict`
  cookies — never in `localStorage` or JavaScript-accessible memory
- HTTPS required for all authenticated endpoints — no exceptions

---

## Authorization

- Use role-based access control (RBAC) as the baseline:
  assign permissions to roles, assign roles to users
- For fine-grained needs, layer attribute-based access control (ABAC) on top
  of RBAC — do not replace RBAC entirely
- Authorise at the service layer, not only at the route layer:
  a route that passes auth may call a service that operates on another user's
  data
- Never trust client-supplied IDs for ownership checks — always verify that
  the authenticated user owns or has access to the requested resource

---

## API keys (service-to-service)

- Issue API keys with the minimum required scope
- Hash API keys before storing — treat them like passwords
- Rotate API keys on a schedule and immediately on suspected compromise
- Log every API key usage with the key ID (not the key value) and the
  calling service identity

---

## Observability

- Log authentication failures at WARN with IP, user agent, and username
  (never the attempted password)
- Log authorization failures at WARN with user ID, resource, and action
- Alert on a spike in auth failures — may indicate a credential stuffing attack
- Never log tokens, passwords, or secrets — even at DEBUG level

---

## Testing

- Unit test permission logic with all role combinations including edge cases
  (no role, multiple roles, deprecated role)
- Integration test that protected endpoints return 401 for unauthenticated
  requests and 403 for authenticated requests with insufficient permissions
- Test token expiry: assert that an expired token is rejected
- Test token revocation: assert that a revoked refresh token cannot obtain
  a new access token