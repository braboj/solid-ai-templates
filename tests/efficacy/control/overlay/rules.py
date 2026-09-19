"""Discount rules.

Every kind honours the Rule contract and registers itself, so adding a kind is
adding a class here and nothing else: the pricing algorithm, the web form and
the template all read the registry rather than naming the kinds they know.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from .errors import ValidationError

REGISTRY: dict = {}


def register(cls):
    """Add a rule kind to the registry under its own `kind`."""
    if not cls.kind:
        raise ValidationError(f"{cls.__name__} declares no kind")
    if cls.kind in REGISTRY:
        raise ValidationError(f"duplicate rule kind {cls.kind!r}")
    REGISTRY[cls.kind] = cls
    return cls


def kinds() -> tuple:
    """Every registered rule kind."""
    return tuple(REGISTRY)


def rule_class(kind: str):
    """The class registered for `kind`."""
    try:
        return REGISTRY[kind]
    except KeyError:
        raise ValidationError(f"unknown rule kind {kind!r}") from None


class Rule(ABC):
    """What every discount rule promises the pricing algorithm.

    `stage` orders application: the rules of one stage compete for a single
    slot, the cheapest wins, and the next stage sees the amount it produced.
    """

    kind: str = ""
    stage: int = 0

    def matches_line(self, product) -> bool:
        """Whether this rule competes for a line of `product`."""
        return False

    def matches_invoice(self, invoice) -> bool:
        """Whether this rule competes for the invoice as a whole."""
        return False

    @abstractmethod
    def apply(self, amount: Decimal, quantity: int) -> Decimal:
        """The amount after this rule, given the amount before it."""

    @property
    def scope_label(self) -> str:
        """How the rule's scope is shown to a reader."""
        return "invoice"

    def detail(self) -> str:
        """The rule's terms, for display."""
        return ""


@register
@dataclass
class PercentageRule(Rule):
    kind = "percentage"
    stage = 2

    rule_id: str
    percent: Decimal
    sku: str | None = None

    def __post_init__(self) -> None:
        if not self.percent > 0 or self.percent > 100:
            raise ValidationError("percent must be greater than zero and at most 100")

    def matches_line(self, product) -> bool:
        return self.sku is not None and self.sku == product.sku

    def matches_invoice(self, invoice) -> bool:
        return self.sku is None

    def apply(self, amount: Decimal, quantity: int) -> Decimal:
        return amount * (Decimal(1) - self.percent / Decimal(100))

    @property
    def scope_label(self) -> str:
        return self.sku or "invoice"

    def detail(self) -> str:
        return f"{self.percent}%"


@register
@dataclass
class BulkRule(Rule):
    kind = "bulk"
    stage = 1

    rule_id: str
    sku: str
    buy: int
    pay: int

    def __post_init__(self) -> None:
        if self.pay < 1 or not self.buy > self.pay:
            raise ValidationError("buy must be greater than pay, and pay must be at least one")

    def matches_line(self, product) -> bool:
        return self.sku == product.sku

    def apply(self, amount: Decimal, quantity: int) -> Decimal:
        groups, remainder = divmod(quantity, self.buy)
        chargeable_units = groups * self.pay + remainder
        return amount / quantity * chargeable_units

    @property
    def scope_label(self) -> str:
        return self.sku

    def detail(self) -> str:
        return f"buy {self.buy}, pay {self.pay}"


@register
@dataclass
class TieredRule(Rule):
    kind = "tiered"
    stage = 0

    rule_id: str
    sku: str
    tiers: tuple

    def __post_init__(self) -> None:
        tiers = tuple((int(min_quantity), Decimal(unit_price)) for min_quantity, unit_price in self.tiers)
        if not tiers:
            raise ValidationError("tiers must not be empty")
        previous = None
        for min_quantity, unit_price in tiers:
            if min_quantity < 1:
                raise ValidationError("tier min_quantity must be at least one")
            if unit_price < 0:
                raise ValidationError("tier unit_price must not be negative")
            if previous is not None and min_quantity <= previous:
                raise ValidationError("tiers must be strictly increasing by min_quantity")
            previous = min_quantity
        self.tiers = tiers

    def matches_line(self, product) -> bool:
        return self.sku == product.sku

    def apply(self, amount: Decimal, quantity: int) -> Decimal:
        applicable_price = None
        for min_quantity, unit_price in self.tiers:
            if quantity >= min_quantity:
                applicable_price = unit_price
        if applicable_price is None:
            return amount
        return applicable_price * quantity

    @property
    def scope_label(self) -> str:
        return self.sku

    def detail(self) -> str:
        return ", ".join(f"{q}:{p}" for q, p in self.tiers)


@register
@dataclass
class CouponRule(Rule):
    kind = "coupon"
    stage = 3

    rule_id: str
    code: str
    percent: Decimal | None = None
    amount: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValidationError("code must be non-empty")
        if (self.percent is None) == (self.amount is None):
            raise ValidationError("coupon must carry exactly one of percent or amount")
        if self.amount is not None and not self.amount > 0:
            raise ValidationError("amount must be greater than zero")

    def matches_invoice(self, invoice) -> bool:
        carried = {code.strip() for code in invoice.coupon_codes}
        return self.code.strip() in carried

    def apply(self, amount: Decimal, quantity: int) -> Decimal:
        if self.percent is not None:
            return amount * (Decimal(1) - self.percent / Decimal(100))
        return amount - min(self.amount, amount)

    def detail(self) -> str:
        terms = f"{self.percent}%" if self.percent is not None else f"{self.amount}"
        return f"code {self.code}, {terms}"
