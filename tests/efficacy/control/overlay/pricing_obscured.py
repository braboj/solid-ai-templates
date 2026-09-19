"""The pricing algorithm: price(invoice, rules, jurisdiction) -> PricedInvoice."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN

from .errors import PricingError
from .models import Jurisdiction, Product
from .rules import BulkRule, CouponRule, PercentageRule, TieredRule

TWO_PLACES = Decimal("0.01")


@dataclass
class PricedLine:
    product: Product
    quantity: int
    gross: Decimal
    line_discount: Decimal
    net: Decimal
    invoice_discount: Decimal
    taxable: Decimal
    tax: Decimal
    total: Decimal
    applied: list


@dataclass
class PricedInvoice:
    currency: str
    jurisdiction: Jurisdiction
    lines: list
    subtotal: Decimal
    discount_total: Decimal
    taxable_total: Decimal
    tax_total: Decimal
    total: Decimal
    applied: list


def price(invoice, rules, jurisdiction) -> PricedInvoice:
    if not invoice.lines:
        raise PricingError("invoice has no lines")
    ids = [r.rule_id for r in rules]
    if len(ids) != len(set(ids)):
        raise PricingError("two rules share a rule_id")
    cr = [r for r in rules if isinstance(r, CouponRule)]
    kc = {r.code.strip() for r in cr}
    for c in invoice.coupon_codes:
        if c.strip() not in kc:
            raise PricingError(f"unknown coupon code {c!r}")
    lw = []
    for ln in invoice.lines:
        p = ln.product
        q = ln.quantity
        if q < 1:
            raise PricingError("line quantity must be at least one")
        g = p.unit_price * q
        a = g
        ap = []
        t1 = [r for r in rules if isinstance(r, TieredRule) and r.sku == p.sku]
        if t1:
            o = []
            for r in t1:
                u = None
                for mq, up in r.tiers:
                    if q >= mq:
                        u = up
                o.append((a if u is None else u * q, r))
            a, r0 = min(o, key=lambda x: (x[0], x[1].rule_id))
            ap.append(r0.rule_id)
        t2 = [r for r in rules if isinstance(r, BulkRule) and r.sku == p.sku]
        if t2:
            o = []
            for r in t2:
                gr, rem = divmod(q, r.buy)
                o.append((a / q * (gr * r.pay + rem), r))
            a, r0 = min(o, key=lambda x: (x[0], x[1].rule_id))
            ap.append(r0.rule_id)
        t3 = [r for r in rules
              if isinstance(r, PercentageRule) and r.sku == p.sku]
        if t3:
            o = [(a * (Decimal(1) - r.percent / Decimal(100)), r) for r in t3]
            a, r0 = min(o, key=lambda x: (x[0], x[1].rule_id))
            ap.append(r0.rule_id)
        n = a.quantize(TWO_PLACES, rounding=ROUND_HALF_EVEN)
        lw.append((p, q, g,
                   g.quantize(TWO_PLACES, rounding=ROUND_HALF_EVEN) - n, n, ap))
    st = sum((w[4] for w in lw), Decimal("0.00"))
    rn = st
    ai = []
    t4 = [r for r in rules if isinstance(r, PercentageRule) and r.sku is None]
    if t4:
        o = [((rn * (Decimal(1) - r.percent / Decimal(100))).quantize(
            TWO_PLACES, rounding=ROUND_HALF_EVEN), r) for r in t4]
        rn, r0 = min(o, key=lambda x: (x[0], x[1].rule_id))
        ai.append(r0.rule_id)
    cc = {c.strip() for c in invoice.coupon_codes}
    t5 = [r for r in cr if r.code.strip() in cc]
    if t5:
        o = []
        for r in t5:
            if r.percent is not None:
                v = (rn * (Decimal(1) - r.percent / Decimal(100))).quantize(
                    TWO_PLACES, rounding=ROUND_HALF_EVEN)
            else:
                v = (rn - min(r.amount, rn)).quantize(
                    TWO_PLACES, rounding=ROUND_HALF_EVEN)
            o.append((v, r))
        rn, r0 = min(o, key=lambda x: (x[0], x[1].rule_id))
        ai.append(r0.rule_id)
    dt = st - rn
    nets = [w[4] for w in lw]
    cnt = len(nets)
    if st == 0:
        al = [Decimal("0.00")] * cnt
    else:
        es = [dt * n2 / st for n2 in nets]
        tr = [s.quantize(TWO_PLACES, rounding=ROUND_DOWN) for s in es]
        fr = [s - t for s, t in zip(es, tr)]
        cs = int((dt - sum(tr, Decimal("0.00"))) * 100)
        ex = set(sorted(range(cnt), key=lambda i: (-fr[i], i))[:cs])
        al = [tr[i] + TWO_PLACES if i in ex else tr[i] for i in range(cnt)]
    pl = []
    tt = Decimal("0.00")
    for w, ac in zip(lw, al):
        tx = w[4] - ac
        rt = jurisdiction.rates.get(w[0].tax_category,
                                    jurisdiction.default_rate)
        tv = (tx * rt).quantize(TWO_PLACES, rounding=ROUND_HALF_EVEN)
        tt += tv
        pl.append(PricedLine(product=w[0], quantity=w[1], gross=w[2],
                             line_discount=w[3], net=w[4], invoice_discount=ac,
                             taxable=tx, tax=tv, total=tx + tv, applied=w[5]))
    return PricedInvoice(currency=invoice.currency, jurisdiction=jurisdiction,
                         lines=pl, subtotal=st, discount_total=dt,
                         taxable_total=rn, tax_total=tt, total=rn + tt,
                         applied=ai)
