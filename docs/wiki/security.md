# Application Security — Wiki

[ID: security-wiki]
[DEPENDS ON: base/security.md]

Wiki notes on reusable structures for secure application code.
Each entry describes a problem, solution structure, when to use
it, and examples.

See `base/security.md` for application security rules.
See `base/devsecops.md` for pipeline security rules and
`devsecops.md` for pipeline security patterns.

---

## 1. Validate-at-boundary

[ID: security-wiki-input-validation]

**Problem:** User input flows through multiple layers with
validation scattered across each. Some paths skip validation
entirely.

**Solution:** Validate at the system boundary. Internal code
trusts validated data.

```
[boundary: validate] → [service: trust] → [repository: trust]
         ↓ reject
     400 Bad Request
```

**When to use:**

- Every HTTP endpoint, CLI argument, message consumer, file import

**Example (TypeScript + Zod):**

```typescript
const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(["admin", "user"]),
});

app.post("/users", (req, res) => {
  const result = CreateUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.issues });
  }
  userService.create(result.data);
});
```

---

## 2. Encode-on-output

[ID: security-wiki-output-encoding]

**Problem:** Data stored raw is rendered in HTML without encoding.
Stored XSS executes in every user's browser.

**Solution:** Encode for the rendering context at the point of
output. Store raw, encode on render.

```
Store:  <script>alert(1)</script>     (raw in database)
Render: &lt;script&gt;alert(1)&lt;/script&gt;  (HTML-encoded in page)
```

**When to use:**

- Every point where dynamic data is rendered in HTML, URLs,
  JSON, SQL, or shell commands

---

## 3. Runtime secret injection

[ID: security-wiki-secret-injection]

**Problem:** Secrets are hardcoded in source, baked into images,
or passed as build-time variables. They leak into version control,
logs, or container layers.

**Solution:** Inject secrets at runtime from a vault. The
application reads them on startup — never from code or images.

```
Build time: no secrets — image is clean
Runtime:    vault → env var / mounted file → application reads
```

**When to use:**

- Every application that uses credentials, tokens, or API keys

**Example (Kubernetes):**

```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: database-url
```

**Example (Docker Compose):**

```yaml
services:
  app:
    environment:
      - DATABASE_URL # read from host env or .env file
```

---

## 4. CSRF double-submit

[ID: security-wiki-csrf]

**Problem:** A malicious site submits a form using the user's
session. The server cannot distinguish legitimate from forged
requests.

**Solution:** Generate a token per session. Embed in forms. Verify
on every state-changing request.

```
Server generates token → stored in session
Page renders token     → hidden field in form
Form submits token     → server verifies against session
Mismatch               → 403 Forbidden
```

**When to use:**

- State-changing endpoints in server-rendered applications
- NOT needed for API-only backends using Bearer tokens
- NOT needed for SameSite=Strict cookies

---

## 5. Rate limiter placement

[ID: security-wiki-rate-limit]

**Problem:** Endpoints are brute-forced or scraped. The server
is overwhelmed with requests.

**Solution:** Limit requests per client per time window at the
reverse proxy or API gateway — not in application code.

```
Client → [rate limiter] → allowed (under limit)
                        → 429 + Retry-After (over limit)
```

**When to use:**

- All public-facing endpoints
- Stricter limits on authentication endpoints

**Tier examples:**

- Auth: 5/min
- API: 100/min
- Static: 1000/min

---

## 6. Lock file as supply chain guard

[ID: security-wiki-dependency-pinning]

**Problem:** A version range pulls a compromised patch release
automatically. Supply chain attack succeeds silently.

**Solution:** Pin exact versions in the lock file. Commit it.
Review updates explicitly through Dependabot or Renovate PRs.

```
package.json:     "lodash": "^4.17.0"   (range — dangerous alone)
package-lock.json: "lodash": "4.17.21"  (pinned — safe)
```

**When to use:**

- Every project with external dependencies

---

## 7. Least-privilege scoping

[ID: security-wiki-least-privilege]

**Problem:** A compromised component has admin access. The blast
radius is the entire system.

**Solution:** Grant each component the minimum permissions it
needs. Start with zero, add only what is required.

```
Service A → read-only access to orders table
Service B → read-write access to users table
CI token  → push to feature branches only
Container → non-root, read-only filesystem
```

**When to use:**

- Every service account, CI token, API key, IAM role, container,
  and database user

---

## 8. Security header baseline

[ID: security-wiki-headers]

**Problem:** Default browser behavior is permissive. Every missing
header is an attack surface.

**Solution:** Set security headers globally at the reverse proxy
or middleware level.

**Baseline:**

```
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

**When to use:**

- Every web application that serves HTML
- API-only backends: subset (HSTS, nosniff)
