# Base — Application Security

[ID: base-security]

Cross-cutting security rules for application code. Applies to
every project regardless of language or framework.


---

## Input validation

[ID: security-input]

- Validate all external input at the system boundary — the first
  point where untrusted data enters the application
- Use schema validation libraries (Zod, Joi, Pydantic, JSON Schema)
  — never hand-write validation for complex inputs
- Allowlist, not blocklist — define what is valid, reject everything
  else
- Reject invalid input with a clear error — do not silently coerce
  or strip fields
- Internal code trusts validated data — do not re-validate in
  service or repository layers

---

## Output encoding

[ID: security-output]

- Encode dynamic data for its rendering context at the point of
  output — HTML, URL, JavaScript, SQL, shell
- Encode on output, not on input — store the raw value, encode
  when rendering
- Use framework-provided encoding: React JSX, Jinja2 autoescape,
  Go `html/template`, Astro `{expression}`
- Never use `innerHTML`, `set:html`, `dangerouslySetInnerHTML`,
  or `| safe` with user-supplied data
- Context matters — HTML encoding does not prevent URL injection

---

## Injection prevention

[ID: security-injection]

- Use parameterized queries for all database access — never
  concatenate user input into SQL strings
- Use prepared statements or ORM query builders — raw SQL with
  string interpolation is a SQL injection vulnerability
- Escape shell arguments when invoking external commands — or
  use API alternatives that do not invoke a shell
- Never pass user input to `eval()`, `exec()`, `Function()`,
  or equivalent dynamic code execution

---

## Authentication

[ID: security-authn]

- Hash passwords with a modern algorithm: bcrypt, scrypt, or
  Argon2 — never MD5, SHA-1, or plain SHA-256
- Enforce minimum password complexity at the boundary
- Use constant-time comparison for secrets and tokens — timing
  attacks leak information through response time
- Support multi-factor authentication for privileged operations
- Lock accounts or throttle after repeated failed attempts

---

## Session management

[ID: security-sessions]

- Generate session IDs with a cryptographic random generator
- Regenerate the session ID after login — prevents session fixation
- Set cookie flags: `HttpOnly`, `Secure`, `SameSite=Lax` (or
  `Strict` for sensitive applications)
- Expire sessions after a reasonable idle period — 30 minutes
  for sensitive applications, configurable otherwise
- Invalidate sessions on logout — do not rely on cookie expiry
  alone

---

## Secrets in code

[ID: security-secrets]

- Never hardcode secrets, API keys, tokens, or credentials in
  source files
- Never commit secrets to version control — even in test files
  or example configurations
- Use `.env` files for local development — add to `.gitignore`
- Provide `.env.example` with placeholder values — never real
  secrets
- If a secret is accidentally committed, rotate it immediately —
  removing from git history is not sufficient; the secret is
  compromised

---

## Transport security

[ID: security-transport]

- HTTPS everywhere — no exceptions for production traffic
- HSTS MUST be enabled on all production sites with
  `includeSubDomains` and a minimum `max-age` of one year
- TLS 1.2 is the minimum version — disable TLS 1.0 and 1.1
- Use strong cipher suites — disable known-weak ciphers
- Internal service-to-service traffic SHOULD use mTLS via a
  service mesh or explicit certificate configuration

---

## Security headers

[ID: security-headers]

- Set security headers on every HTTP response at the reverse proxy
  or middleware level — not per route
- Required headers:
  - `Content-Security-Policy` — start strict, relax only as needed
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY` (or CSP `frame-ancestors`)
  - `Strict-Transport-Security` (see Transport security)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy` — disable unused browser APIs
- When enabling `nosniff`, pin static asset MIME types in code — the
  OS registry resolves `.js` to `text/plain` on some platforms, so the
  browser refuses to run the script and CI on Linux will not catch it;
  verify script/style execution in a real browser, not just status codes
- Never use `unsafe-inline` or `unsafe-eval` in CSP without a
  written justification
- Do not expose server version or technology stack in headers —
  remove `X-Powered-By`, `Server` version strings

---

## Error handling

[ID: security-errors]

- Never expose stack traces, internal paths, or database errors
  to end users — return generic error messages externally
- Log full error details server-side for debugging
- Use consistent error response formats — do not leak internal
  structure through varying error shapes
- Return appropriate HTTP status codes — do not use 200 for errors
- Do not reveal whether a resource exists via error messages —
  login errors should say "invalid credentials", not "user not
  found" vs "wrong password"

---

## Logging

[ID: security-logging]

- Never log secrets, tokens, passwords, or personally identifiable
  information (PII)
- Sanitize log output — user-supplied data in logs can enable
  log injection attacks
- Log security-relevant events: authentication attempts, access
  denials, privilege changes, configuration changes
- Include enough context for investigation: timestamp, user ID,
  IP, action, result
- Retain security logs for a defined period — compliance may
  require 90 days to 7 years

---

## CORS

[ID: security-cors]

- Restrict `Access-Control-Allow-Origin` to specific known
  origins — never use `*` for authenticated endpoints
- Do not reflect the `Origin` header back as
  `Access-Control-Allow-Origin` without validation
- Restrict allowed methods and headers to what the API actually
  needs
- Set `Access-Control-Max-Age` to cache preflight responses —
  reduces latency and server load

---

## Deserialization and data integrity

[ID: security-integrity]

- Never deserialize untrusted data with native serialization
  formats (Python `pickle`, Java `ObjectInputStream`, PHP
  `unserialize`) — use safe formats (JSON, Protocol Buffers)
- Validate the structure and types of deserialized data before
  use — treat it as untrusted input
- Verify integrity of downloaded artifacts, updates, and
  dependencies — use checksums or digital signatures
- Pin dependency versions and verify checksums in lockfiles —
  do not trust upstream registries blindly
- CI/CD pipelines MUST use pinned, verified actions and images —
  never pull `latest` tags in production pipelines

---

## Server-Side Request Forgery (SSRF)

[ID: security-ssrf]

- Never pass user-supplied URLs directly to server-side HTTP
  clients — validate and sanitize first
- Allowlist permitted destination hosts and schemes — reject
  anything not on the list
- Block requests to internal networks (`127.0.0.0/8`,
  `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`,
  `::1`, `fc00::/7`) — even after DNS resolution
- Resolve the hostname and validate the IP before making the
  request — prevents DNS rebinding attacks
- Disable HTTP redirects in server-side HTTP clients, or
  re-validate the destination after each redirect
- Limit response size and timeout for outbound requests to
  prevent resource exhaustion

---

## File uploads

[ID: security-uploads]

- Validate file type by content (magic bytes), not by extension
  or MIME type — both are trivially spoofed
- Enforce maximum file size at the boundary
- Store uploads outside the web root — never serve user uploads
  from the same domain without sanitization
- Generate random filenames — do not use the original filename
  (path traversal risk)
- Scan uploaded files for malware if the application serves them
  to other users

---

## Agent secrets handling

[ID: security-agent-secrets]

- MUST NOT read, print, or cat files that may contain secrets:
  `.env`, `credentials.json`, `*-key*`, `*.pem`, `*.key`,
  `serviceaccount.json`, `secrets.yaml`
- MUST NOT echo, log, or display environment variable values —
  use `printenv | grep -c KEY` to check presence without
  revealing the value
- MUST NOT include secret values in commit messages, PR
  descriptions, or conversation output
- MUST warn the user before committing files that commonly
  contain secrets (`.env`, `credentials.json`, private keys)
- Use targeted commands to verify secret presence without
  exposure: `grep -c PATTERN file` (count matches),
  `test -f .env && echo exists` (check file existence)
- If secrets are accidentally exposed in a session, immediately
  flag to the user: name the exposed secret, recommend
  immediate rotation, and note that session history may be
  cached or logged
