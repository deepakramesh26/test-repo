"""Read expenses from a CSV file."""
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

REQUIRED_COLUMNS = ("payer", "amount", "description")


class ExpenseError(ValueError):
    """Raised when the input CSV is malformed."""


@dataclass(frozen=True)
class Expense:
    payer: str
    amount: Decimal
    description: str


def parse_expenses(lines):
    """Parse an iterable of CSV lines (with a header row) into Expenses."""
    reader = csv.DictReader(lines)
    fields = [f.strip().lower() for f in reader.fieldnames or []]
    missing = [c for c in REQUIRED_COLUMNS if c not in fields]
    if missing:
        raise ExpenseError(f"missing column(s): {', '.join(missing)}")
    reader.fieldnames = fields

    expenses = []
    for row in reader:
        line = reader.line_num
        payer = (row["payer"] or "").strip()
        if not payer:
            raise ExpenseError(f"line {line}: payer is empty")
        try:
            amount = Decimal((row["amount"] or "").strip())
        except InvalidOperation:
            raise ExpenseError(f"line {line}: invalid amount {row['amount']!r}") from None
        if not amount.is_finite() or amount < 0:
            raise ExpenseError(f"line {line}: amount must be a non-negative number")
        expenses.append(Expense(payer, amount, (row["description"] or "").strip()))
    return expenses


def load_expenses(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return parse_expenses(f)
