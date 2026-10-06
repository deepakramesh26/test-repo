"""Command-line entry point."""
import argparse
import sys

from .calculator import compute_balances
from .parser import ExpenseError, load_expenses


def format_report(balances):
    if not balances:
        return "No expenses found."
    width = max(len(name) for name in balances)
    lines = []
    for name, owed in balances.items():
        if owed > 0:
            text = f"owes {owed:.2f}"
        elif owed < 0:
            text = f"is owed {-owed:.2f}"
        else:
            text = "is settled"
        lines.append(f"{name:<{width}}  {text}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="expense-splitter",
        description="Show how much each person owes after splitting shared expenses.",
    )
    parser.add_argument(
        "csv_file",
        help="CSV with columns: payer, amount, description "
        "[, participants (semicolon-separated payers; blank = all payers)]",
    )
    args = parser.parse_args(argv)
    try:
        expenses = load_expenses(args.csv_file)
    except (OSError, ExpenseError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(format_report(compute_balances(expenses)))
    return 0
