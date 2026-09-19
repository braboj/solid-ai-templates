"""Build the rubric control's trees, so the judge can be validated.

The benchmark's primary dimensions are a model's opinion, and an opinion that
never changes measures nothing. This builds three trees from one pinned
application and leaves them where `judge.py` finds them: the application
unaltered, a deliberately damaged copy, and a deliberately improved one. All
three pass the same test suite, so what the judge sees between them is
structure and nothing else.

Reading the result is in README.md. What matters here is that a run whose
damaged tree scores no worse, or whose improved tree scores no better, has
found something about the rubric rather than about the arms.

    py tests/efficacy/control/control.py --root C:/efficacy/control-2026-09-20
    py tests/efficacy/judge.py --root C:/efficacy/control-2026-09-20

`base/` is an input, not an artifact: it is one trial's output, pinned, and it
is never regenerated. Regenerating it would compare a later run against a
different application, and the before-and-after numbers would mean nothing.
Every edit below is an exact-text swap that refuses when its target is absent,
so a base that drifts stops the control instead of silently mutating less.
"""

import argparse
import hashlib
import io
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "base.zip")
OVERLAY = os.path.join(HERE, "overlay")

# The pinned application's archive, by content. The build refuses on any other
# digest: a base that changed would compare a later run against a different
# application, and every reading this control has taken would silently stop
# meaning what it says. It is an archive rather than a directory so that no
# linter over this repository's own Python reads one trial's generated output
# as source to be brought into line.
BASE_SHA256 = "38b9a1f262ebae7b5c858178468ff53257c3308b6a57a7caa81db6fbe4671f0c"

# The domain modules the damaged tree merges into one, in the order they are
# concatenated: errors before the objects that raise them, rules before the
# algorithm that applies them.
MERGED = ("errors", "models", "rules", "pricing")

TRIALS = ("base-1", "degraded-1", "improved-1", "improved-2",
          "obscured-1")


class ControlError(Exception):
    """A mutation could not be applied to the tree as written."""


def read(root, rel):
    with io.open(os.path.join(root, rel), encoding="utf-8") as handle:
        return handle.read()


def write(root, rel, text):
    with io.open(os.path.join(root, rel), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(text)


def swap(text, old, new, where):
    """Replace `old` once, refusing when it is absent.

    The refusal is the point: these are exact-text edits against a pinned
    application, so a target that has gone missing means the base moved and
    the control is no longer building what it claims to build.
    """
    if old not in text:
        raise ControlError("%s: the text to replace is not in the tree; the "
                           "base has moved and this control no longer "
                           "describes it" % where)
    return text.replace(old, new, 1)


def degrade(tree):
    """Damage the tree in three ways a reviewer would name without hesitating.

    The domain becomes one module; it imports the web framework; and the
    package's exceptions lose their common base. None of it changes behaviour,
    so the suite still passes and the judge is reading structure alone.
    """
    import re

    parts = []
    for name in MERGED:
        text = read(tree, "tariff/%s.py" % name)
        text = re.sub(r"(?m)^from \.\w+ import .*\n", "", text)
        text = re.sub(r'(?m)^""".*?"""\n', "", text, count=1, flags=re.S)
        parts.append(text.strip("\n"))

    core = ('"""tariff core: errors, models, rules and the pricing '
            'algorithm."""\n\n'
            "from dataclasses import dataclass, field\n"
            "from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN\n\n"
            "from flask import current_app\n\n"
            + "\n\n\n".join(parts) + "\n")

    core = swap(core, 'class TariffError(Exception):\n'
                '    """Base of every exception this package raises on '
                'purpose."""\n',
                "TariffError = Exception\n", "the package's error base")
    for name in ("ValidationError", "CatalogError", "PricingError"):
        core = swap(core, "class %s(TariffError):" % name,
                    "class %s(Exception):" % name, "%s's base" % name)

    core = swap(core,
                "def price(invoice, rules, jurisdiction) -> PricedInvoice:",
                "def price(invoice, rules, jurisdiction) -> PricedInvoice:\n"
                "    try:\n"
                "        rounding = current_app.config.get("
                '"TARIFF_ROUNDING", ROUND_HALF_EVEN)\n'
                "    except RuntimeError:\n"
                "        rounding = ROUND_HALF_EVEN\n"
                "    del rounding", "the domain's framework read")

    write(tree, "tariff/core.py", core)
    for name in MERGED:
        os.remove(os.path.join(tree, "tariff/%s.py" % name))

    init = read(tree, "tariff/__init__.py")
    init = re.sub(r"(?m)^from \.(errors|models|pricing|rules) import .*\n",
                  "", init)
    init = swap(init, '"""\n\n',
                '"""\n\nfrom .core import (BulkRule, Catalog, CatalogError,\n'
                "                   CouponRule, Invoice, InvoiceLine,\n"
                "                   Jurisdiction, PercentageRule,\n"
                "                   PricedInvoice, PricedLine, PricingError,\n"
                "                   Product, TariffError, TieredRule,\n"
                "                   ValidationError, price)\n\n",
                "the package's re-exports")
    write(tree, "tariff/__init__.py", init)

    for dirpath, _, files in os.walk(os.path.join(tree, "tariff", "web")):
        for name in files:
            if not name.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), tree)
            text = original = read(tree, rel)
            text = re.sub(r"(?m)^from \.\.(errors|models|pricing|rules) "
                          r"import ", "from ..core import ", text)
            text = re.sub(r"(?m)^from \.\.\.(errors|models|pricing|rules) "
                          r"import ", "from ...core import ", text)
            if text != original:
                write(tree, rel, text)


def improve(tree):
    """Give the rule kinds a contract and a registry, and one error hierarchy.

    Every edit removes something a reviewer names: dispatch on concrete type,
    a hardcoded list of kinds, a template branching on a class name, and error
    classes outside the package's own base. Behaviour is unchanged.
    """
    shutil.copy2(os.path.join(OVERLAY, "rules.py"),
                 os.path.join(tree, "tariff", "rules.py"))

    pricing = read(tree, "tariff/pricing.py")
    pricing = swap(pricing, "from .rules import BulkRule, CouponRule, "
                   "PercentageRule, TieredRule\n", "", "the pricing imports")
    pricing = swap(pricing, APPLY_HELPERS, BY_STAGE, "the apply helpers")
    pricing = swap(pricing, LINE_LADDER, LINE_DISPATCH, "the line dispatch")
    pricing = swap(pricing,
                   "    coupon_rules = [r for r in rules if isinstance(r, "
                   "CouponRule)]\n",
                   '    coupon_rules = [r for r in rules if r.kind == '
                   '"coupon"]\n', "the coupon collection")
    pricing = swap(pricing, INVOICE_LADDER, INVOICE_DISPATCH,
                   "the invoice dispatch")
    write(tree, "tariff/pricing.py", pricing)

    formatting = read(tree, "tariff/web/formatting.py")
    formatting = swap(formatting, "class FieldError(Exception):",
                      "from ..errors import TariffError\n\n\n"
                      "class FieldError(TariffError):", "FieldError's base")
    write(tree, "tariff/web/formatting.py", formatting)

    view = read(tree, "tariff/web/views/rules.py")
    view = swap(view, "from ...rules import BulkRule, CouponRule, "
                "PercentageRule, TieredRule",
                "from ...rules import BulkRule, CouponRule, PercentageRule, "
                "TieredRule, kinds", "the rules view's imports")
    view = swap(view, 'KINDS = ("percentage", "bulk", "tiered", "coupon")',
                "KINDS = kinds()", "the hardcoded kinds")
    write(tree, "tariff/web/views/rules.py", view)

    invoices = read(tree, "tariff/web/views/invoices.py")
    invoices = swap(invoices, "from ...errors import PricingError",
                    "from ...errors import PricingError, TariffError",
                    "the invoices view's imports")
    invoices = swap(invoices, "class _BadRequest(Exception):",
                    "class _BadRequest(TariffError):", "_BadRequest's base")
    write(tree, "tariff/web/views/invoices.py", invoices)

    db = read(tree, "tariff/web/db.py")
    db = swap(db, ROW_LADDERS, ROW_TABLES, "the persistence ladders")
    db = swap(db, "from ..rules import BulkRule, CouponRule, PercentageRule, "
              "TieredRule",
              "from ..errors import ValidationError\n"
              "from ..rules import BulkRule, CouponRule, PercentageRule, "
              "TieredRule", "the db imports")
    write(tree, "tariff/web/db.py", db)

    template = read(tree, "tariff/web/templates/rules.html")
    template = swap(template, KIND_LADDER, KIND_CELLS, "the template's ladder")
    write(tree, "tariff/web/templates/rules.html", template)


def improve_further(tree):
    """Take the improvement into persistence, so no module names a kind.

    `improved-1` leaves the store mapping each kind by hand, which is what
    the maintainability anchor's 5 rules out. Here a rule states its own
    terms, the store maps term names onto its columns, and a codec belongs
    to a column rather than to a kind.
    """
    improve(tree)

    rules = read(tree, "tariff/rules.py")
    rules = swap(rules, "from abc import ABC, abstractmethod",
                 "import dataclasses\nfrom abc import ABC, abstractmethod",
                 "the rules module's imports")
    rules = swap(rules, TERMS_ANCHOR, TERMS_NEW, "the rule contract's terms")
    write(tree, "tariff/rules.py", rules)

    db = read(tree, "tariff/web/db.py")
    db = swap(db, ROW_TABLES, ROW_TERMS, "the persistence tables")
    db = swap(db, "from ..rules import BulkRule, CouponRule, PercentageRule, "
              "TieredRule", "from ..rules import rule_class",
              "the db module's rule imports")
    write(tree, "tariff/web/db.py", db)


def obscure(tree):
    """Damage what a reader has to hold in their head, and nothing else.

    The module boundaries, the error hierarchy and the dispatch are left
    exactly as the base has them: only the pricing algorithm is inlined into
    one long function with abbreviated names. A rubric row that reads
    function length, nesting and names then has something to move on, and
    every other row has nothing.
    """
    shutil.copy2(os.path.join(OVERLAY, "pricing_obscured.py"),
                 os.path.join(tree, "tariff", "pricing.py"))


# Every entity a variant is supposed to change, with what each tree must read
# after the build. A control whose mutation silently did nothing reports the
# tree it never touched as clean, so the build refuses rather than hand that
# result to a reader.
LANDINGS = (
    ("tariff/core.py exists", lambda t: os.path.isfile(
        os.path.join(t, "tariff", "core.py")),
     {"base-1": False, "degraded-1": True, "improved-1": False, "improved-2": False, "obscured-1": False}),

    # Read against the domain alone: the web package imports flask in every
    # tree, so a whole-tree probe would answer yes whatever was done.
    ("the domain imports flask", lambda t: "from flask import current_app"
     in domain(t), {"base-1": False, "degraded-1": True,
                    "improved-1": False, "improved-2": False, "obscured-1": False}),
    ("ValidationError derives from TariffError",
     lambda t: "class ValidationError(TariffError):" in whole(t),
     {"base-1": True, "degraded-1": False, "improved-1": True, "improved-2": True, "obscured-1": True}),

    # The damaged tree keeps the ladder: merging the modules moves it into
    # core.py rather than removing it. Only the improved tree loses it.
    ("pricing dispatches on concrete type",
     lambda t: "isinstance(r, TieredRule)" in whole(t),
     {"base-1": True, "degraded-1": True, "improved-1": False, "improved-2": False, "obscured-1": True}),
    ("the rules declare a contract", lambda t: "class Rule(ABC):" in whole(t),
     {"base-1": False, "degraded-1": False, "improved-1": True, "improved-2": True, "obscured-1": False}),
    ("the kinds are hardcoded",
     lambda t: 'KINDS = ("percentage", "bulk", "tiered", "coupon")'
     in whole(t), {"base-1": True, "degraded-1": True,
                   "improved-1": False, "improved-2": False, "obscured-1": True}),
    ("an error class sits outside the hierarchy",
     lambda t: "class _BadRequest(Exception):" in whole(t),
     {"base-1": True, "degraded-1": True, "improved-1": False, "improved-2": False, "obscured-1": True}),
    ("the template branches on a class name",
     lambda t: "__class__.__name__" in whole(t),
     {"base-1": True, "degraded-1": True, "improved-1": False, "improved-2": False, "obscured-1": True}),

    # The seed fixture names a kind per sample row in every tree, and has to:
    # that is data. What this reads is whether the store DISPATCHES on kind,
    # by a ladder or by a table of its own.
    ("the store dispatches on a rule kind",
     lambda t: ('kind == "tiered"' in store(t)
                or "isinstance(rule, TieredRule)" in store(t)
                or "_TO_ROW = {" in store(t)),
     {"base-1": True, "degraded-1": True, "improved-1": True,
      "improved-2": False, "obscured-1": True}),

    ("the pricing algorithm is broken into named steps",
     lambda t: "def _price_line(" in whole(t),
     {"base-1": True, "degraded-1": True, "improved-1": True,
      "improved-2": True, "obscured-1": False}),
)

_CACHE = {}


def domain(tree):
    """The domain package's own modules, without the web package beneath it."""
    chunks = []
    for name in sorted(os.listdir(os.path.join(tree, "tariff"))):
        if not name.endswith(".py"):
            continue
        with io.open(os.path.join(tree, "tariff", name),
                     encoding="utf-8") as handle:
            chunks.append(handle.read())
    return "\n".join(chunks)


def store(tree):
    """The persistence module, which is where a kind is named or is not."""
    with io.open(os.path.join(tree, "tariff", "web", "db.py"),
                 encoding="utf-8") as handle:
        return handle.read()


def whole(tree):
    """Every text file of a tree, concatenated, for the landing checks."""
    if tree in _CACHE:
        return _CACHE[tree]
    chunks = []
    for dirpath, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if os.path.splitext(name)[1] not in (".py", ".html"):
                continue
            with io.open(os.path.join(dirpath, name), encoding="utf-8",
                         errors="replace") as handle:
                chunks.append(handle.read())
    _CACHE[tree] = "\n".join(chunks)
    return _CACHE[tree]


def pinned():
    """The base archive, refusing any content but the one pinned above."""
    with io.open(BASE, "rb") as handle:
        data = handle.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != BASE_SHA256:
        raise ControlError("base.zip is %s, not the pinned %s; the control's "
                           "application has changed and its recorded readings "
                           "no longer describe it" % (digest, BASE_SHA256))
    return data


def build(root):
    """Write the three trees where `judge.py` reads them."""
    data = pinned()
    scoring = os.path.abspath(root).rstrip("\\/") + "-scoring"
    made = {}
    for trial in TRIALS:
        tree = os.path.join(scoring, "scoring", trial, "tree", trial)
        if os.path.isdir(tree):
            shutil.rmtree(tree)
        os.makedirs(tree)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(tree)
        made[trial] = tree
    degrade(made["degraded-1"])
    improve(made["improved-1"])
    improve_further(made["improved-2"])
    obscure(made["obscured-1"])
    _CACHE.clear()
    return made


def landings(made):
    """Each entity a variant claims to change, read back off the trees."""
    rows = []
    for label, probe, expected in LANDINGS:
        actual = {trial: probe(tree) for trial, tree in sorted(made.items())}
        rows.append((label, actual, actual == expected))
    return rows


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="the run root to build beside; the "
                        "trees land under <root>-scoring/scoring/")
    parser.add_argument("--self-test", action="store_true",
                        help="build into a temporary directory and check "
                        "every mutation landed, then throw it away")
    options = parser.parse_args(argv)

    if options.self_test:
        scratch = tempfile.mkdtemp(prefix="efficacy-control-")
        try:
            made = build(os.path.join(scratch, "run"))
            rows = landings(made)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    elif options.root:
        made = build(options.root)
        rows = landings(made)
    else:
        print("--root is required unless --self-test is given")
        return 2

    failed = 0
    for label, actual, ok in rows:
        failed += 0 if ok else 1
        print("  %-4s %-44s %s" % ("ok" if ok else "FAIL", label,
                                   "  ".join("%s=%s" % (trial, "yes" if value
                                                        else "no")
                                             for trial, value in
                                             sorted(actual.items()))))
    if failed:
        print("VERDICT: FAIL - %d mutation(s) did not land; the trees do not "
              "differ as this control claims" % failed)
        return 1
    if not options.self_test:
        print("built %s under %s" % (", ".join(TRIALS),
                                     os.path.abspath(options.root).rstrip(
                                         "\\/") + "-scoring"))
        print("next: py tests/efficacy/judge.py --root %s" % options.root)
    print("VERDICT: PASS - %d mutation(s) landed" % len(rows))
    return 0


APPLY_HELPERS = '''def _apply_tiered(rule: TieredRule, amount: Decimal, quantity: int) -> Decimal:
    applicable_price = None
    for min_quantity, unit_price in rule.tiers:
        if quantity >= min_quantity:
            applicable_price = unit_price
    if applicable_price is None:
        return amount
    return applicable_price * quantity


def _apply_bulk(rule: BulkRule, amount: Decimal, quantity: int) -> Decimal:
    groups, remainder = divmod(quantity, rule.buy)
    chargeable_units = groups * rule.pay + remainder
    return amount / quantity * chargeable_units


def _apply_percentage(percent: Decimal, amount: Decimal) -> Decimal:
    return amount * (Decimal(1) - percent / Decimal(100))


'''

BY_STAGE = '''def _by_stage(rules, competes):
    """The rules that compete, grouped into the stages they apply in.

    The algorithm knows only that stages run in order and that one rule wins
    each; which kinds exist, and in what order they apply, the kinds declare.
    """
    matched = [rule for rule in rules if competes(rule)]
    return [[rule for rule in matched if rule.stage == stage]
            for stage in sorted({rule.stage for rule in matched})]


'''

LINE_LADDER = '''    tiered_candidates = [r for r in rules if isinstance(r, TieredRule) and r.sku == product.sku]
    if tiered_candidates:
        options = [(_apply_tiered(r, amount, quantity), r) for r in tiered_candidates]
        amount, rule = _select(options)
        applied.append(rule.rule_id)

    bulk_candidates = [r for r in rules if isinstance(r, BulkRule) and r.sku == product.sku]
    if bulk_candidates:
        options = [(_apply_bulk(r, amount, quantity), r) for r in bulk_candidates]
        amount, rule = _select(options)
        applied.append(rule.rule_id)

    pct_candidates = [r for r in rules if isinstance(r, PercentageRule) and r.sku == product.sku]
    if pct_candidates:
        options = [(_apply_percentage(r.percent, amount), r) for r in pct_candidates]
        amount, rule = _select(options)
        applied.append(rule.rule_id)
'''

LINE_DISPATCH = '''    for candidates in _by_stage(rules, lambda r: r.matches_line(product)):
        options = [(r.apply(amount, quantity), r) for r in candidates]
        amount, rule = _select(options)
        applied.append(rule.rule_id)
'''

INVOICE_LADDER = '''    pct_candidates = [r for r in rules if isinstance(r, PercentageRule) and r.sku is None]
    if pct_candidates:
        options = [(_round2(_apply_percentage(r.percent, running)), r) for r in pct_candidates]
        running, rule = _select(options)
        applied_invoice.append(rule.rule_id)

    carried_codes = {c.strip() for c in invoice.coupon_codes}
    coupon_candidates = [r for r in coupon_rules if r.code.strip() in carried_codes]
    if coupon_candidates:
        options = []
        for r in coupon_candidates:
            if r.percent is not None:
                amount = _round2(_apply_percentage(r.percent, running))
            else:
                amount = _round2(running - min(r.amount, running))
            options.append((amount, r))
        running, rule = _select(options)
        applied_invoice.append(rule.rule_id)
'''

INVOICE_DISPATCH = '''    for candidates in _by_stage(rules, lambda r: r.matches_invoice(invoice)):
        options = [(_round2(r.apply(running, 1)), r) for r in candidates]
        running, rule = _select(options)
        applied_invoice.append(rule.rule_id)
'''

ROW_LADDERS = '''def _row_to_rule(row):
    kind = row["kind"]
    if kind == "tiered":
        return TieredRule(row["rule_id"], row["sku"], parse_tiers(row["tiers"]))
    if kind == "bulk":
        return BulkRule(row["rule_id"], row["sku"], row["buy"], row["pay"])
    if kind == "percentage":
        return PercentageRule(row["rule_id"], Decimal(row["percent"]), row["sku"])
    if kind == "coupon":
        percent = Decimal(row["percent"]) if row["percent"] is not None else None
        amount = Decimal(row["amount"]) if row["amount"] is not None else None
        return CouponRule(row["rule_id"], row["code"], percent=percent, amount=amount)
    raise ValueError(f"unknown rule kind {kind!r}")


def _rule_to_row(rule):
    if isinstance(rule, TieredRule):
        return (rule.rule_id, "tiered", rule.sku, None, None, None, format_tiers(rule.tiers), None, None)
    if isinstance(rule, BulkRule):
        return (rule.rule_id, "bulk", rule.sku, None, rule.buy, rule.pay, None, None, None)
    if isinstance(rule, PercentageRule):
        return (rule.rule_id, "percentage", rule.sku, str(rule.percent), None, None, None, None, None)
    if isinstance(rule, CouponRule):
        percent = str(rule.percent) if rule.percent is not None else None
        amount = str(rule.amount) if rule.amount is not None else None
        return (rule.rule_id, "coupon", None, percent, None, None, None, rule.code, amount)
    raise TypeError(f"unknown rule type {type(rule)!r}")
'''

ROW_TABLES = '''def _coupon_from_row(row):
    percent = Decimal(row["percent"]) if row["percent"] is not None else None
    amount = Decimal(row["amount"]) if row["amount"] is not None else None
    return CouponRule(row["rule_id"], row["code"], percent=percent, amount=amount)


def _coupon_to_row(rule):
    percent = str(rule.percent) if rule.percent is not None else None
    amount = str(rule.amount) if rule.amount is not None else None
    return (rule.rule_id, "coupon", None, percent, None, None, None, rule.code, amount)


# One entry per rule kind, keyed by the kind the rule itself declares. A new
# kind is an entry here; no function below is reopened to add one.
_FROM_ROW = {
    "tiered": lambda row: TieredRule(row["rule_id"], row["sku"], parse_tiers(row["tiers"])),
    "bulk": lambda row: BulkRule(row["rule_id"], row["sku"], row["buy"], row["pay"]),
    "percentage": lambda row: PercentageRule(row["rule_id"], Decimal(row["percent"]), row["sku"]),
    "coupon": _coupon_from_row,
}

_TO_ROW = {
    "tiered": lambda r: (r.rule_id, "tiered", r.sku, None, None, None, format_tiers(r.tiers), None, None),
    "bulk": lambda r: (r.rule_id, "bulk", r.sku, None, r.buy, r.pay, None, None, None),
    "percentage": lambda r: (r.rule_id, "percentage", r.sku, str(r.percent), None, None, None, None, None),
    "coupon": _coupon_to_row,
}


def _row_to_rule(row):
    try:
        build = _FROM_ROW[row["kind"]]
    except KeyError:
        raise ValidationError(f"no row mapping for rule kind {row['kind']!r}") from None
    return build(row)


def _rule_to_row(rule):
    try:
        build = _TO_ROW[rule.kind]
    except KeyError:
        raise ValidationError(f"no row mapping for rule kind {rule.kind!r}") from None
    return build(rule)
'''

KIND_LADDER = """      {% if rule.__class__.__name__ == 'PercentageRule' %}
      <td>percentage</td>
      <td>{{ rule.sku or 'invoice' }}</td>
      <td>{{ rule.percent }}%</td>
      {% elif rule.__class__.__name__ == 'BulkRule' %}
      <td>bulk</td>
      <td>{{ rule.sku }}</td>
      <td>buy {{ rule.buy }}, pay {{ rule.pay }}</td>
      {% elif rule.__class__.__name__ == 'TieredRule' %}
      <td>tiered</td>
      <td>{{ rule.sku }}</td>
      <td>{% for q, p in rule.tiers %}{{ q }}:{{ p }}{% if not loop.last %}, {% endif %}{% endfor %}</td>
      {% elif rule.__class__.__name__ == 'CouponRule' %}
      <td>coupon</td>
      <td>invoice</td>
      <td>code {{ rule.code }}, {% if rule.percent is not none %}{{ rule.percent }}%{% else %}{{ rule.amount }}{% endif %}</td>
      {% endif %}
"""

KIND_CELLS = """      <td>{{ rule.kind }}</td>
      <td>{{ rule.scope_label }}</td>
      <td>{{ rule.detail() }}</td>
"""

TERMS_ANCHOR = '''        """The rule\'s terms, for display."""
        return ""'''

TERMS_NEW = TERMS_ANCHOR + '''

    def terms(self) -> dict:
        """The rule\'s own fields as plain values, for a store to map.

        A store maps these names onto its own columns: the rule names no
        column, and the store names no kind.
        """
        return {field.name: getattr(self, field.name)
                for field in dataclasses.fields(self)}

    @classmethod
    def from_terms(cls, terms):
        """The rule these terms describe, less any it does not carry."""
        return cls(**{field.name: terms[field.name]
                      for field in dataclasses.fields(cls)
                      if terms.get(field.name) is not None})'''

ROW_TERMS = '''# The columns a rule is stored in, and the codec for each column that is
# not stored as it is held. Both are keyed by column: a new rule kind
# reusing a column reuses its codec, and nothing below names a kind.
_COLUMNS = ("rule_id", "kind", "sku", "percent", "buy", "pay", "tiers",
            "code", "amount")

_CODECS = {
    "tiers": (format_tiers, parse_tiers),
    "percent": (str, Decimal),
    "amount": (str, Decimal),
}


def _encode(column, value):
    if value is None:
        return None
    write_value, _ = _CODECS.get(column, (lambda v: v, None))
    return write_value(value)


def _decode(column, value):
    if value is None:
        return None
    _, read_value = _CODECS.get(column, (None, lambda v: v))
    return read_value(value)


def _row_to_rule(row):
    terms = {column: _decode(column, row[column]) for column in _COLUMNS
             if column != "kind"}
    return rule_class(row["kind"]).from_terms(terms)


def _rule_to_row(rule):
    terms = dict(rule.terms(), kind=rule.kind)
    return tuple(_encode(column, terms.get(column)) for column in _COLUMNS)
'''


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
