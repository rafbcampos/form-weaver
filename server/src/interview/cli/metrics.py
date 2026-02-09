from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import dspy


def _parse_ui_blocks(raw: Any) -> list[dict[str, Any]]:
    """Extract UI block dicts from a DSPy prediction response."""
    if hasattr(raw, "response"):
        raw = raw.response
    if hasattr(raw, "ui_blocks"):
        blocks = raw.ui_blocks
        return [b.model_dump() if hasattr(b, "model_dump") else b for b in blocks]
    if isinstance(raw, dict) and "ui_blocks" in raw:
        return list(raw["ui_blocks"])
    return []


def _get_bindings_from_blocks(blocks: list[dict[str, Any]]) -> set[str]:
    """Extract all bindings from a list of UI block dicts."""
    bindings: set[str] = set()
    for block in blocks:
        if block.get("kind") == "form":
            for element in block.get("elements", []):
                binding = element.get("binding")
                if binding:
                    bindings.add(binding)
                for item_el in element.get("item_elements", []):
                    item_binding = item_el.get("binding")
                    if item_binding:
                        bindings.add(item_binding)
    return bindings


def _validate_block_structure(blocks: list[dict[str, Any]], schema_fields: set[str]) -> float:
    """Score structural validity of UI blocks (0.0 to 1.0)."""
    if not blocks:
        return 0.0

    score = 0.0
    checks = 0

    # Check: starts with TextBlock
    checks += 1
    if blocks[0].get("kind") == "text" and blocks[0].get("value"):
        score += 1.0

    # Check: all blocks parse correctly as valid kinds
    checks += 1
    valid_kinds = {"text", "form"}
    all_valid = all(b.get("kind") in valid_kinds for b in blocks)
    if all_valid:
        score += 1.0

    # Check: bindings are valid dot-paths in schema
    bindings = _get_bindings_from_blocks(blocks)
    if bindings:
        checks += 1
        valid_bindings = sum(1 for b in bindings if b in schema_fields)
        score += valid_bindings / len(bindings)

    # Check: form elements have required fields
    checks += 1
    form_blocks = [b for b in blocks if b.get("kind") == "form"]
    elements_valid = True
    for fb in form_blocks:
        for el in fb.get("elements", []):
            if not el.get("binding") or not el.get("label"):
                elements_valid = False
                break
    if elements_valid:
        score += 1.0

    return score / checks if checks > 0 else 0.0


def _score_conciseness(blocks: list[dict[str, Any]], collected_fields: set[str]) -> float:
    """Score conciseness of the response (0.0 to 1.0)."""
    bindings = _get_bindings_from_blocks(blocks)
    if not bindings:
        return 0.5

    num_asked = len(bindings)

    # Penalize asking for already-collected fields
    already_collected = bindings & collected_fields
    if already_collected:
        penalty = len(already_collected) / num_asked
        return max(0.0, 1.0 - penalty)

    # Ideal: 2-5 fields
    if 2 <= num_asked <= 5:
        return 1.0
    if num_asked == 1:
        return 0.7
    if num_asked > 5:
        return max(0.0, 1.0 - (num_asked - 5) * 0.15)

    return 0.5


def interview_step_metric(
    example: dspy.Example,
    prediction: Any,
    trace: Any = None,  # noqa: ARG001
) -> float:
    """Metric for InterviewStep optimization.

    Scores along 3 axes:
    - Binding coverage (0.4 weight)
    - Structural validity (0.3 weight)
    - Conciseness (0.3 weight)
    """
    expected_bindings = set(example.expected_field_bindings)
    predicted_blocks = _parse_ui_blocks(prediction)

    # Parse schema field paths for validation
    schema_fields: set[str] = set()
    try:
        schema_dict = json.loads(example.field_schema)
        schema_fields = set(schema_dict.keys())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Binding coverage
    predicted_bindings = _get_bindings_from_blocks(predicted_blocks)
    if expected_bindings:
        covered = len(expected_bindings & predicted_bindings)
        binding_score = covered / len(expected_bindings)
    else:
        binding_score = 1.0 if not predicted_bindings else 0.5

    # Structural validity
    structure_score = _validate_block_structure(predicted_blocks, schema_fields)

    # Conciseness
    collected_fields: set[str] = set()
    try:
        current_data = json.loads(example.current_data)
        collected_fields = _get_collected_field_paths(current_data)
    except (json.JSONDecodeError, AttributeError):
        pass
    conciseness_score = _score_conciseness(predicted_blocks, collected_fields)

    return 0.4 * binding_score + 0.3 * structure_score + 0.3 * conciseness_score


def _get_collected_field_paths(data: dict[str, Any], prefix: str = "") -> set[str]:
    """Get all dot-notation paths that have values in the data dict."""
    paths: set[str] = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.update(_get_collected_field_paths(value, path))
        elif value is not None and value != "" and value != []:
            paths.add(path)
    return paths


def _parse_extracted(raw: Any) -> dict[str, Any]:
    """Extract the extracted dict from a DSPy prediction response."""
    if hasattr(raw, "response"):
        raw = raw.response
    if hasattr(raw, "extracted"):
        return dict(raw.extracted)
    if isinstance(raw, dict) and "extracted" in raw:
        return dict(raw["extracted"])
    return {}


def text_extractor_metric(
    example: dspy.Example,
    prediction: Any,
    trace: Any = None,  # noqa: ARG001
) -> float:
    """Metric for TextDataExtractor optimization.

    Scores along 2 axes:
    - Extraction accuracy (0.6 weight)
    - Type correctness (0.4 weight)
    """
    expected = example.expected_extracted
    predicted = _parse_extracted(prediction)

    if not expected:
        # No expected extractions — perfect if nothing extracted
        return 1.0 if not predicted else 0.5

    # Extraction accuracy: fraction of expected key-value pairs present
    correct = 0
    for key, expected_val in expected.items():
        if key in predicted and _values_match(expected_val, predicted[key]):
            correct += 1

    accuracy = correct / len(expected)

    # Penalize spurious extractions
    spurious = set(predicted.keys()) - set(expected.keys())
    if spurious:
        accuracy = max(0.0, accuracy - len(spurious) * 0.1)

    # Type correctness
    type_checks = 0
    type_correct: float = 0
    for key, expected_val in expected.items():
        if key in predicted:
            type_checks += 1
            if type(expected_val) is type(predicted[key]):
                type_correct += 1
            elif isinstance(expected_val, (int, float)) and isinstance(
                predicted[key], (int, float)
            ):
                type_correct += 0.5

    type_score = type_correct / type_checks if type_checks > 0 else 0.0

    return 0.6 * accuracy + 0.4 * type_score


def _values_match(expected: Any, predicted: Any) -> bool:
    """Check if two values match, with some flexibility for numeric types."""
    if expected == predicted:
        return True
    # Allow int/float equivalence (e.g., 25 == 25.0)
    if isinstance(expected, (int, float)) and isinstance(predicted, (int, float)):
        return float(expected) == float(predicted)
    # Allow string comparison
    return str(expected).lower() == str(predicted).lower()
