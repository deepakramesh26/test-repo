from decimal import Decimal

import pytest

from expense_splitter.calculator import compute_balances
from expense_splitter.cli import main
from expense_splitter.parser import ExpenseError, parse_expenses

CSV = ["payer,amount,description", "Alice,30,Dinner", "Bob,10.50,Taxi", "Carol,0,Nothing"]


def test_parse_expenses():
    expenses = parse_expenses(CSV)
    assert [e.payer for e in expenses] == ["Alice", "Bob", "Carol"]
    assert expenses[1].amount == Decimal("10.50")
    assert expenses[0].description == "Dinner"


@pytest.mark.parametrize("bad", [
    ["payer,amount", "A,1"],
    ["payer,amount,description", "A,abc,x"],
    ["payer,amount,description", "A,-5,x"],
    ["payer,amount,description", ",5,x"],
])
def test_parse_errors(bad):
    with pytest.raises(ExpenseError):
        parse_expenses(bad)


def test_balances():
    balances = compute_balances(parse_expenses(CSV))
    # total 40.50 / 3 = 13.50 each
    assert balances == {
        "Alice": Decimal("-16.50"),
        "Bob": Decimal("3.00"),
        "Carol": Decimal("13.50"),
    }


def test_balances_empty():
    assert compute_balances([]) == {}


def test_multiple_expenses_same_payer():
    balances = compute_balances(parse_expenses(
        ["payer,amount,description", "A,10,x", "A,10,y", "B,0,z"]
    ))
    assert balances == {"A": Decimal("-10.00"), "B": Decimal("10.00")}


def test_cli_output(tmp_path, capsys):
    f = tmp_path / "e.csv"
    f.write_text("\n".join(CSV))
    assert main([str(f)]) == 0
    out = capsys.readouterr().out
    assert "Alice  is owed 16.50" in out
    assert "Carol  owes 13.50" in out


def test_cli_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "nope.csv")]) == 1
    assert "error:" in capsys.readouterr().err
