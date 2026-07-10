# Backend — HTTP Conventions
[ID: backend-http]

## Handler design
- Handlers are thin: decode request → call service → encode response
- No business logic in handlers — delegate to a service layer
- Validate all incoming request data before processing

## URI design
- Path segments MUST be lowercase with hyphens as word separators —
  underscores and camelCase are not permitted
- Paths MUST use nouns, not verbs: `/orders` not `/getOrders`
- Collection resources MUST use plural nouns: `/orders`, `/products`
- Individual resources MUST be addressed under their collection:
  `/orders/{orderId}`
- Sub-resources MUST be nested under their parent: `/customers/{id}/orders`
- A URI MUST NOT end with a trailing slash
- Paths MUST use American English spelling with no abbreviations or acronyms

## Query parameters
- Query parameter names MUST use camelCase
- Query parameters MUST be used for filtering, sorting, and pagination —
  not for resource identity (use path segments for that)
- The following names are reserved for framework-level use and MUST NOT
  be repurposed: `limit`, `skip`, `offset`, `expand`, `sortedBy`
- Parse a typed query parameter explicitly so you can distinguish three
  states: absent (use the default), present-and-valid (use it), and
  present-but-invalid (raise 400). Do NOT rely on a framework's
  type-coercing helper (e.g. Flask `request.args.get('n', type=int)`)
  that returns the default on a malformed value — it silently turns a
  client error into a successful default-valued 200

## Request headers
- All HTTP headers MUST follow Hyphenated-Pascal-Case casing:
  `Api-Correlation-Id`, `Accept-Language`
- Custom headers SHOULD NOT use the `X-` prefix — this convention was
  deprecated by RFC 6648; use a vendor or application-specific prefix instead

## HTTP methods
| Method | Use for | Idempotent |
|--------|---------|-----------|
| GET | Retrieve a resource or collection — no side effects | Yes |
| POST | Create a new resource — server assigns URI | No |
| PUT | Replace a resource entirely | Yes |
| PATCH | Partially update a resource | No |
| DELETE | Remove a resource | Yes |

## Resource representation
- JSON MUST be the default serialisation format; XML MAY be used where
  explicitly required by the consuming system
- Field types MUST conform to the relevant ISO standard:
  - Date and time values: ISO 8601
  - Language codes: ISO 639
  - Country codes: ISO 3166-1 alpha-2
  - Currency codes: ISO 4217
- Any integer that exceeds 2^53 − 1 (9007199254740991) MUST be serialised
  as a string — JavaScript cannot represent larger integers precisely
- Endpoints that serialise computed floats MUST reject non-finite values:
  `NaN`/`Infinity` are not valid RFC 8259 JSON. Configure the encoder to
  reject them (e.g. `allow_nan=false`) so it fails loud at the
  serialisation boundary (a 500) instead of emitting a bare `NaN` token
  that strict parsers reject; represent an undefined value as `null`
  (normalised before serialisation) and document the field as nullable
  in the contract
- Responses MUST contain only the fields needed by the caller — do not pad
  payloads with fields that are not consumed

## HATEOAS
- Embed hyperlinks in responses to enable resource discovery
- Use a `links` array with `href`, `rel`, `type`, and `media` fields:
  ```json
  "links": [
    {
      "href": "invoices/f9c3b2a1-0d4e-4f8b-9c7a-1e2d3f4a5b6c",
      "rel": "invoice",
      "type": "paymentSummary",
      "media": "application/pdf"
    }
  ]
  ```
- Support at minimum: `self`, `next`, `prev` relations on paginated collections

## Error responses
- Use consistent error response shape across all endpoints
- Follow RFC 9457 (`application/problem+json`) for error format
- Use 4xx for client errors, 5xx for server errors — never use 200 for errors
- Never return stack traces, internal paths, or implementation details to the
  client
- Set explicit `Content-Type: application/json` on all JSON responses

## Authentication and authorisation
- All API traffic MUST be served over HTTPS — plain HTTP is not acceptable
- Access tokens MUST have a finite lifetime; use JWT or an equivalent
  short-lived token mechanism
- Every external API endpoint MUST enforce both authentication and
  authorisation
- Internal API endpoints SHOULD require authentication at minimum
- Write endpoints MUST NOT be accessible without a valid authenticated identity