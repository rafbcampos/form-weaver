from __future__ import annotations

from typing import Any

from interview.engine.conditions import _resolve_path, evaluate_conditions
from interview.engine.validator import validate_field
from interview.models.schema import FieldSchema, InterviewSchema


def flatten_schema(
    schema: InterviewSchema,
) -> dict[str, FieldSchema]:
    out: dict[str, FieldSchema] = {}
    _flatten_fields(schema.fields, "", out)
    return out


def _flatten_fields(
    fields: dict[str, FieldSchema],
    prefix: str,
    out: dict[str, FieldSchema],
) -> None:
    for name, field in fields.items():
        path = f"{prefix}.{name}" if prefix else name
        if field.type == "object" and field.fields:
            _flatten_fields(field.fields, path, out)
        else:
            out[path] = field


def _is_required(field: FieldSchema) -> bool:
    return any(r.type == "required" for r in field.validation)


def get_missing_fields(schema: InterviewSchema, data: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    _find_missing(schema.fields, data, data, "", missing)
    return missing


def _find_missing(
    fields: dict[str, FieldSchema],
    data: dict[str, Any],
    root_data: dict[str, Any],
    prefix: str,
    missing: list[str],
) -> None:
    for name, field in fields.items():
        path = f"{prefix}.{name}" if prefix else name

        if not evaluate_conditions(field.conditions, root_data):
            continue

        if field.type == "object" and field.fields:
            _find_missing(field.fields, data, root_data, path, missing)
            continue

        if _is_required(field):
            found, value = _resolve_path(root_data, path)
            if not found or value is None or value == "" or value == []:
                missing.append(path)

        if field.type == "array" and field.item_schema and field.item_schema.type == "object":
            found, arr = _resolve_path(root_data, path)
            if found and isinstance(arr, list):
                for i, _item in enumerate(arr):
                    item_prefix = f"{path}[{i}]"
                    _find_missing(
                        field.item_schema.fields,
                        data,
                        root_data,
                        item_prefix,
                        missing,
                    )


def get_invalid_fields(schema: InterviewSchema, data: dict[str, Any]) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    _find_invalid(schema.fields, data, data, "", errors)
    return errors


def _find_invalid(
    fields: dict[str, FieldSchema],
    data: dict[str, Any],
    root_data: dict[str, Any],
    prefix: str,
    errors: dict[str, list[str]],
) -> None:
    for name, field in fields.items():
        path = f"{prefix}.{name}" if prefix else name

        if not evaluate_conditions(field.conditions, root_data):
            continue

        if field.type == "object" and field.fields:
            _find_invalid(field.fields, data, root_data, path, errors)
            continue

        found, value = _resolve_path(root_data, path)
        if found and value is not None and value != "":
            field_errors = validate_field(value, field)
            if field_errors:
                errors[path] = field_errors

        if (
            field.type == "array"
            and field.item_schema
            and field.item_schema.type == "object"
            and found
            and isinstance(value, list)
        ):
            for i, _item in enumerate(value):
                item_prefix = f"{path}[{i}]"
                _find_invalid(
                    field.item_schema.fields,
                    data,
                    root_data,
                    item_prefix,
                    errors,
                )


def is_complete(schema: InterviewSchema, data: dict[str, Any]) -> bool:
    return not get_missing_fields(schema, data) and not get_invalid_fields(schema, data)
