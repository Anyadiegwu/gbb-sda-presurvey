"""
Safe formula evaluation for BOQ item pricing.

Every formula-mode item gets `rate` (the item's admin-set rate) and
`quantity` (the customer-driven quantity for that item -- distance_m for
fibre, bandwidth_mbps for bandwidth, or 1 for flat-style items) as
variables. Known item keys additionally expose a friendlier named alias
for `quantity` so formulas read naturally.

We NEVER use eval()/exec() for this -- simpleeval only allows arithmetic
on a whitelisted set of named variables, so a malicious or broken formula
can't execute arbitrary code or touch the filesystem/network.
"""

from typing import Dict, Set

from simpleeval import SimpleEval, InvalidExpression

# Every formula, regardless of item, always has these two.
BASE_VARIABLES = {"rate", "quantity"}

# Extra named aliases available per item key, purely for formula readability.
# The value(s) are computed from `quantity` when building the variable dict.
ITEM_EXTRA_VARIABLES: Dict[str, Set[str]] = {
    "fibre": {"distance_m", "distance_km"},
    "bandwidth": {"bandwidth_mbps"},
}

DEFAULT_EXPRESSION = "quantity * rate"


class FormulaError(Exception):
    pass


def get_allowed_variables(item_key: str) -> Set[str]:
    return BASE_VARIABLES | ITEM_EXTRA_VARIABLES.get(item_key, set())


def build_variables(item_key: str, rate: float, quantity: float) -> Dict[str, float]:
    """Builds the full variable dict for a given item's formula evaluation."""
    variables = {"rate": rate, "quantity": quantity}
    if item_key == "fibre":
        variables["distance_m"] = quantity
        variables["distance_km"] = quantity / 1000
    elif item_key == "bandwidth":
        variables["bandwidth_mbps"] = quantity
    return variables


def validate_expression(item_key: str, expression: str) -> None:
    """Raises FormulaError if the expression uses a disallowed name or
    doesn't parse. Call this before saving any admin-submitted formula."""
    allowed = get_allowed_variables(item_key)
    dummy_values = {name: 1.0 for name in allowed}
    evaluator = SimpleEval(names=dummy_values)
    try:
        evaluator.eval(expression)
    except InvalidExpression as exc:
        raise FormulaError(f"Invalid formula: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surface any parse/name error to the admin
        raise FormulaError(f"Invalid formula: {exc}") from exc


def evaluate(item_key: str, expression: str, rate: float, quantity: float) -> float:
    """Evaluate an already-validated expression with real values."""
    variables = build_variables(item_key, rate, quantity)
    evaluator = SimpleEval(names=variables)
    try:
        result = evaluator.eval(expression)
    except Exception as exc:  # noqa: BLE001
        raise FormulaError(f"Could not evaluate formula for '{item_key}': {exc}") from exc

    return float(result)
