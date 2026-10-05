# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`expense-splitter` is a small Python CLI (in a practice repo). It reads a CSV of expenses (`payer,amount,description`) and prints how much each person owes so everyone pays an equal share. `docs/hello.txt` is intentionally left as is; don't modify it.

## Commands

Run from the repo root unless noted.

- Install: `pip install -r requirements.txt` (only pytest)
- Test all: `python -m pytest`
- Single test: `python -m pytest tests/test_expense_splitter.py::test_balances`
- Run the CLI: `cd src && python -m expense_splitter ../docs/sample_expenses.csv`

There is no build step, linter, or packaging config (no `pyproject.toml`). `pytest.ini` sets `pythonpath = src`, so tests import `expense_splitter` directly. Running the CLI requires `src/` as the working directory (or on `PYTHONPATH`).

## Architecture

Package `src/expense_splitter/` is a three-stage pipeline wired together by `cli.py`:

1. `parser.py`: CSV lines to `Expense` dataclasses. Validates input and raises `ExpenseError` (a `ValueError`) with line numbers.
2. `calculator.py`: `compute_balances(expenses)` returns `{person: owed}`. Positive means owes, negative means is owed.
3. `cli.py`: formats the report and maps `OSError`/`ExpenseError` to `error: ...` on stderr with exit code 1.

Behaviors that aren't obvious from a single file:
- Amounts are `Decimal` throughout (never float); balances are quantized to cents with banker's rounding, so balances may not sum to exactly zero.
- The split is among people who appear as a payer only. Someone who paid nothing must have a row with amount `0` to be included.
- Header names are case-insensitive and whitespace-trimmed; the CSV is read with `utf-8-sig`, so a BOM is tolerated.
