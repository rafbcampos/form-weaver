from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ValidationRule(BaseModel):
    type: Literal[
        "required",
        "min",
        "max",
        "min_length",
        "max_length",
        "pattern",
        "one_of",
    ]
    param: Any = None
    message: str | None = None


class Condition(BaseModel):
    field: str
    op: Literal[
        "eq",
        "neq",
        "in",
        "not_in",
        "gt",
        "lt",
        "gte",
        "lte",
        "exists",
        "not_exists",
    ]
    value: Any = None


class SelectOption(BaseModel):
    value: str
    label: str


class FieldSchema(BaseModel):
    type: Literal[
        "string",
        "text",
        "integer",
        "float",
        "boolean",
        "date",
        "enum",
        "object",
        "array",
    ]
    label: str | None = None
    description: str | None = None
    validation: list[ValidationRule] = []
    conditions: list[Condition] = []
    options: list[SelectOption] = []
    fields: dict[str, FieldSchema] = {}
    item_schema: FieldSchema | None = None


class InterviewSchema(BaseModel):
    fields: dict[str, FieldSchema]
