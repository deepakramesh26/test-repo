"""Compute each person's balance for an equal split."""
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


def compute_balances(expenses):
    """Return {person: amount owed}, sorted by name.

    Positive means the person owes money; negative means they are owed.
    Everyone who appears as a payer shares the total equally.
    """
    paid = {}
    for e in expenses:
        paid[e.payer] = paid.get(e.payer, Decimal(0)) + e.amount
    if not paid:
        return {}
    share = sum(paid.values()) / len(paid)
    return {
        person: (share - paid[person]).quantize(CENT, rounding=ROUND_HALF_EVEN)
        for person in sorted(paid)
    }
