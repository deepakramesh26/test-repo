"""Compute each person's balance after splitting shared expenses."""
from decimal import ROUND_HALF_EVEN, Decimal

from .errors import ExpenseError

CENT = Decimal("0.01")


def _clean(name):
    return " ".join(name.split())


def name_key(name):
    """Identity of a person: case-insensitive, whitespace-collapsed."""
    return _clean(name).casefold()


def compute_balances(expenses):
    """Return {person: amount owed}, sorted by name.

    Positive means the person owes money; negative means they are owed.
    An expense is split among its participants; if it lists none, among
    everyone who paid in any row. Participants must be payers (the parser
    enforces this), and display names come from the first payer spelling.
    """
    people = {}  # key -> display name (first payer spelling seen)
    for e in expenses:
        people.setdefault(name_key(e.payer), _clean(e.payer))
    if not people:
        return {}

    paid = {key: Decimal(0) for key in people}
    owed = {key: Decimal(0) for key in people}
    for e in expenses:
        paid[name_key(e.payer)] += e.amount
        group = {name_key(p) for p in e.participants} or set(people)
        share = e.amount / len(group)
        for key in group:
            if key not in owed:
                raise ExpenseError(f"participant {key!r} is not a payer in any row")
            owed[key] += share

    return {
        people[key]: (owed[key] - paid[key]).quantize(CENT, rounding=ROUND_HALF_EVEN)
        for key in sorted(people)
    }
