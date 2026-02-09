from __future__ import annotations

import re
from typing import Any

from interview.engine.conditions import _resolve_path, get_active_fields
from interview.models.schema import FieldSchema, InterviewSchema, ValidationRule


def validate_field(value: Any, field: FieldSchema) -> list[str]:
    errors: list[str] = []
    for rule in field.validation:
        err = _check_rule(value, rule)
        if err:
            errors.append(err)
    return errors


def _check_rule(value: Any, rule: ValidationRule) -> str | None:
    custom = rule.message
    rtype = rule.type
    param = rule.param

    if rtype == "required":
        if value is None or value == "" or value == []:
            return custom or "This field is required."
        return None

    # Skip further checks if value is absent (non-required)
    if value is None or value == "":
        return None

    if rtype == "min":
        if isinstance(value, (int, float)) and value < param:
            return custom or f"Must be at least {param}."
    elif rtype == "max":
        if isinstance(value, (int, float)) and value > param:
            return custom or f"Must be at most {param}."
    elif rtype == "min_length":
        if isinstance(value, str) and len(value) < param:
            return custom or f"Must be at least {param} characters."
    elif rtype == "max_length":
        if isinstance(value, str) and len(value) > param:
            return custom or f"Must be at most {param} characters."
    elif rtype == "pattern":
        if isinstance(value, str) and not re.search(param, value):
            return custom or f"Must match pattern {param}."
    elif rtype == "one_of":
        allowed = param or []
        if value not in allowed:
            return custom or f"Must be one of: {', '.join(str(a) for a in allowed)}."
    return None


def validate_data(
    data: dict[str, Any],
    schema: InterviewSchema,
    current_data: dict[str, Any],
) -> dict[str, list[str]]:
    """Validate a flat dict of submitted data (binding-path → value)
    against the active schema. Returns errors keyed by dot-path."""
    active = get_active_fields(schema, current_data)
    errors: dict[str, list[str]] = {}

    for path, field in active.items():
        found, value = _resolve_path(data, path)
        if not found:
            # Check if it's in flat binding form
            value = data.get(path)

        field_errors = validate_field(value, field)
        if field_errors:
            errors[path] = field_errors

    return errors
