from interview.engine.conditions import (
    evaluate_condition,
    evaluate_conditions,
    get_active_fields,
)
from interview.models.schema import (
    Condition,
    FieldSchema,
    InterviewSchema,
    ValidationRule,
)


def test_evaluate_eq():
    cond = Condition(field="status", op="eq", value="married")
    assert evaluate_condition(cond, {"status": "married"}) is True
    assert evaluate_condition(cond, {"status": "single"}) is False


def test_evaluate_neq():
    cond = Condition(field="status", op="neq", value="married")
    assert evaluate_condition(cond, {"status": "single"}) is True
    assert evaluate_condition(cond, {"status": "married"}) is False


def test_evaluate_in():
    cond = Condition(field="status", op="in", value=["employed", "self_employed"])
    assert evaluate_condition(cond, {"status": "employed"}) is True
    assert evaluate_condition(cond, {"status": "student"}) is False


def test_evaluate_not_in():
    cond = Condition(field="status", op="not_in", value=["employed"])
    assert evaluate_condition(cond, {"status": "student"}) is True
    assert evaluate_condition(cond, {"status": "employed"}) is False


def test_evaluate_gt_lt():
    assert evaluate_condition(Condition(field="age", op="gt", value=18), {"age": 25}) is True
    assert evaluate_condition(Condition(field="age", op="gt", value=18), {"age": 18}) is False
    assert evaluate_condition(Condition(field="age", op="lt", value=18), {"age": 10}) is True


def test_evaluate_gte_lte():
    assert evaluate_condition(Condition(field="age", op="gte", value=18), {"age": 18}) is True
    assert evaluate_condition(Condition(field="age", op="lte", value=18), {"age": 18}) is True


def test_evaluate_exists():
    assert evaluate_condition(Condition(field="name", op="exists"), {"name": "John"}) is True
    assert evaluate_condition(Condition(field="name", op="exists"), {"name": None}) is False
    assert evaluate_condition(Condition(field="name", op="exists"), {}) is False


def test_evaluate_not_exists():
    assert evaluate_condition(Condition(field="name", op="not_exists"), {}) is True
    assert evaluate_condition(Condition(field="name", op="not_exists"), {"name": None}) is True
    assert evaluate_condition(Condition(field="name", op="not_exists"), {"name": "John"}) is False


def test_evaluate_nested_path():
    cond = Condition(field="user.status", op="eq", value="active")
    assert evaluate_condition(cond, {"user": {"status": "active"}}) is True
    assert evaluate_condition(cond, {"user": {"status": "inactive"}}) is False
    assert evaluate_condition(cond, {}) is False


def test_evaluate_conditions_and_logic():
    conditions = [
        Condition(field="age", op="gte", value=18),
        Condition(field="status", op="eq", value="active"),
    ]
    assert evaluate_conditions(conditions, {"age": 25, "status": "active"}) is True
    assert evaluate_conditions(conditions, {"age": 25, "status": "inactive"}) is False
    assert evaluate_conditions(conditions, {"age": 10, "status": "active"}) is False


def test_evaluate_conditions_empty():
    assert evaluate_conditions([], {}) is True


def test_get_active_fields_with_conditions():
    schema = InterviewSchema(
        fields={
            "personal": FieldSchema(
                type="object",
                fields={
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
            )
        }
    )

    # When single, spouse_name should not be active
    active = get_active_fields(schema, {"personal": {"marital_status": "single"}})
    assert "personal.marital_status" in active
    assert "personal.spouse_name" not in active

    # When married, spouse_name should be active
    active = get_active_fields(schema, {"personal": {"marital_status": "married"}})
    assert "personal.marital_status" in active
    assert "personal.spouse_name" in active
