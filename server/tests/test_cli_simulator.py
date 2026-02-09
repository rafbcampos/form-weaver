from __future__ import annotations

from interview.cli.simulator import (
    _build_expected_ui_blocks,
    _build_field_descriptions,
    _extract_values_for_fields,
    _select_field_subset,
)
from interview.models.schema import FieldSchema, SelectOption


class TestBuildFieldDescriptions:
    def test_uses_label_when_present(self):
        flat_schema = {
            "name": FieldSchema(type="string", label="Full Name"),
        }
        descriptions = _build_field_descriptions(flat_schema)
        assert descriptions["name"] == "Full Name"

    def test_falls_back_to_path(self):
        flat_schema = {
            "first_name": FieldSchema(type="string"),
        }
        descriptions = _build_field_descriptions(flat_schema)
        assert descriptions["first_name"] == "First Name"

    def test_includes_description(self):
        flat_schema = {
            "bio": FieldSchema(type="text", label="Bio", description="Tell us about yourself"),
        }
        descriptions = _build_field_descriptions(flat_schema)
        assert "Tell us about yourself" in descriptions["bio"]

    def test_includes_options(self):
        flat_schema = {
            "status": FieldSchema(
                type="enum",
                label="Status",
                options=[
                    SelectOption(value="active", label="Active"),
                    SelectOption(value="inactive", label="Inactive"),
                ],
            ),
        }
        descriptions = _build_field_descriptions(flat_schema)
        assert "active" in descriptions["status"]
        assert "inactive" in descriptions["status"]


class TestSelectFieldSubset:
    def test_returns_subset_of_fields(self):
        fields = ["a", "b", "c", "d", "e"]
        subset = _select_field_subset(fields, min_count=1, max_count=3)
        assert 1 <= len(subset) <= 3
        assert all(f in fields for f in subset)

    def test_min_count_respected(self):
        fields = ["a", "b", "c"]
        for _ in range(20):
            subset = _select_field_subset(fields, min_count=2, max_count=3)
            assert len(subset) >= 2

    def test_handles_small_lists(self):
        fields = ["a"]
        subset = _select_field_subset(fields, min_count=1, max_count=5)
        assert subset == ["a"]

    def test_default_max_count(self):
        fields = ["a", "b", "c", "d", "e", "f", "g", "h"]
        subset = _select_field_subset(fields)
        assert 1 <= len(subset) <= 5


class TestExtractValuesForFields:
    def test_extracts_existing_fields(self):
        record = {"name": "John", "age": 25, "city": "NYC"}
        values = _extract_values_for_fields(record, ["name", "age"])
        assert values == {"name": "John", "age": 25}

    def test_skips_missing_fields(self):
        record = {"name": "John"}
        values = _extract_values_for_fields(record, ["name", "missing"])
        assert values == {"name": "John"}

    def test_empty_fields_list(self):
        record = {"name": "John"}
        values = _extract_values_for_fields(record, [])
        assert values == {}


class TestBuildExpectedUiBlocks:
    def test_creates_text_and_form_blocks(self):
        flat_schema = {
            "name": FieldSchema(type="string", label="Name"),
            "age": FieldSchema(type="integer", label="Age"),
        }
        blocks = _build_expected_ui_blocks(["name", "age"], flat_schema)

        assert len(blocks) == 2
        assert blocks[0]["kind"] == "text"
        assert blocks[1]["kind"] == "form"
        assert len(blocks[1]["elements"]) == 2

    def test_enum_with_few_options_uses_radio(self):
        flat_schema = {
            "status": FieldSchema(
                type="enum",
                label="Status",
                options=[
                    SelectOption(value="a", label="A"),
                    SelectOption(value="b", label="B"),
                ],
            ),
        }
        blocks = _build_expected_ui_blocks(["status"], flat_schema)
        element = blocks[1]["elements"][0]
        assert element["kind"] == "radio"

    def test_enum_with_many_options_uses_select(self):
        flat_schema = {
            "country": FieldSchema(
                type="enum",
                label="Country",
                options=[SelectOption(value=f"c{i}", label=f"Country {i}") for i in range(6)],
            ),
        }
        blocks = _build_expected_ui_blocks(["country"], flat_schema)
        element = blocks[1]["elements"][0]
        assert element["kind"] == "select"

    def test_boolean_uses_checkbox(self):
        flat_schema = {
            "agree": FieldSchema(type="boolean", label="Agree"),
        }
        blocks = _build_expected_ui_blocks(["agree"], flat_schema)
        element = blocks[1]["elements"][0]
        assert element["kind"] == "checkbox"

    def test_text_uses_textarea(self):
        flat_schema = {
            "bio": FieldSchema(type="text", label="Bio"),
        }
        blocks = _build_expected_ui_blocks(["bio"], flat_schema)
        element = blocks[1]["elements"][0]
        assert element["kind"] == "textarea"

    def test_skips_unknown_bindings(self):
        flat_schema = {
            "name": FieldSchema(type="string", label="Name"),
        }
        blocks = _build_expected_ui_blocks(["name", "nonexistent"], flat_schema)
        assert len(blocks[1]["elements"]) == 1

    def test_empty_bindings_no_form_block(self):
        blocks = _build_expected_ui_blocks([], {})
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "text"
