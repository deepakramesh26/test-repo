from decimal import Decimal

import pytest

from expense_splitter.calculator import compute_balances
from expense_splitter.cli import main
from expense_splitter.parser import Expense, ExpenseError, _split_participants, parse_expenses

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


def _rows(*rows):
    return ["payer,amount,description,participants", *rows]


def _bal(*rows):
    return compute_balances(parse_expenses(_rows(*rows)))


def test_participants_parsed_and_trimmed():
    assert _split_participants("alice; bob ") == ("alice", "bob")


@pytest.mark.parametrize("cell,expected", [
    ("", ()), (" ", ()), (";;", ()), (None, ()), ("alice;", ("alice",)),
])
def test_participants_blank_variants(cell, expected):
    assert _split_participants(cell) == expected


def test_participants_column_optional_and_header_case():
    assert parse_expenses(CSV)[0].participants == ()
    [e, _] = parse_expenses(["Payer,Amount,Description,Participants", "A,1,x,b", "b,0,y,"])
    assert e.participants == ("b",)


def test_subset_split():
    assert _bal("A,30,x,A;B", "B,0,y,", "C,0,z,") == {
        "A": Decimal("-15.00"), "B": Decimal("15.00"), "C": Decimal("0.00"),
    }


def test_unknown_participant_raises_with_line_number():
    with pytest.raises(ExpenseError, match=r"line 3.*'Bbo'"):
        parse_expenses(_rows("Alice,10,x,", "Bob,5,y,Alice;Bbo"))


@pytest.mark.parametrize("cell", [";", "; ;", " ;; "])
def test_separator_only_participants_raises_with_line_number(cell):
    with pytest.raises(ExpenseError, match=r"line 3.*no names"):
        parse_expenses(_rows("Alice,10,x,", f"Bob,5,y,{cell}"))


def test_compute_balances_unknown_participant_raises_expense_error():
    expenses = [Expense("Alice", Decimal(10), "x", ("Zed",))]
    with pytest.raises(ExpenseError, match="zed"):
        compute_balances(expenses)


def test_unknown_participant_matches_case_and_whitespace_of_payer():
    assert _bal("Mary   Ann,10,x,  mary ann ") == {"Mary Ann": Decimal("-0.00")}


def test_cli_unknown_participant(tmp_path, capsys):
    f = tmp_path / "e.csv"
    f.write_text("payer,amount,description,participants\nAlice,10,x,\nBob,5,y,Bbo\n")
    assert main([str(f)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: line 3:") and "'Bbo'" in err


def test_blank_means_payers_only():
    # B and C are payers (even of $0), so a blank row splits three ways.
    assert _bal("A,30,x,", "B,0,y,", "C,0,z,") == {
        "A": Decimal("-20.00"), "B": Decimal("10.00"), "C": Decimal("10.00"),
    }


def test_blank_row_not_affected_by_other_rows_participants():
    # Naming people in a subset row doesn't add anyone to the blank split.
    assert _bal("A,40,x,", "B,30,y,A;B", "D,0,z,") == {
        "A": Decimal("-11.66"), "B": Decimal("-1.67"), "D": Decimal("13.33"),
    }
    assert set(_bal("A,40,x,", "B,30,y,A")) == {"A", "B"}


def test_display_name_comes_from_payer_rows():
    balances = _bal("Bob,10,x,ALICE;bob", "alice,0,y,", "Alice,0,z,")
    assert balances == {"Bob": Decimal("-5.00"), "alice": Decimal("5.00")}


def test_payer_not_in_participants():
    assert _bal("A,20,x,B;C", "B,0,y,", "C,0,z,") == {
        "A": Decimal("-20.00"), "B": Decimal("10.00"), "C": Decimal("10.00"),
    }


def test_uneven_division_rounds_to_cents():
    # The leftover cent goes to the first name in sorted order.
    assert _bal("A,10.00,x,A;B;C", "B,0,y,", "C,0,z,") == {
        "A": Decimal("-6.66"), "B": Decimal("3.33"), "C": Decimal("3.33"),
    }


@pytest.mark.parametrize("rows", [
    ("A,10.00,x,A;B;C", "B,0,y,", "C,0,z,"),
    ("A,10.00,x,", "B,0,y,", "C,0,z,"),
    ("A,0.01,x,", "B,0,y,", "C,0,z,"),
    ("A,100,x,", "B,0,y,", "C,0,z,", "D,0,w,", "E,0,v,", "F,0,u,", "G,0,t,"),
    ("A,40,x,", "B,30,y,A;B", "D,0,z,"),
    ("A,1.00,x,", "B,2.00,y,", "C,0.01,z,", "D,0.01,w,"),
])
def test_balances_sum_to_zero(rows):
    assert sum(_bal(*rows).values()) == Decimal("0.00")


def test_negative_leftover_removes_cent():
    # 0.20 over 3: shares round up to 0.07, so the rounded sum is +0.01 and a
    # cent must be taken away from someone.
    # All three rounding errors are equal, so the tie goes to A (sorted order).
    assert _bal("A,0.20,x,A;B;C", "B,0,y,", "C,0,z,") == {
        "A": Decimal("-0.14"), "B": Decimal("0.07"), "C": Decimal("0.07"),
    }


def test_tie_reached_by_different_arithmetic_paths():
    # A, B and C all have a true balance of -0.1333../0.0667../0.0667.. with
    # equal rounding errors, but B's is computed as (0.0667.. + 0.01) - 0.01
    # and C's from two shares, so unquantized Decimals differ in the last digits.
    assert _bal("A,0.20,x,A;B;C", "B,0.01,x,B", "C,0,x,C;B") == {
        "A": Decimal("-0.14"), "B": Decimal("0.07"), "C": Decimal("0.07"),
    }


def test_negative_leftover_tie_goes_to_first_name_not_payer():
    # 0.05 over 3: shares round up to 0.02; tie among all three, payer Z isn't
    # in the split and must be untouched.
    assert _bal("Z,0.05,x,A;B;C", "A,0,y,", "B,0,z,", "C,0,w,") == {
        "A": Decimal("0.01"), "B": Decimal("0.02"), "C": Decimal("0.02"),
        "Z": Decimal("-0.05"),
    }


def test_positive_leftover_tie_goes_to_first_name_not_payer():
    # Payer Z sorts last and has no rounding error; A wins the tie.
    assert _bal("Z,10.00,x,A;B;C", "A,0,y,", "B,0,z,", "C,0,w,") == {
        "A": Decimal("3.34"), "B": Decimal("3.33"), "C": Decimal("3.33"),
        "Z": Decimal("-10.00"),
    }


def test_positive_leftover_goes_to_largest_rounding_error():
    # Exact balances: A .0516.., B -.1183.., C .045, D .0216.. Rounded: .05,
    # -.12, .04 (half-even), .02, summing to -0.01. C was rounded down by a
    # full half cent (the others by ~0.0017), so C gets the cent, not A.
    bal = _bal("A,0.02,x,C;D;B;A", "B,0.20,x,D;C;A;B", "C,0.02,x,C;B", "D,0.05,x,D;B;A")
    assert bal == {
        "A": Decimal("0.05"), "B": Decimal("-0.12"),
        "C": Decimal("0.05"), "D": Decimal("0.02"),
    }


def test_negative_leftover_goes_to_largest_rounding_error():
    # Exact: A 0.00, B -.125, C .07, D .055. Half-even rounds B to -.12 and D
    # to .06 (each moved up half a cent), so the rounded sum is +0.01. B and D
    # tie for the largest upward error; B wins by name. A and C are untouched.
    bal = _bal("A,0.01,x,C;A", "B,0.20,x,B;D;C", "C,0.01,x,C;B;D", "D,0.02,x,D;C;A;B")
    assert bal == {
        "A": Decimal("0.00"), "B": Decimal("-0.13"),
        "C": Decimal("0.07"), "D": Decimal("0.06"),
    }


def test_uninvolved_person_stays_at_zero():
    # Aaron sorts first but isn't in the split; he must not absorb the cent.
    bal = _bal("Dan,10.00,x,Dan;Eve;Fay", "Eve,0,y,", "Fay,0,z,", "Aaron,0,w,")
    assert bal["Aaron"] == Decimal("0.00")
    assert bal == {
        "Aaron": Decimal("0.00"), "Dan": Decimal("-6.66"),
        "Eve": Decimal("3.33"), "Fay": Decimal("3.33"),
    }


def test_single_person_balance_is_zero():
    assert _bal("Solo,10,x,") == {"Solo": Decimal("0.00")}


def test_leftover_cents_assigned_in_sorted_order():
    # 1.00 over 7 people: each rounds to 0.14, leaving 2 cents over-credited.
    # Every rounding error is equal, so ties go to the first two names (A and B).
    bal = _bal("A,1.00,x,", *(f"{n},0,y," for n in "BCDEFG"))
    assert bal["A"] == Decimal("-0.85")
    assert bal["B"] == Decimal("0.15")
    assert all(bal[n] == Decimal("0.14") for n in "CDEFG")
    assert sum(bal.values()) == Decimal("0.00")


def test_bankers_rounding_tie():
    assert _bal("A,0.05,x,A;B", "B,0,y,") == {"A": Decimal("-0.02"), "B": Decimal("0.02")}


def test_whitespace_and_case_in_names():
    balances = _bal("Alice,20,x, bob ;  ALICE", "Mary   Ann,0,y,mary ann", "Bob,0,z,")
    assert balances == {
        "Alice": Decimal("-10.00"), "Bob": Decimal("10.00"), "Mary Ann": Decimal("0.00"),
    }


def test_payer_case_variants_merge():
    assert _bal("Alice,10,x,", "alice,10,y,", "Bob,0,z,") == {
        "Alice": Decimal("-10.00"), "Bob": Decimal("10.00"),
    }


def test_duplicate_participant_counted_once():
    assert _bal("A,10,x,bob;Bob", "bob,0,y,") == {"A": Decimal("-10.00"), "bob": Decimal("10.00")}


def test_cli_participants_output(tmp_path, capsys):
    f = tmp_path / "e.csv"
    f.write_text("payer,amount,description,participants\nbob,20,x,alice;Bob\nAlice,0,y,\n")
    assert main([str(f)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["Alice  owes 10.00", "bob    is owed 10.00"]
