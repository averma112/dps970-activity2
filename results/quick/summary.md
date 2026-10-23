# Experiment results

Runs per position: 4. Games per match vs reference: 2 (vs random: 2). Reference player: plain UCT, 100 cycles. Match cycles: 100 (except the cycles experiment).

## Experiment 1: consistency and tactics

| config | position | most_common_move | agreement | distinct_moves | move_counts | accuracy | mean_tree_size | mean_seconds |
|---|---|---|---|---|---|---|---|---|
| baseline | empty | 3 | 0.5 | 3 | 1:1 3:2 5:1 |  | 1401 | 0.04 |
| baseline | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1140 | 0.029 |
| baseline | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 734 | 0.017 |
| baseline | midgame | 3 | 1.0 | 1 | 3:4 |  | 1390 | 0.035 |
| cycles=50 | empty | 6 | 0.25 | 4 | 1:1 3:1 4:1 6:1 |  | 351 | 0.005 |
| cycles=50 | must_block | 3 | 0.5 | 3 | 0:1 3:2 6:1 | 0.5 | 300 | 0.006 |
| cycles=50 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 256 | 0.008 |
| cycles=50 | midgame | 2 | 0.5 | 3 | 2:2 3:1 6:1 |  | 346 | 0.009 |
| cycles=1000 | empty | 3 | 0.5 | 3 | 1:1 3:2 5:1 |  | 1401 | 0.039 |
| cycles=1000 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1140 | 0.025 |
| cycles=1000 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 734 | 0.027 |
| cycles=1000 | midgame | 3 | 1.0 | 1 | 3:4 |  | 1390 | 0.038 |
| x=2 | empty | 3 | 1.0 | 1 | 3:4 |  | 364 | 0.036 |
| x=2 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 130 | 0.009 |
| x=2 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 53 | 0.003 |
| x=2 | midgame | 3 | 1.0 | 1 | 3:4 |  | 194 | 0.019 |
| x=7 | empty | 3 | 0.5 | 3 | 1:1 3:2 5:1 |  | 1401 | 0.038 |
| x=7 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1140 | 0.025 |
| x=7 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 734 | 0.015 |
| x=7 | midgame | 3 | 1.0 | 1 | 3:4 |  | 1390 | 0.028 |
| depth=1 | empty | 4 | 0.5 | 2 | 3:2 4:2 |  | 8 | 0.011 |
| depth=1 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 8 | 0.006 |
| depth=1 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 8 | 0.005 |
| depth=1 | midgame | 3 | 0.5 | 3 | 2:1 3:2 5:1 |  | 8 | 0.005 |
| depth=42 | empty | 3 | 0.5 | 3 | 1:1 3:2 5:1 |  | 1401 | 0.027 |
| depth=42 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1140 | 0.02 |
| depth=42 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 734 | 0.016 |
| depth=42 | midgame | 3 | 1.0 | 1 | 3:4 |  | 1390 | 0.025 |
| W=0 | empty | 3 | 0.5 | 3 | 2:1 3:2 4:1 |  | 1401 | 0.03 |
| W=0 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1154 | 0.022 |
| W=0 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 766 | 0.013 |
| W=0 | midgame | 3 | 1.0 | 1 | 3:4 |  | 1387 | 0.023 |
| W=5 | empty | 3 | 0.5 | 3 | 2:1 3:2 5:1 |  | 1401 | 0.018 |
| W=5 | must_block | 3 | 1.0 | 1 | 3:4 | 1.0 | 1147 | 0.019 |
| W=5 | win_now | 0 | 1.0 | 1 | 0:4 | 1.0 | 785 | 0.015 |
| W=5 | midgame | 3 | 1.0 | 1 | 3:4 |  | 1389 | 0.02 |

## Experiment 2: strength

| config | opponent | games | wins | draws | losses | score |
|---|---|---|---|---|---|---|
| baseline | reference | 2 | 1 | 0 | 1 | 0.5 |
| baseline | random | 2 | 2 | 0 | 0 | 1.0 |
| cycles=50 | reference | 2 | 1 | 0 | 1 | 0.5 |
| cycles=50 | random | 2 | 2 | 0 | 0 | 1.0 |
| cycles=1000 | reference | 2 | 1 | 1 | 0 | 0.75 |
| cycles=1000 | random | 2 | 2 | 0 | 0 | 1.0 |
| x=2 | reference | 2 | 2 | 0 | 0 | 1.0 |
| x=2 | random | 2 | 2 | 0 | 0 | 1.0 |
| x=7 | reference | 2 | 1 | 0 | 1 | 0.5 |
| x=7 | random | 2 | 2 | 0 | 0 | 1.0 |
| depth=1 | reference | 2 | 2 | 0 | 0 | 1.0 |
| depth=1 | random | 2 | 2 | 0 | 0 | 1.0 |
| depth=42 | reference | 2 | 1 | 0 | 1 | 0.5 |
| depth=42 | random | 2 | 2 | 0 | 0 | 1.0 |
| W=0 | reference | 2 | 1 | 0 | 1 | 0.5 |
| W=0 | random | 2 | 2 | 0 | 0 | 1.0 |
| W=5 | reference | 2 | 1 | 0 | 1 | 0.5 |
| W=5 | random | 2 | 2 | 0 | 0 | 1.0 |
