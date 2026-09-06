import argparse

from .generate import generate_batch
from .ladder import generate_ladder
from .pilot import generate_pilot
from .recipes import RECIPES


def main():
    ap = argparse.ArgumentParser(prog="geomake", description="Geometry puzzle generator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate verified puzzles (PNG + JSON/JSONL)")
    g.add_argument("--n", type=int, default=10, help="number of puzzles")
    g.add_argument("--depth", type=int, choices=[1, 2, 3], default=None,
                   help="deduction-chain depth; omit for a mix")
    g.add_argument("--recipe", choices=sorted(RECIPES), default=None,
                   help="force a specific recipe")
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--out", default="out")
    g.add_argument("--show-answer", action="store_true",
                   help="print the answer as the figure title (answer-key mode)")

    ls = sub.add_parser("recipes", help="list available recipes")

    ld = sub.add_parser("ladder", help="graded easy->hard sequence with validated ordering")
    ld.add_argument("--n", type=int, default=12, help="number of puzzles in the ladder")
    ld.add_argument("--seed", type=int, default=0)
    ld.add_argument("--out", default="ladder")

    pilot = sub.add_parser("pilot", help="seven authored daily sessions with separate hints and explanations")
    pilot.add_argument("--seed", type=int, default=7, help="use the same seed for both players")
    pilot.add_argument("--out", default="out/pilot")

    args = ap.parse_args()
    if args.cmd == "recipes":
        for name, (_, depth) in sorted(RECIPES.items(), key=lambda kv: (kv[1][1], kv[0])):
            print(f"  depth {depth}  {name}")
        return
    if args.cmd == "ladder":
        generate_ladder(args.n, args.seed, args.out)
        return
    if args.cmd == "pilot":
        try:
            generate_pilot(args.seed, args.out)
        except (ValueError, RuntimeError) as error:
            ap.error(str(error))
        return
    generate_batch(args.n, args.depth, args.seed, args.out,
                   recipe=args.recipe, show_answer=args.show_answer)


if __name__ == "__main__":
    main()
