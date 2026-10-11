"""Compute each person's balance after splitting shared expenses."""
from decimal import ROUND_HALF_EVEN, Decimal

from .errors import ExpenseError

CENT = Decimal("0.01")
# Precision used to rank rounding errors when handing out leftover cents.
# Far finer than a cent, far coarser than Decimal's 28-digit division noise.
TIE_EPS = Decimal("1e-12")


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

    keys = sorted(people)
    exact = {key: owed[key] - paid[key] for key in keys}
    balances = {key: exact[key].quantize(CENT, rounding=ROUND_HALF_EVEN) for key in keys}

    # Exact balances sum to zero; rounding may leave a few cents over or
    # under. Largest-remainder: give each cent to the person rounding hurt
    # most (ties broken by sorted name), so no one moves further than a cent.
    leftover = int(-sum(balances.values()) / CENT)
    if leftover:
        sign = 1 if leftover > 0 else -1
        # Errors are bucketed to TIE_EPS so last-digit division noise doesn't
        # decide between people whose true errors are equal; sorted() is
        # stable, so ties keep name order. This is a bucket, not a tolerance:
        # it can't separate errors closer than TIE_EPS, and in principle an
        # equal pair straddling a bucket edge could still split.
        by_error = sorted(
            keys, key=lambda k: -sign * (exact[k] - balances[k]).quantize(TIE_EPS)
        )
        for key in by_error[:abs(leftover)]:
            balances[key] += sign * CENT

    return {people[key]: balances[key] for key in keys}
