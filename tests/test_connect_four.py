"""Tests for the Connect Four game and the MCTS move generator (Question 1)."""

import json
import os

import pytest

from connect_four.game import DRAW, P1, P2, ROWS, ConnectFour, State, from_moves
from connect_four.mcts import MCTSConfig, MCTSPlayer, RandomPlayer, play_game

DATA = os.path.join(os.path.dirname(__file__), "data", "positions.json")
with open(DATA) as f:
    POSITIONS = json.load(f)

game = ConnectFour()


# ---------------------------------------------------------------- game rules
def test_initial_state():
    s = game.initial
    assert game.to_move(s) == P1
    assert game.actions(s) == list(range(7))
    assert not game.is_terminal(s)


def test_result_does_not_change_original_and_alternates_players():
    s = game.initial
    t = game.result(s, 3)
    assert s.moves == 0 and t.moves == 1
    assert game.to_move(t) == P2
    assert t.board[3 * ROWS + 0] == P1


def test_full_column_is_not_an_action():
    s = from_moves([0, 0, 0, 0, 0, 0])
    assert 0 not in game.actions(s)
    with pytest.raises(ValueError):
        s.play(0)


@pytest.mark.parametrize("case", POSITIONS["wins"], ids=lambda c: c["name"])
def test_wins_are_detected(case):
    s = from_moves(case["moves"])
    assert game.is_terminal(s)
    assert s.winner == case["winner"]
    assert game.utility(s, case["winner"]) == 1
    assert game.utility(s, 3 - case["winner"]) == -1
    assert game.actions(s) == []


@pytest.mark.parametrize("case", POSITIONS["not_wins"], ids=lambda c: c["name"])
def test_non_wins_are_not_terminal(case):
    s = from_moves(case["moves"])
    assert not game.is_terminal(s)


def test_full_board_draw():
    s = from_moves(POSITIONS["draw"]["moves"])
    assert s.winner == DRAW
    assert game.utility(s, P1) == 0 and game.utility(s, P2) == 0


def test_evaluate_is_symmetric_and_favours_threats():
    s = from_moves([0, 6, 1, 6, 2])  # X has three on the bottom row
    assert game.evaluate(s, P1) == -game.evaluate(s, P2)
    assert game.evaluate(s, P1) > 0


# ---------------------------------------------------------------- MCTS
@pytest.mark.parametrize("case", POSITIONS["tactics"], ids=lambda c: c["name"])
def test_mcts_finds_tactical_move(case):
    p = MCTSPlayer(MCTSConfig(cycles=800, seed=0))
    assert p(from_moves(case["moves"])) == case["best"]


@pytest.mark.parametrize("w", [0.0, 1.0, 5.0])
def test_mcts_finds_tactical_move_for_every_utility_weight(w):
    case = POSITIONS["tactics"][0]
    p = MCTSPlayer(MCTSConfig(cycles=800, w_objective=w, seed=0))
    assert p(from_moves(case["moves"])) == case["best"]


def test_cycles_equal_root_playouts():
    p = MCTSPlayer(MCTSConfig(cycles=137, seed=1))
    p(game.initial)
    assert p.last_stats["root_playouts"] == 137
    assert sum(n for n, _, _ in p.last_stats["children"].values()) == 137


@pytest.mark.parametrize("depth", [1, 2, 3])
def test_tree_height_is_limited(depth):
    p = MCTSPlayer(MCTSConfig(cycles=300, max_depth=depth, seed=1))
    p(game.initial)
    assert p.last_stats["tree_height"] <= depth


@pytest.mark.parametrize("width", [1, 2, 4])
def test_expansion_width_limits_children(width):
    p = MCTSPlayer(MCTSConfig(cycles=300, expansion_width=width, seed=1))
    tree_root_children = None
    p(game.initial)
    tree_root_children = p.last_stats["children"]
    assert len(tree_root_children) == width


def test_same_seed_gives_same_move_and_tree():
    a = MCTSPlayer(MCTSConfig(cycles=300, seed=42))
    b = MCTSPlayer(MCTSConfig(cycles=300, seed=42))
    s = from_moves([3, 3, 2])
    assert a(s) == b(s)
    assert a.last_stats["children"] == b.last_stats["children"]


def test_returned_move_is_legal_and_most_played():
    s = from_moves([0, 0, 0, 0, 0, 0])  # column 0 full
    p = MCTSPlayer(MCTSConfig(cycles=300, seed=3))
    m = p(s)
    assert m in game.actions(s)
    kids = p.last_stats["children"]
    assert kids[m][0] == max(n for n, _, _ in kids.values())


def test_random_expansion_order_works():
    p = MCTSPlayer(MCTSConfig(cycles=200, expansion_width=3,
                              expansion_order="random", seed=5))
    assert p(game.initial) in range(7)


def test_mcts_beats_random_player():
    wins = 0
    for g in range(4):
        me = MCTSPlayer(MCTSConfig(cycles=200, seed=g))
        rnd = RandomPlayer(seed=100 + g)
        if g % 2 == 0:
            wins += play_game(me, rnd).winner == P1
        else:
            wins += play_game(rnd, me).winner == P2
    assert wins >= 3


def test_play_game_ends_in_terminal_state():
    final = play_game(RandomPlayer(1), RandomPlayer(2))
    assert final.winner in (P1, P2, DRAW)


def test_quick_experiment_run(tmp_path, monkeypatch):
    from connect_four import experiments
    monkeypatch.setattr(experiments, "RESULTS", str(tmp_path))
    assert experiments.main(["--quick", "--workers", "1", "--runs", "2", "--games", "2"]) == 0
    assert (tmp_path / "quick" / "summary.md").exists()
    assert (tmp_path / "quick" / "consistency_summary.csv").exists()
