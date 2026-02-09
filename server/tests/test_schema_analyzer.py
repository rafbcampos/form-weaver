from interview.engine.schema_analyzer import (
    flatten_schema,
    get_invalid_fields,
    get_missing_fields,
    is_complete,
)
from interview.models.schema import (
    Condition,
    FieldSchema,
    InterviewSchema,
    ValidationRule,
)


def _make_schema() -> InterviewSchema:
    return InterviewSchema(
        fields={
            "personal": FieldSchema(
                type="object",
                fields={
                    "first_name": FieldSchema(
                        type="string",
                        validation=[ValidationRule(type="required")],
                    ),
                    "age": FieldSchema(
                        type="integer",
                        validation=[
                            ValidationRule(type="required"),
                            ValidationRule(type="min", param=18),
                        ],
                    ),
                    "marital_status": FieldSchema(
                        type="enum",
                        validation=[ValidationRule(type="required")],
                    ),
                    "spouse_name": FieldSchema(
                        type="string",
                        validation=[ValidationRule(type="required")],
                        conditions=[
                            Condition(
                                field="personal.marital_status",
                                op="eq",
                                value="married",
                            )
                        ],
                    ),
                },
            ),
            "bio": FieldSchema(type="text"),
        }
    )


def test_flatten_schema():
    schema = _make_schema()
    flat = flatten_schema(schema)
    assert "personal.first_name" in flat
    assert "personal.age" in flat
    assert "personal.marital_status" in flat
    assert "personal.spouse_name" in flat
    assert "bio" in flat
    assert "personal" not in flat  # object itself shouldn't appear


def test_get_missing_fields_all_empty():
    schema = _make_schema()
    missing = get_missing_fields(schema, {})
    assert "personal.first_name" in missing
    assert "personal.age" in missing
    assert "personal.marital_status" in missing
    # spouse_name should NOT be missing because condition not met
    assert "personal.spouse_name" not in missing


def test_get_missing_fields_married():
    schema = _make_schema()
    data = {"personal": {"marital_status": "married"}}
    missing = get_missing_fields(schema, data)
    assert "personal.first_name" in missing
    assert "personal.age" in missing
    assert "personal.spouse_name" in missing  # condition met


def test_get_missing_fields_partial():
    schema = _make_schema()
    data = {
        "personal": {
            "first_name": "John",
            "age": 25,
            "marital_status": "single",
        }
    }
    missing = get_missing_fields(schema, data)
    assert missing == []


def test_get_invalid_fields():
    schema = _make_schema()
    data = {"personal": {"first_name": "J", "age": 10, "marital_status": "single"}}
    invalid = get_invalid_fields(schema, data)
    assert "personal.age" in invalid
    assert any("18" in msg for msg in invalid["personal.age"])


def test_is_complete_true():
    schema = _make_schema()
    data = {
        "personal": {
            "first_name": "John",
            "age": 25,
            "marital_status": "single",
        }
    }
    assert is_complete(schema, data) is True


def test_is_complete_false_missing():
    schema = _make_schema()
    assert is_complete(schema, {}) is False


def test_is_complete_false_invalid():
    schema = _make_schema()
    data = {
        "personal": {
            "first_name": "John",
            "age": 10,
            "marital_status": "single",
        }
    }
    assert is_complete(schema, data) is False


def test_is_complete_with_conditional():
    schema = _make_schema()
    # Married but no spouse name → incomplete
    data = {
        "personal": {
            "first_name": "John",
            "age": 25,
            "marital_status": "married",
        }
    }
    assert is_complete(schema, data) is False

    # Married with spouse name → complete
    data["personal"]["spouse_name"] = "Jane"
    assert is_complete(schema, data) is True
