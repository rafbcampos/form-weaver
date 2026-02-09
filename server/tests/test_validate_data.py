from __future__ import annotations

from interview.engine.validator import validate_data
from interview.models.schema import (
    Condition,
    FieldSchema,
    InterviewSchema,
    SelectOption,
    ValidationRule,
)


def _schema_with_required_fields() -> InterviewSchema:
    return InterviewSchema(
        fields={
            "name": FieldSchema(
                type="string",
                label="Name",
                validation=[ValidationRule(type="required")],
            ),
            "age": FieldSchema(
                type="integer",
                label="Age",
                validation=[
                    ValidationRule(type="required"),
                    ValidationRule(type="min", param=18),
                ],
            ),
        }
    )


class TestValidateData:
    def test_valid_data_returns_no_errors(self):
        schema = _schema_with_required_fields()
        errors = validate_data(
            {"name": "John", "age": 25},
            schema,
            {"name": "John", "age": 25},
        )
        assert errors == {}

    def test_missing_required_field_returns_error(self):
        schema = _schema_with_required_fields()
        errors = validate_data({}, schema, {})
        assert "name" in errors
        assert "age" in errors

    def test_validation_rule_violation(self):
        schema = _schema_with_required_fields()
        errors = validate_data(
            {"name": "John", "age": 5},
            schema,
            {"name": "John", "age": 5},
        )
        assert "name" not in errors
        assert "age" in errors

    def test_conditional_field_skipped_when_inactive(self):
        schema = InterviewSchema(
            fields={
                "status": FieldSchema(
                    type="enum",
                    label="Status",
                    validation=[ValidationRule(type="required")],
                    options=[
                        SelectOption(value="employed", label="Employed"),
                        SelectOption(value="unemployed", label="Unemployed"),
                    ],
                ),
                "company": FieldSchema(
                    type="string",
                    label="Company",
                    validation=[ValidationRule(type="required")],
                    conditions=[Condition(field="status", op="eq", value="employed")],
                ),
            }
        )
        # Status is unemployed, so company should not be validated
        errors = validate_data(
            {"status": "unemployed"},
            schema,
            {"status": "unemployed"},
        )
        assert "company" not in errors

    def test_conditional_field_validated_when_active(self):
        schema = InterviewSchema(
            fields={
                "status": FieldSchema(
                    type="enum",
                    label="Status",
                    validation=[ValidationRule(type="required")],
                    options=[
                        SelectOption(value="employed", label="Employed"),
                        SelectOption(value="unemployed", label="Unemployed"),
                    ],
                ),
                "company": FieldSchema(
                    type="string",
                    label="Company",
                    validation=[ValidationRule(type="required")],
                    conditions=[Condition(field="status", op="eq", value="employed")],
                ),
            }
        )
        # Status is employed, so company is required but missing
        errors = validate_data(
            {"status": "employed"},
            schema,
            {"status": "employed"},
        )
        assert "company" in errors

    def test_flat_binding_lookup(self):
        """validate_data should find values in flat binding form (data dict)."""
        schema = _schema_with_required_fields()
        # Data is flat bindings, current_data is empty
        errors = validate_data(
            {"name": "John", "age": 25},
            schema,
            {},
        )
        # name and age should pass since they're in the submitted data dict
        assert "name" not in errors
        assert "age" not in errors
