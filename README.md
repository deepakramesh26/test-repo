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
prints how much each person owes so everyone pays an equal share. Everyone who
appears as a payer is included in the split.

An optional fourth column, `participants`, lists the people (separated by `;`,
e.g. `alice;bob`) an expense is split between. If it is blank, the expense is
split among everyone who appears in the file. Names are matched
case-insensitively and ignoring extra spaces. See
`docs/sample_expenses_participants.csv`.

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
