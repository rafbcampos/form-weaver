from __future__ import annotations

import logging
import random
import statistics
from pathlib import Path
from typing import Any

import dspy

from interview.cli.examples import (
    load_interview_step_examples,
    load_text_extractor_examples,
    save_dataset,
)
from interview.cli.metrics import interview_step_metric, text_extractor_metric
from interview.cli.programs import get_default_path, load_optimized, save_optimized
from interview.cli.simulator import generate_training_data
from interview.config import settings
from interview.engine.dspy_modules import create_interview_step, create_text_extractor

logger = logging.getLogger(__name__)


def _configure_dspy() -> None:
    """Configure DSPy LM from application settings."""
    settings.validate_api_key()
    lm = dspy.LM(settings.llm_model)
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())


def _get_module_config(
    module_name: str,
) -> tuple[
    dspy.Module,
    Any,
    Any,
]:
    """Get the base program, metric, and example loader for a module name.

    Returns (program, metric_fn, example_loader_fn).
    """
    if module_name == "interview_step":
        return (
            create_interview_step(),
            interview_step_metric,
            load_interview_step_examples,
        )
    if module_name == "text_extractor":
        return (
            create_text_extractor(),
            text_extractor_metric,
            load_text_extractor_examples,
        )
    msg = f"Unknown module: {module_name}. Must be 'interview_step' or 'text_extractor'."
    raise ValueError(msg)


def cmd_generate(
    schema_path: Path,
    count: int,
    output_path: Path,
) -> None:
    """Generate synthetic training examples from a schema."""
    _configure_dspy()

    print(f"Generating {count} synthetic records from {schema_path}...")
    dataset = generate_training_data(schema_path, count=count)

    save_dataset(dataset, output_path)
    print(f"Saved {len(dataset.interview_step_examples)} interview step examples")
    print(f"Saved {len(dataset.text_extractor_examples)} text extractor examples")
    print(f"Output: {output_path}")


def cmd_optimize(
    module_name: str,
    examples_path: Path,
    optimizer_name: str,
    output_path: Path | None,
    max_demos: int,
    num_trials: int,
    eval_split: float,
) -> None:
    """Run a DSPy optimizer on a module."""
    _configure_dspy()

    program, metric_fn, loader_fn = _get_module_config(module_name)
    examples = loader_fn(examples_path)

    if not examples:
        print(f"No examples found for module '{module_name}' in {examples_path}")
        return

    # Split into train/eval
    random.shuffle(examples)
    split_idx = max(1, int(len(examples) * (1.0 - eval_split)))
    train_set = examples[:split_idx]
    eval_set = examples[split_idx:] if split_idx < len(examples) else examples[-1:]

    print(f"Module: {module_name}")
    print(f"Optimizer: {optimizer_name}")
    print(f"Examples: {len(examples)} total ({len(train_set)} train, {len(eval_set)} eval)")
    print(f"Max demos: {max_demos}, Num trials: {num_trials}")
    print()

    # Instantiate optimizer
    if optimizer_name == "miprov2":
        optimizer = dspy.MIPROv2(
            metric=metric_fn,
            num_threads=1,
            max_bootstrapped_demos=max_demos,
            num_candidates=num_trials,
        )
        optimized = optimizer.compile(program, trainset=train_set, valset=eval_set)
    elif optimizer_name == "bootstrap":
        optimizer = dspy.BootstrapFewShot(
            metric=metric_fn,
            max_bootstrapped_demos=max_demos,
        )
        optimized = optimizer.compile(program, trainset=train_set)
    elif optimizer_name == "gepa":
        optimizer = dspy.GEPA(
            metric=metric_fn,
            num_threads=1,
        )
        optimized = optimizer.compile(program, trainset=train_set, valset=eval_set)
    else:
        msg = f"Unknown optimizer: {optimizer_name}. Must be 'miprov2', 'bootstrap', or 'gepa'."
        raise ValueError(msg)

    # Save
    if output_path is None:
        output_path = get_default_path(module_name)

    save_optimized(optimized, output_path)
    print(f"\nOptimized program saved to: {output_path}")

    # Evaluate on eval set
    print("\nEvaluating on held-out set...")
    scores = _evaluate_examples(optimized, eval_set, metric_fn)
    _print_scores(scores)


def cmd_evaluate(
    module_name: str,
    examples_path: Path,
    program_path: Path | None,
) -> None:
    """Evaluate a saved optimized program on examples."""
    _configure_dspy()

    program, metric_fn, loader_fn = _get_module_config(module_name)
    examples = loader_fn(examples_path)

    if not examples:
        print(f"No examples found for module '{module_name}' in {examples_path}")
        return

    if program_path is not None:
        program = load_optimized(program, program_path)
        print(f"Evaluating optimized program from: {program_path}")
    else:
        print("Evaluating unoptimized baseline")

    print(f"Module: {module_name}")
    print(f"Examples: {len(examples)}")
    print()

    scores = _evaluate_examples(program, examples, metric_fn)
    _print_scores(scores)


def _evaluate_examples(
    program: dspy.Module,
    examples: list[dspy.Example],
    metric_fn: Any,
) -> list[float]:
    """Run program on examples and score with metric. Returns list of scores."""
    scores: list[float] = []
    for i, example in enumerate(examples):
        try:
            # Extract input fields for the program call
            inputs = {k: example[k] for k in example.inputs()}
            prediction = program(**inputs)
            score = metric_fn(example, prediction)
            scores.append(float(score))
            print(f"  Example {i + 1}: {score:.3f}")
        except Exception as e:
            print(f"  Example {i + 1}: ERROR - {e}")
            scores.append(0.0)
    return scores


def _print_scores(scores: list[float]) -> None:
    """Print aggregate statistics for a list of scores."""
    if not scores:
        print("No scores to report.")
        return

    print()
    print(f"  Mean:   {statistics.mean(scores):.3f}")
    print(f"  Median: {statistics.median(scores):.3f}")
    print(f"  Min:    {min(scores):.3f}")
    print(f"  Max:    {max(scores):.3f}")
