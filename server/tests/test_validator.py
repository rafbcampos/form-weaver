from interview.engine.validator import validate_field
from interview.models.schema import FieldSchema, ValidationRule


def test_required_with_value():
    field = FieldSchema(type="string", validation=[ValidationRule(type="required")])
    assert validate_field("John", field) == []


def test_required_empty():
    field = FieldSchema(type="string", validation=[ValidationRule(type="required")])
    errors = validate_field("", field)
    assert len(errors) == 1
    assert "required" in errors[0].lower()


def test_required_none():
    field = FieldSchema(type="string", validation=[ValidationRule(type="required")])
    errors = validate_field(None, field)
    assert len(errors) == 1


def test_min():
    field = FieldSchema(type="integer", validation=[ValidationRule(type="min", param=18)])
    assert validate_field(25, field) == []
    assert len(validate_field(10, field)) == 1


def test_max():
    field = FieldSchema(type="integer", validation=[ValidationRule(type="max", param=120)])
    assert validate_field(25, field) == []
    assert len(validate_field(150, field)) == 1


def test_min_length():
    field = FieldSchema(
        type="string",
        validation=[ValidationRule(type="min_length", param=2)],
    )
    assert validate_field("Jo", field) == []
    assert len(validate_field("J", field)) == 1


def test_max_length():
    field = FieldSchema(
        type="string",
        validation=[ValidationRule(type="max_length", param=5)],
    )
    assert validate_field("John", field) == []
    assert len(validate_field("Jonathan", field)) == 1


def test_pattern():
    field = FieldSchema(
        type="string",
        validation=[
            ValidationRule(
                type="pattern",
                param=r"^[^@]+@[^@]+\.[^@]+$",
                message="Invalid email",
            )
        ],
    )
    assert validate_field("a@b.com", field) == []
    assert validate_field("invalid", field) == ["Invalid email"]


def test_one_of():
    field = FieldSchema(
        type="string",
        validation=[ValidationRule(type="one_of", param=["single", "married", "divorced"])],
    )
    assert validate_field("single", field) == []
    assert len(validate_field("other", field)) == 1


def test_custom_message():
    field = FieldSchema(
        type="integer",
        validation=[ValidationRule(type="min", param=18, message="Must be 18 or older.")],
    )
    errors = validate_field(10, field)
    assert errors == ["Must be 18 or older."]


def test_skip_non_required_empty():
    field = FieldSchema(
        type="string",
        validation=[ValidationRule(type="min_length", param=2)],
    )
    # Non-required field with empty value should pass
    assert validate_field("", field) == []
    assert validate_field(None, field) == []
