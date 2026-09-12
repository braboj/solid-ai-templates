# tariff — a pricing and invoicing engine with a web UI

Build `tariff`: a Python package that prices invoices against a catalogue of
products, a set of discount rules and a tax jurisdiction, plus a
server-rendered web application for editing that data and building invoices.

This document fixes the domain semantics, the public Python API, the HTTP
routes and the export formats, because other software depends on them. Every
other decision is yours.

## 1. Constraints

- Python 3.12. The package is named `tariff` and installs with
  `pip install .`.
- The web application uses Flask and Jinja templates. Its only client-side
  dependency is HTMX, loaded from a single vendored script file. No build
  step, no bundler, no other JavaScript framework.
- No network access at runtime, in tests, or during installation beyond
  what `pip install .` needs.
- Persistence is SQLite in a single file. The application owns the schema
  and creates it on first run.
- The pages must work with JavaScript disabled: HTMX enhances the invoice
  builder, and every form still submits and re-renders without it.
- The rendered HTML must be valid.
- `import tariff` must work without Flask installed and without touching
  the database. The pricing engine does not depend on the web application.

## 2. Money

- Every monetary value is a `decimal.Decimal`. Floats appear nowhere in the
  pricing path.
- An invoice has exactly one currency, given as an ISO 4217 code. Every
  currency this application handles has two minor digits.
- Rounding is half-even to two decimal places, and happens only at the
  points section 4 names. Intermediate arithmetic stays exact.

## 3. Domain

### 3.1 Product

| Field | Type | Notes |
|---|---|---|
| `sku` | `str` | unique, non-empty |
| `name` | `str` | non-empty |
| `unit_price` | `Decimal` | at least zero |
| `tax_category` | `str` | non-empty; free text, matched against a jurisdiction's rate table |

### 3.2 Discount rules

Four kinds. Each carries a `rule_id`, unique across the set.

| Kind | Scope | Fields | Meaning |
|---|---|---|---|
| percentage | a product, or the whole invoice | `percent` | reduces the running amount by that percentage |
| bulk | a product | `buy`, `pay` | for every complete group of `buy` units, charge for `pay` |
| tiered | a product | `tiers` — a list of `(min_quantity, unit_price)` | replaces the unit price for every unit once the quantity reaches a tier |
| coupon | the whole invoice | `code`, and exactly one of `percent` or `amount` | applies only when the invoice carries the code |

A rule is invalid, and constructing it raises, when:

- `percent` is not greater than zero, or is greater than 100
- `buy` is not greater than `pay`, or `pay` is less than one
- `tiers` is empty, a `min_quantity` is less than one, the tiers are not
  strictly increasing by `min_quantity`, or a tier's `unit_price` is
  negative
- a coupon's `code` is empty, or it carries neither or both of `percent`
  and `amount`, or its `amount` is not greater than zero

### 3.3 Jurisdiction

| Field | Type | Notes |
|---|---|---|
| `code` | `str` | unique, non-empty |
| `name` | `str` | non-empty |
| `rates` | `dict[str, Decimal]` | tax category to rate, where `0.19` means 19% |
| `default_rate` | `Decimal` | used for a category the table does not name |

### 3.4 Invoice

An invoice carries a currency, an ordered list of lines, and zero or more
coupon codes. A line carries a product and an integer quantity of at least
one.

## 4. Pricing

`price(invoice, rules, jurisdiction)` returns a priced invoice. The
algorithm is fixed.

### 4.1 Per line

1. `gross = unit_price * quantity`, exact.
2. Line-scoped rules apply to the line's product in this kind order:
   **tiered, then bulk, then percentage**.
3. At most one rule of each kind applies to a line. Where several rules of
   one kind match the product, the one producing the lowest resulting
   amount applies; a tie is broken by `rule_id` ascending.
4. Each applied rule reads the running amount and replaces it:
   - **tiered** — the applicable tier is the one with the greatest
     `min_quantity` less than or equal to the quantity; a quantity exactly
     at a tier's `min_quantity` reaches that tier. Where no tier applies,
     the rule changes nothing. The running amount becomes
     `tier_unit_price * quantity`.
   - **bulk** — with `groups, remainder = divmod(quantity, buy)`, the
     chargeable units are `groups * pay + remainder`, and the running
     amount becomes `running_amount / quantity * chargeable_units`.
   - **percentage** — the running amount becomes
     `running_amount * (1 - percent / 100)`.
5. `net` is the running amount rounded. `line_discount = gross - net`,
   where `gross` is rounded for this subtraction only.

### 4.2 Per invoice

6. `subtotal` is the sum of the lines' `net`.
7. Invoice-scoped rules apply in this kind order: **percentage, then
   coupon**. A coupon applies only when the invoice carries its code. The
   same one-per-kind, lowest-result, `rule_id`-ascending selection as
   step 3 applies.
8. Each applied rule reads the running amount and replaces it, rounding
   after each:
   - **percentage** — `running_amount * (1 - percent / 100)`.
   - **coupon with `percent`** — the same.
   - **coupon with `amount`** — `running_amount - min(amount,
     running_amount)`. The invoice never goes negative.
9. `discounted_subtotal` is the running amount, and
   `discount_total = subtotal - discounted_subtotal`.

### 4.3 Allocation and tax

10. `discount_total` is allocated across the lines pro rata by `net`, by
    largest remainder: each line's exact share is
    `discount_total * net / subtotal`, truncated to two decimals; the
    remaining cents go one each to the lines with the largest truncated
    fraction, ties broken by line order. The allocated parts sum to
    `discount_total` exactly. Where `subtotal` is zero, every allocation is
    zero.
11. `taxable = net - allocated_discount` per line. The lines' `taxable`
    sums to `discounted_subtotal`.
12. `tax = round(taxable * rate)` per line, where `rate` is the
    jurisdiction's rate for the product's tax category, or its
    `default_rate` where the table does not name that category.
13. `tax_total` is the sum of the lines' `tax`, and
    `total = discounted_subtotal + tax_total`.

### 4.4 Refusals

`price` raises when the invoice has no lines, when a line's quantity is
less than one, when two rules share a `rule_id`, or when the invoice
carries a coupon code no rule defines. Every exception this package raises
on purpose derives from `TariffError`.

## 5. Public Python API

Importable from the `tariff` package root, with these names and
signatures:

```python
Product(sku, name, unit_price, tax_category)
Catalog(products=())            # .add(product), .get(sku), iterable, len()
InvoiceLine(product, quantity)
Invoice(currency, lines, coupon_codes=())
Jurisdiction(code, name, rates, default_rate)

PercentageRule(rule_id, percent, sku=None)   # sku None means invoice scope
BulkRule(rule_id, sku, buy, pay)
TieredRule(rule_id, sku, tiers)
CouponRule(rule_id, code, percent=None, amount=None)

price(invoice, rules, jurisdiction)          # -> PricedInvoice
TariffError                                   # base of every raised error
```

`Catalog.get` raises for an unknown sku.

A `PricedInvoice` exposes `currency`, `jurisdiction`, `lines`, `subtotal`,
`discount_total`, `taxable_total`, `tax_total`, `total`, and `applied` —
the `rule_id`s of the invoice-scoped rules that applied, in application
order.

A priced line exposes `product`, `quantity`, `gross`, `line_discount`,
`net`, `invoice_discount`, `taxable`, `tax`, `total`, and `applied` — the
`rule_id`s of the line-scoped rules that applied, in application order.

## 6. Web application

A Flask application factory named `create_app` in the package, taking the
database path and returning the application. Every route below exists with
the method and path given.

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | dashboard linking to the pages below |
| GET | `/products` | product list and a creation form |
| POST | `/products` | create a product |
| POST | `/products/<sku>/delete` | delete a product |
| GET | `/rules` | rule list and a creation form |
| POST | `/rules` | create a rule |
| POST | `/rules/<rule_id>/delete` | delete a rule |
| GET | `/jurisdictions` | jurisdiction list and a creation form |
| POST | `/jurisdictions` | create a jurisdiction |
| POST | `/jurisdictions/<code>/delete` | delete a jurisdiction |
| GET | `/invoices/new` | the invoice builder |
| POST | `/invoices/preview` | re-price the builder's current state, returning the priced-invoice fragment |
| POST | `/invoices` | save the invoice and redirect to its page |
| GET | `/invoices/<invoice_id>` | a saved invoice |
| GET | `/invoices/<invoice_id>/export.json` | JSON export |
| GET | `/invoices/<invoice_id>/export.csv` | CSV export |
| GET | `/invoices/<invoice_id>/print` | a printable invoice |

### 6.1 Form fields

Other software drives these forms, so the field names are fixed. Anything
not named here is yours.

| Route | Fields |
|---|---|
| POST `/products` | `sku`, `name`, `unit_price`, `tax_category` |
| POST `/rules` | `rule_id`, `kind` (one of `percentage`, `bulk`, `tiered`, `coupon`), `sku` (empty means invoice scope), and the fields its kind needs: `percent`, `buy`, `pay`, `tiers`, `code`, `amount` |
| POST `/jurisdictions` | `code`, `name`, `default_rate`, `rates` |
| POST `/invoices/preview`, POST `/invoices` | `jurisdiction`, `currency`, `sku` and `quantity` repeated once per line and read pairwise in order, `coupon_codes` |

Three fields carry more than one value in one control:

- `tiers` — `min_quantity:unit_price` pairs separated by commas, as
  `1:10.00,10:9.00,50:8.00`
- `rates` — `category=rate` pairs separated by commas, as
  `standard=0.19,reduced=0.07`
- `coupon_codes` — codes separated by commas, and empty for none

Behaviour:

- The invoice builder lets a person pick a jurisdiction, add and remove
  lines by sku and quantity, and enter coupon codes. Every change re-prices
  through `POST /invoices/preview`.
- The builder is one form whose action is `/invoices/preview`. Its save
  control carries `formaction="/invoices"`, so the one form serves both the
  re-price and the save.
- `POST /invoices/preview` returns an HTML fragment — the priced invoice
  table and totals, not a whole page — when the request carries the
  `HX-Request` header, which is what HTMX sends. Without that header it
  renders the whole page, which is the JavaScript-disabled path, and both
  show the same figures.
- `POST /invoices/preview` refuses a body naming an unknown sku or an
  unknown jurisdiction code, or carrying a quantity below one, with 400.
  That is bad input rather than a missing page, so it is not a 404.
- The priced fragment shows, per line, the sku, name, quantity, unit price,
  gross, line discount, net, allocated invoice discount, taxable, tax and
  total, and shows the invoice's subtotal, discount total, taxable total,
  tax total and total.
- Every POST validates on the server and re-renders the form with a
  message naming the field on bad input. Nothing is written on a failed
  validation.
- Every POST form carries a CSRF token, and a POST without a valid token is
  refused with 400 or 403.
- Unknown sku, unknown invoice id, and unknown jurisdiction code return
  404.

## 7. Export formats

Both exports are byte-stable for the same invoice.

**JSON**, `Content-Type: application/json`. Monetary values are strings
with exactly two decimals. Keys appear in this order:

```json
{
  "invoice_id": 1,
  "currency": "EUR",
  "jurisdiction": "DE",
  "lines": [
    {
      "sku": "WID-1",
      "name": "Widget",
      "quantity": 12,
      "unit_price": "10.00",
      "gross": "120.00",
      "line_discount": "12.00",
      "net": "108.00",
      "invoice_discount": "15.66",
      "taxable": "92.34",
      "tax": "17.54",
      "total": "109.88",
      "applied": ["r-tier-wid"]
    }
  ],
  "subtotal": "228.35",
  "discount_total": "33.11",
  "taxable_total": "195.24",
  "tax_total": "31.83",
  "total": "227.07",
  "applied": ["r-pct-all", "c-welcome"]
}
```

**CSV**, `Content-Type: text/csv; charset=utf-8`, LF line endings, no byte
order mark, one header row, one row per line, and a final total row whose
`sku` is `TOTAL` and whose `name`, `quantity` and `unit_price` are empty.
The header is exactly:

```
sku,name,quantity,unit_price,gross,line_discount,net,invoice_discount,taxable,tax,total
```

The total row's `gross` is the sum of the lines' gross and its
`line_discount` the sum of theirs, so the row's own arithmetic closes: for
the worked example, 250.25 less 21.90 is the 228.35 the invoice calls its
subtotal. Its `net` is that subtotal, and its `invoice_discount`, `taxable`,
`tax` and `total` are the invoice's `discount_total`, `taxable_total`,
`tax_total` and `total`.

## 8. Seed fixture

The application seeds an empty database with exactly this data, and a
documented command re-seeds it.

Products, priced in EUR:

| sku | name | unit_price | tax_category |
|---|---|---|---|
| WID-1 | Widget | 10.00 | standard |
| GAD-2 | Gadget | 24.50 | standard |
| BOK-3 | Handbook | 12.00 | reduced |
| SRV-4 | Support hour | 80.00 | standard |
| SEE-5 | Seed pack | 3.75 | zero |

Jurisdictions:

| code | name | standard | reduced | zero | default_rate |
|---|---|---|---|---|---|
| DE | Germany | 0.19 | 0.07 | 0.00 | 0.19 |
| IE | Ireland | 0.23 | 0.135 | 0.00 | 0.23 |

Rules:

| rule_id | kind | scope | detail |
|---|---|---|---|
| r-tier-wid | tiered | WID-1 | (1, 10.00), (10, 9.00), (50, 8.00) |
| r-bulk-see | bulk | SEE-5 | buy 3, pay 2 |
| r-pct-bok | percentage | BOK-3 | 10 |
| r-pct-all | percentage | invoice | 5 |
| c-welcome | coupon | invoice | code WELCOME, percent 10 |
| c-tenoff | coupon | invoice | code TENOFF, amount 10.00 |

## 9. Worked example

Jurisdiction DE, currency EUR, coupon codes `WELCOME`, and the lines
below. Your implementation must reproduce every figure.

| sku | qty | unit | gross | line rules | net | allocated | taxable | rate | tax | total |
|---|---|---|---|---|---|---|---|---|---|---|
| WID-1 | 12 | 10.00 | 120.00 | r-tier-wid | 108.00 | 15.66 | 92.34 | 0.19 | 17.54 | 109.88 |
| SEE-5 | 7 | 3.75 | 26.25 | r-bulk-see | 18.75 | 2.72 | 16.03 | 0.00 | 0.00 | 16.03 |
| BOK-3 | 2 | 12.00 | 24.00 | r-pct-bok | 21.60 | 3.13 | 18.47 | 0.07 | 1.29 | 19.76 |
| SRV-4 | 1 | 80.00 | 80.00 | none | 80.00 | 11.60 | 68.40 | 0.19 | 13.00 | 81.40 |

| Figure | Value |
|---|---|
| subtotal | 228.35 |
| after r-pct-all | 216.93 |
| after c-welcome | 195.24 |
| discount_total | 33.11 |
| taxable_total | 195.24 |
| tax_total | 31.83 |
| total | 227.07 |

The allocation is the sharpest step. The exact shares are 15.6596…,
2.7186…, 3.1319… and 11.5997…; truncated they sum to 33.08, and the three
remaining cents go to the three largest fractions — SRV-4, WID-1 and
SEE-5 — leaving BOK-3 at 3.13.

## 10. Done

- `pip install .` succeeds in a clean virtual environment, and
  `python -c "import tariff"` works.
- The application starts, serves `/`, and every route in section 6 works
  against the seed fixture.
- Your own tests pass.
- A reader can install it, seed it, run it and price an invoice from the
  documentation you ship.
