"""Show one search: python -m connect_four.demo [columns played ...]

With no arguments it uses the must-block position 0 6 1 6 2, where O must
play column 3 to stop X's three in a row.
"""

import sys

from .game import from_moves
from .mcts import MCTSConfig, MCTSPlayer


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    moves = [int(a) for a in argv] if argv else [0, 6, 1, 6, 2]
    s = from_moves(moves)
    print(s)
    print()
    p = MCTSPlayer(MCTSConfig(cycles=1000, seed=0))
    m = p(s)
    print("Chosen column:", m)
    print("Root moves (column: playouts, win rate, objective score):")
    for c, (n, u, h) in sorted(p.last_stats["children"].items()):
        print(f"  {c}: N={n:4}  U/N={u}  H={h}")
    print("Tree size:", p.last_stats["tree_size"], " tree height:", p.last_stats["tree_height"])


if __name__ == "__main__":
    main()
