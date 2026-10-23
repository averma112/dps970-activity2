"""Monte Carlo tree search move generator, following AIMA Figure 5.11.

    function MONTE-CARLO-TREE-SEARCH(state) returns an action
        tree <- NODE(state)
        while IS-TIME-REMAINING() do
            leaf   <- SELECT(tree)
            child  <- EXPAND(leaf)
            result <- SIMULATE(child)
            BACK-PROPAGATE(result, child)
        return the move in ACTIONS(state) whose node has highest number of playouts

Changes asked for by the activity (all configurable through `MCTSConfig`):

* IS-TIME-REMAINING() is replaced by a fixed number of `cycles`.
* SELECT uses a utility with a playout part (stored win rate plus the UCB1
  exploration term from Section 5.4) and an objective part (the rule based
  evaluation `ConnectFour.evaluate`):

      UTILITY(n) = U(n)/N(n) + C * sqrt(ln N(PARENT(n)) / N(n))
                   + W * H(n) / (N(n) + 1)

  H(n) is the objective score of n, squashed into [0, 1]. Dividing by
  N(n) + 1 makes the objective part matter most while a node has few
  playouts and fade out as real playout results build up ("progressive
  bias"). W = 0 gives plain UCT with UCB1.
* EXPAND creates `expansion_width` (x) children at once, chosen either by the
  objective score or at random. Only those x moves are ever searched below
  that node, so x is the width of the tree at each level.
* The tree stops growing at `max_depth`. A leaf at that depth is not expanded;
  SIMULATE runs a random playout from it.
* SIMULATE uses a uniform random playout policy.
"""

import math
import random
import time
from dataclasses import dataclass, field

from .game import DRAW, ConnectFour, other


@dataclass
class MCTSConfig:
    cycles: int = 1000            # iterations of the main loop
    expansion_width: int = 7      # x: children created when a node is expanded
    max_depth: int = 42           # tree height (42 = no limit for Connect Four)
    c: float = math.sqrt(2)       # UCB1 exploration constant C
    w_objective: float = 1.0      # W: weight of the objective (rule) part
    expansion_order: str = "objective"  # "objective" or "random"
    objective_scale: float = 20.0  # used to squash evaluate() into [0, 1]
    seed: int = None


class Node:
    """A search tree node: the state, its statistics and its children."""

    __slots__ = ("state", "parent", "move", "children", "N", "U", "H", "depth")

    def __init__(self, state, parent=None, move=None, H=0.5):
        self.state = state
        self.parent = parent
        self.move = move          # the action that led here from the parent
        self.children = []
        self.N = 0                # number of playouts through this node
        self.U = 0.0              # wins for the player who moved INTO this node
        self.H = H                # objective score in [0, 1] for that player
        self.depth = 0 if parent is None else parent.depth + 1


class MCTSPlayer:
    def __init__(self, config=None, game=None):
        self.config = config or MCTSConfig()
        self.game = game or ConnectFour()
        self.rng = random.Random(self.config.seed)
        self.last_stats = None

    # ------------------------------------------------------------------ main loop
    def monte_carlo_tree_search(self, state):
        start = time.perf_counter()
        tree = Node(state)
        for _ in range(self.config.cycles):         # IS-TIME-REMAINING()
            leaf = self.select(tree)                 # SELECT(tree)
            child = self.expand(leaf)                # EXPAND(leaf)
            result = self.simulate(child)            # SIMULATE(child)
            self.back_propagate(result, child)       # BACK-PROPAGATE(result, child)
        best = max(tree.children, key=lambda n: n.N)  # highest number of playouts
        self.last_stats = self._stats(tree, best, time.perf_counter() - start)
        return best.move

    __call__ = monte_carlo_tree_search

    # ------------------------------------------------------------------ SELECT
    def utility(self, n):
        """Selection utility: playout part + objective part."""
        cfg = self.config
        if n.N == 0:
            # An unvisited child is tried first; the objective breaks ties.
            return math.inf if cfg.w_objective == 0 else 1e9 + n.H
        exploit = n.U / n.N
        explore = cfg.c * math.sqrt(math.log(n.parent.N) / n.N)
        objective = cfg.w_objective * n.H / (n.N + 1)
        return exploit + explore + objective

    def select(self, node):
        """Follow the child with the highest utility until reaching a leaf."""
        while node.children:
            best_value = max(self.utility(ch) for ch in node.children)
            ties = [ch for ch in node.children if self.utility(ch) == best_value]
            node = ties[0] if len(ties) == 1 else self.rng.choice(ties)
        return node

    # ------------------------------------------------------------------ EXPAND
    def objective(self, state, player):
        """Squash the rule based evaluation into [0, 1] for `player`."""
        if state.winner == player:
            return 1.0
        if state.winner == DRAW:
            return 0.5
        if state.winner is not None:
            return 0.0
        score = self.game.evaluate(state, player)
        return 0.5 + 0.5 * math.tanh(score / self.config.objective_scale)

    def expand(self, leaf):
        """Create x children of the leaf and return one of them to simulate from.

        A terminal leaf, or a leaf at the maximum tree height, is returned
        unchanged so the playout starts from it.
        """
        cfg = self.config
        if self.game.is_terminal(leaf.state) or leaf.depth >= cfg.max_depth:
            return leaf
        mover = self.game.to_move(leaf.state)
        candidates = []
        for a in self.game.actions(leaf.state):
            s = self.game.result(leaf.state, a)
            candidates.append((self.objective(s, mover), a, s))
        if cfg.expansion_order == "random":
            self.rng.shuffle(candidates)
        else:
            self.rng.shuffle(candidates)  # random tie break between equal scores
            candidates.sort(key=lambda t: t[0], reverse=True)
        for h, a, s in candidates[: max(1, cfg.expansion_width)]:
            leaf.children.append(Node(s, leaf, a, h))
        return self.rng.choice(leaf.children)

    # ------------------------------------------------------------------ SIMULATE
    def simulate(self, node):
        """Random playout policy: play uniformly random legal moves to the end."""
        s = node.state.copy()
        rng = self.rng
        while s.winner is None:
            s.play(rng.choice(s.legal_columns()))
        return s.winner  # P1, P2 or DRAW

    # ------------------------------------------------------------------ BACK-PROPAGATE
    @staticmethod
    def back_propagate(result, node):
        """Update N and U on the path to the root.

        U(n) counts wins for the player who made the move into n, so that a
        parent picking the child with the best U/N picks the best move for
        itself. A draw counts as half a win.
        """
        while node is not None:
            node.N += 1
            mover = other(node.state.to_move)
            if result == mover:
                node.U += 1.0
            elif result == DRAW:
                node.U += 0.5
            node = node.parent

    # ------------------------------------------------------------------ reporting
    @staticmethod
    def _stats(tree, best, seconds):
        size, height = 0, 0
        stack = [tree]
        while stack:
            n = stack.pop()
            size += 1
            height = max(height, n.depth)
            stack.extend(n.children)
        return {
            "move": best.move,
            "seconds": seconds,
            "tree_size": size,
            "tree_height": height,
            "root_playouts": tree.N,
            "children": {ch.move: (ch.N, round(ch.U / ch.N, 3) if ch.N else None,
                                   round(ch.H, 3)) for ch in tree.children},
        }


class RandomPlayer:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def __call__(self, state):
        return self.rng.choice(state.legal_columns())


def play_game(player1, player2, game=None, start=None):
    """Play one game. Returns the final state (its .winner is P1, P2 or DRAW)."""
    game = game or ConnectFour()
    state = (start or game.initial).copy()
    players = {1: player1, 2: player2}
    while not game.is_terminal(state):
        move = players[game.to_move(state)](state)
        state = game.result(state, move)
    return state
