# test-repo

A small practice repository for experimenting with git and Claude Code.

## Layout

| Path | Purpose |
|---|---|
| `src/` | Source code |
| `tests/` | Tests |
| `docs/` | Notes and documentation |
| `docs/scratch/` | Scratch files |

## Getting started

`expense-splitter` reads a CSV of expenses (`payer,amount,description`) and
prints how much each person owes. By default every expense is split equally
among everyone who appears as a payer in the file.

An optional fourth column, `participants`, lists the people (separated by `;`,
e.g. `alice;bob`) an expense is split between. If it is blank, the expense is
split among all payers. Every participant must also be a payer in some row,
otherwise the file is rejected with a line-numbered error (this catches
typos). Names are matched case-insensitively and ignoring extra spaces, and the
report uses the payer's spelling. See `docs/sample_expenses_participants.csv`.

### Install

```
pip install -r requirements.txt
```

### Run

```
cd src
python -m expense_splitter ../docs/sample_expenses.csv
```

Example output:

```
Alice  is owed 30.00
Bob    owes 10.00
Carol  owes 20.00
```

### Test

From the repo root:

```
python -m pytest
```

**Note:** this is a practice repo.

- first item
- second item

[Git docs](https://git-scm.com/doc)
