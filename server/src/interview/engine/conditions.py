from __future__ import annotations

from typing import Any

from interview.models.schema import Condition, FieldSchema, InterviewSchema


def _resolve_path(data: dict[str, Any], path: str) -> tuple[bool, Any]:
    """Walk a dot-notation path through nested dicts/lists.

    Returns (found, value).  `found=False` means the path didn't exist.
    """
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def evaluate_condition(condition: Condition, data: dict[str, Any]) -> bool:
    found, value = _resolve_path(data, condition.field)
    op = condition.op
    expected = condition.value

    if op == "exists":
        return found and value is not None
    if op == "not_exists":
        return not found or value is None

    if not found:
        return False

    if op == "eq":
        return bool(value == expected)
    if op == "neq":
        return bool(value != expected)
    if op == "in":
        return bool(value in (expected or []))
    if op == "not_in":
        return bool(value not in (expected or []))
    if op == "gt":
        return bool(value > expected)
    if op == "lt":
        return bool(value < expected)
    if op == "gte":
        return bool(value >= expected)
    if op == "lte":
        return bool(value <= expected)

    return False


def evaluate_conditions(conditions: list[Condition], data: dict[str, Any]) -> bool:
    """AND logic: all conditions must pass.  Empty list → True."""
    return all(evaluate_condition(c, data) for c in conditions)


def _collect_active_fields(
    fields: dict[str, FieldSchema],
    data: dict[str, Any],
    prefix: str,
    out: dict[str, FieldSchema],
) -> None:
    for name, field in fields.items():
        path = f"{prefix}.{name}" if prefix else name

        if not evaluate_conditions(field.conditions, data):
            continue

        if field.type == "object" and field.fields:
            _collect_active_fields(field.fields, data, path, out)
        else:
            out[path] = field

            if field.type == "array" and field.item_schema and field.item_schema.type == "object":
                found, arr = _resolve_path(data, path)
                if found and isinstance(arr, list):
                    for i in range(len(arr)):
                        item_prefix = f"{path}[{i}]"
                        _collect_active_fields(field.item_schema.fields, data, item_prefix, out)


def get_active_fields(schema: InterviewSchema, data: dict[str, Any]) -> dict[str, FieldSchema]:
    out: dict[str, FieldSchema] = {}
    _collect_active_fields(schema.fields, data, "", out)
    return out
