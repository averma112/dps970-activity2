"""Experiments for Question 1.

Run:  python -m connect_four.experiments            (full run, a few minutes)
      python -m connect_four.experiments --quick    (small run for CI)

Each setting is changed one at a time from a baseline configuration, so any
difference in the results comes from that setting alone.

Experiment 1 (consistency and tactics): every configuration searches four
fixed positions many times with different random seeds. We record which move
it picks, how often it picks its most common move, how often it finds the
correct move in the two tactical positions, the tree size and the time.

Experiment 2 (strength): every configuration plays a match against a fixed
reference player (plain UCT: W = 0, x = 7, no depth limit) and against a
random player, alternating who moves first.

Results go to results/*.csv, results/summary.md and results/*.png.
"""

import argparse
import csv
import os
import statistics
import sys
from collections import Counter
from dataclasses import asdict, replace
from multiprocessing import Pool

from .game import DRAW, P1, P2, from_moves
from .mcts import MCTSConfig, MCTSPlayer, RandomPlayer, play_game

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

# Test positions: (name, moves from the empty board, correct move or None)
POSITIONS = [
    ("empty", [], None),
    # X has three in a row on the bottom (cols 0-2); O must block at column 3.
    ("must_block", [0, 6, 1, 6, 2], 3),
    # X has three stacked in column 0; X wins immediately at column 0.
    ("win_now", [0, 1, 0, 1, 0, 2], 0),
    # A quiet middle game position with no immediate win or forced block.
    ("midgame", [3, 3, 2, 4, 4, 2, 5, 1], None),
]

BASELINE = MCTSConfig(cycles=1000, expansion_width=7, max_depth=42,
                      c=1.414, w_objective=1.0, expansion_order="objective")


def variants(quick=False):
    """(experiment group, label, config) changed one setting at a time."""
    b = BASELINE
    out = [("baseline", "baseline", b)]
    cycles = [50, 1000] if quick else [50, 200, 1000, 3000]
    widths = [2, 7] if quick else [1, 2, 3, 5, 7]
    depths = [1, 42] if quick else [1, 2, 4, 8, 42]
    weights = [0.0, 5.0] if quick else [0.0, 1.0, 5.0, 20.0]
    cs = [] if quick else [0.5, 1.414, 3.0]
    for v in cycles:
        out.append(("cycles", f"cycles={v}", replace(b, cycles=v)))
    for v in widths:
        out.append(("width", f"x={v}", replace(b, expansion_width=v)))
    if not quick:
        out.append(("width", "x=3 random", replace(b, expansion_width=3, expansion_order="random")))
    for v in depths:
        out.append(("depth", f"depth={v}", replace(b, max_depth=v)))
    for v in weights:
        out.append(("utility", f"W={v:g}", replace(b, w_objective=v)))
    for v in cs:
        out.append(("utility", f"C={v:g}", replace(b, c=v)))
    if quick:
        out = [(g, lab, replace(cfg, cycles=min(cfg.cycles, 200))) for g, lab, cfg in out]
    return out


# --------------------------------------------------------------------- experiment 1
def _search(job):
    group, label, cfg, pos_name, moves, correct, seed = job
    player = MCTSPlayer(replace(cfg, seed=seed))
    move = player(from_moves(moves))
    st = player.last_stats
    return {"group": group, "config": label, "position": pos_name, "seed": seed,
            "move": move, "correct": "" if correct is None else int(move == correct),
            "tree_size": st["tree_size"], "tree_height": st["tree_height"],
            "seconds": round(st["seconds"], 4)}


def experiment_consistency(configs, runs, pool):
    jobs = [(g, lab, cfg, name, moves, correct, seed)
            for g, lab, cfg in configs
            for name, moves, correct in POSITIONS
            for seed in range(runs)]
    return pool.map(_search, jobs, chunksize=4)


def summarise_consistency(rows):
    out = []
    key = lambda r: (r["config"], r["position"])
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    for (label, pos), rs in groups.items():
        moves = Counter(r["move"] for r in rs)
        mode, freq = moves.most_common(1)[0]
        correct = [r["correct"] for r in rs if r["correct"] != ""]
        out.append({
            "group": rs[0]["group"], "config": label, "position": pos, "runs": len(rs),
            "most_common_move": mode, "agreement": round(freq / len(rs), 3),
            "distinct_moves": len(moves),
            "move_counts": " ".join(f"{m}:{n}" for m, n in sorted(moves.items())),
            "accuracy": round(sum(correct) / len(correct), 3) if correct else "",
            "mean_tree_size": round(statistics.mean(r["tree_size"] for r in rs)),
            "mean_seconds": round(statistics.mean(r["seconds"] for r in rs), 3),
        })
    return out


# --------------------------------------------------------------------- experiment 2
REFERENCE = replace(BASELINE, w_objective=0.0)  # plain UCT with UCB1


def _match_game(job):
    group, label, cfg, opponent, game_no, ref_cycles = job
    me = MCTSPlayer(replace(cfg, seed=1000 + game_no))
    if opponent == "random":
        opp = RandomPlayer(seed=2000 + game_no)
    else:
        opp = MCTSPlayer(replace(REFERENCE, cycles=ref_cycles, seed=3000 + game_no))
    me_first = game_no % 2 == 0
    final = play_game(me, opp) if me_first else play_game(opp, me)
    me_id = P1 if me_first else P2
    outcome = "draw" if final.winner == DRAW else ("win" if final.winner == me_id else "loss")
    return {"group": group, "config": label, "opponent": opponent, "game": game_no,
            "moved_first": int(me_first), "outcome": outcome, "plies": final.moves}


def experiment_strength(configs, games, pool, ref_cycles, match_cycles):
    jobs = []
    for g, lab, cfg in configs:
        # Cycles are reduced for the matches (unless cycles is the setting under
        # test) so that the matches finish in reasonable time.
        c = cfg if g == "cycles" else replace(cfg, cycles=min(cfg.cycles, match_cycles))
        for opp in ("reference", "random"):
            n = games if opp == "reference" else max(2, games // 2)
            for k in range(n):
                jobs.append((g, lab, c, opp, k, ref_cycles))
    return pool.map(_match_game, jobs, chunksize=1)


def summarise_strength(rows):
    out = {}
    for r in rows:
        k = (r["group"], r["config"], r["opponent"])
        d = out.setdefault(k, Counter())
        d[r["outcome"]] += 1
    table = []
    for (g, lab, opp), c in out.items():
        n = sum(c.values())
        table.append({"group": g, "config": lab, "opponent": opp, "games": n,
                      "wins": c["win"], "draws": c["draw"], "losses": c["loss"],
                      "score": round((c["win"] + 0.5 * c["draw"]) / n, 3)})
    return table


# --------------------------------------------------------------------- output
def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def md_table(rows, cols):
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def plots(cons, strength):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    groups = ["cycles", "width", "depth", "utility"]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.2), sharey=True)
    for ax, g in zip(axes, groups):
        labels = [r["config"] for r in cons if r["group"] == g and r["position"] == "empty"]
        for pos, marker in (("empty", "o"), ("midgame", "s"), ("must_block", "^"), ("win_now", "v")):
            vals = [r["agreement"] for r in cons if r["group"] == g and r["position"] == pos]
            ax.plot(labels, vals, marker=marker, label=pos)
        ax.set_title(f"Move agreement vs {g}")
        ax.set_ylim(0, 1.05)
        ax.tick_params(axis="x", rotation=40)
    axes[0].set_ylabel("share of runs picking the most common move")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "agreement.png"), dpi=120)
    plt.close(fig)

    fig, axes = plt.subplots(1, 4, figsize=(18, 4.2), sharey=True)
    for ax, g in zip(axes, groups):
        rows = [r for r in strength if r["group"] == g and r["opponent"] == "reference"]
        ax.bar([r["config"] for r in rows], [r["score"] for r in rows], color="#4C72B0")
        ax.axhline(0.5, color="grey", lw=0.8, ls="--")
        ax.set_title(f"Score vs reference UCT: {g}")
        ax.set_ylim(0, 1.05)
        ax.tick_params(axis="x", rotation=40)
    axes[0].set_ylabel("score (win = 1, draw = 0.5)")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "strength.png"), dpi=120)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--runs", type=int, default=None, help="searches per position")
    ap.add_argument("--games", type=int, default=None, help="games per match")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args(argv)
    runs = args.runs or (4 if args.quick else 20)
    games = args.games or (2 if args.quick else 10)
    ref_cycles = 100 if args.quick else 300
    match_cycles = 100 if args.quick else 300
    global RESULTS
    if args.quick and not RESULTS.endswith("quick"):
        RESULTS = os.path.join(RESULTS, "quick")  # keep the full results intact
    os.makedirs(RESULTS, exist_ok=True)
    configs = variants(args.quick)

    with Pool(args.workers) as pool:
        print(f"Experiment 1: {len(configs)} configs x {len(POSITIONS)} positions x {runs} runs",
              flush=True)
        cons_rows = experiment_consistency(configs, runs, pool)
        print(f"Experiment 2: matches of {games} games", flush=True)
        match_rows = experiment_strength(configs, games, pool, ref_cycles, match_cycles)

    cons = summarise_consistency(cons_rows)
    strength = summarise_strength(match_rows)
    write_csv(os.path.join(RESULTS, "consistency_runs.csv"), cons_rows)
    write_csv(os.path.join(RESULTS, "consistency_summary.csv"), cons)
    write_csv(os.path.join(RESULTS, "match_games.csv"), match_rows)
    write_csv(os.path.join(RESULTS, "match_summary.csv"), strength)
    with open(os.path.join(RESULTS, "configs.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "config"] + list(asdict(BASELINE).keys()))
        for g, lab, cfg in configs:
            w.writerow([g, lab] + list(asdict(cfg).values()))

    with open(os.path.join(RESULTS, "summary.md"), "w") as f:
        f.write(f"# Experiment results\n\nRuns per position: {runs}. Games per match vs "
                f"reference: {games} (vs random: {max(2, games // 2)}). Reference player: "
                f"plain UCT, {ref_cycles} cycles. Match cycles: {match_cycles} "
                f"(except the cycles experiment).\n\n")
        f.write("## Experiment 1: consistency and tactics\n\n")
        f.write(md_table(cons, ["config", "position", "most_common_move", "agreement",
                                "distinct_moves", "move_counts", "accuracy",
                                "mean_tree_size", "mean_seconds"]))
        f.write("\n\n## Experiment 2: strength\n\n")
        f.write(md_table(strength, ["config", "opponent", "games", "wins", "draws",
                                    "losses", "score"]))
        f.write("\n")
    plots(cons, strength)
    print("Results written to", RESULTS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
