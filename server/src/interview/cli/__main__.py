from __future__ import annotations

import argparse
import logging
from pathlib import Path

from interview.cli.commands import cmd_evaluate, cmd_generate, cmd_optimize


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="interview-cli",
        description="DSPy prompt optimization CLI for the interview system",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen_parser = subparsers.add_parser(
        "generate", help="Generate synthetic training examples from a schema"
    )
    gen_parser.add_argument("--schema", type=Path, required=True, help="Path to schema JSON file")
    gen_parser.add_argument(
        "--count", type=int, default=10, help="Number of records to simulate (default: 10)"
    )
    gen_parser.add_argument("--output", type=Path, required=True, help="Output JSON path")

    # optimize
    opt_parser = subparsers.add_parser("optimize", help="Run a DSPy optimizer on a module")
    opt_parser.add_argument(
        "--module",
        required=True,
        choices=["interview_step", "text_extractor"],
        help="Module to optimize",
    )
    opt_parser.add_argument(
        "--examples", type=Path, required=True, help="Path to training dataset JSON"
    )
    opt_parser.add_argument(
        "--optimizer",
        default="miprov2",
        choices=["miprov2", "bootstrap", "gepa"],
        help="Optimizer to use (default: miprov2)",
    )
    opt_parser.add_argument(
        "--output", type=Path, default=None, help="Path to save optimized state"
    )
    opt_parser.add_argument(
        "--max-demos", type=int, default=4, help="Max few-shot demos (default: 4)"
    )
    opt_parser.add_argument(
        "--num-trials", type=int, default=15, help="Optimization trials for MIPROv2 (default: 15)"
    )
    opt_parser.add_argument(
        "--eval-split",
        type=float,
        default=0.2,
        help="Fraction of examples for evaluation (default: 0.2)",
    )

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a program on examples")
    eval_parser.add_argument(
        "--module",
        required=True,
        choices=["interview_step", "text_extractor"],
        help="Module to evaluate",
    )
    eval_parser.add_argument("--examples", type=Path, required=True, help="Path to dataset JSON")
    eval_parser.add_argument(
        "--program",
        type=Path,
        default=None,
        help="Path to optimized program (omit for baseline)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.command == "generate":
        cmd_generate(
            schema_path=args.schema,
            count=args.count,
            output_path=args.output,
        )
    elif args.command == "optimize":
        cmd_optimize(
            module_name=args.module,
            examples_path=args.examples,
            optimizer_name=args.optimizer,
            output_path=args.output,
            max_demos=args.max_demos,
            num_trials=args.num_trials,
            eval_split=args.eval_split,
        )
    elif args.command == "evaluate":
        cmd_evaluate(
            module_name=args.module,
            examples_path=args.examples,
            program_path=args.program,
        )


if __name__ == "__main__":
    main()
