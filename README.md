# DPS970 Activity 2

**Student:** Ashutosh Verma
**Textbook:** Russell and Norvig, *Artificial Intelligence: A Modern Approach*, 4th edition (AIMA)

Written answers and the Question 1 report are in [ANSWERS.md](ANSWERS.md).

## Contents

| Path | What it is |
|---|---|
| `connect_four/game.py` | Connect Four (6 x 7) as a game in the form of AIMA Section 5.1 |
| `connect_four/mcts.py` | MCTS move generator following AIMA Figure 5.11 |
| `connect_four/experiments.py` | The experiments for Question 1 (writes to `results/`) |
| `connect_four/demo.py` | Prints one search: the board, the chosen move and the statistics per move |
| `screenshots/` | Captures of the tests, a quick experiment run and the demo |
| `logic/propositional.py` | TT-ENTAILS (Fig. 7.10), CNF conversion (Sec. 7.5.2), PL-RESOLUTION (Fig. 7.12) |
| `tests/` | pytest tests; test data in `tests/data/` |
| `results/` | Data collected by the experiments (CSV, summary tables, charts) |
| `.github/workflows/tests.yml` | GitHub Actions: runs the tests and a quick experiment on every push |

## Requirements

Python 3.10 or newer.

```
pip install -r requirements.txt
```

## Running the tests

From this folder:

```
python -m pytest -v
```

There are 59 tests:

- `tests/test_connect_four.py`: game rules (wins in all four directions, full
  columns, draws, utility), and the MCTS generator (finds wins and forced
  blocks, `cycles` equals root playouts, the depth limit and expansion width
  are respected, same seed gives the same move, beats a random player, and a
  quick experiment run completes). Positions are in `tests/data/positions.json`.
- `tests/test_logic.py`: the answers to Questions 2, 3 and 4 checked three
  ways (truth table, TT-ENTAILS and resolution), model counts, and that each
  CNF conversion is equivalent to the original sentence and gives the
  expected clauses. Cases are in `tests/data/logic_cases.json`.

The same tests run automatically on GitHub through GitHub Actions
(`.github/workflows/tests.yml`) when the folder is pushed to a repository.

## Running the experiments

```
python -m connect_four.experiments            # full run used in the report (about 15 to 20 minutes on 2 cores)
python -m connect_four.experiments --quick    # small run, under 30 seconds, writes to results/quick/
```

Options: `--runs N` (searches per position, default 20), `--games N` (games per
match, default 10), `--workers N` (processes, default all cores).

## Demo of one search

```
python -m connect_four.demo              # the must-block position
python -m connect_four.demo 3 3 2 4      # any position, given as the columns played
```

## Screenshots

`screenshots/` has captures of the three commands above (tests, quick
experiment, demo). To take your own on Windows, open a terminal in this
folder, run the command and press Win + Shift + S; on macOS press
Cmd + Shift + 4.

## Using the move generator

```python
from connect_four.game import ConnectFour, from_moves
from connect_four.mcts import MCTSConfig, MCTSPlayer

player = MCTSPlayer(MCTSConfig(cycles=1000, expansion_width=7, max_depth=42,
                               c=1.414, w_objective=1.0, seed=None))
state = from_moves([3, 3, 2])     # columns played so far, starting with X
print(state)
print(player(state))              # the chosen column
print(player.last_stats)          # playouts and win rate per root move
```

## Using the logic code

```python
from logic.propositional import classify, count_models, to_cnf_steps, pl_resolution, parse, TRUE

classify("Smoke ==> Fire")                       # 'satisfiable'
count_models("B | C", "ABCD")                     # 12
for name, s in to_cnf_steps("(Food & Drinks) ==> Party"):
    print(name, s)
trace = []
pl_resolution(TRUE, parse("((Food ==> Party) | (Drinks ==> Party)) ==> ((Food & Drinks) ==> Party)"), trace)
```

Syntax: `~` not, `&` and, `|` or, `==>` implies, `<=>` if and only if.
