from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from interview.models.schema import SelectOption


class TextBlock(BaseModel):
    kind: Literal["text"] = "text"
    value: str


class InputElement(BaseModel):
    kind: Literal["input"] = "input"
    type: Literal["text", "integer", "float", "email", "date", "phone"] = "text"
    label: str
    binding: str
    placeholder: str | None = None


class SelectElement(BaseModel):
    kind: Literal["select"] = "select"
    label: str
    binding: str
    options: list[SelectOption]


class RadioElement(BaseModel):
    kind: Literal["radio"] = "radio"
    label: str
    binding: str
    options: list[SelectOption]


class CheckboxElement(BaseModel):
    kind: Literal["checkbox"] = "checkbox"
    label: str
    binding: str


class TextareaElement(BaseModel):
    kind: Literal["textarea"] = "textarea"
    label: str
    binding: str
    placeholder: str | None = None


class ArrayElement(BaseModel):
    kind: Literal["array"] = "array"
    label: str
    binding: str
    item_elements: list[
        InputElement | SelectElement | RadioElement | CheckboxElement | TextareaElement
    ]
    add_label: str = "Add another"


FormElement = Annotated[
    InputElement | SelectElement | RadioElement | CheckboxElement | TextareaElement | ArrayElement,
    Field(discriminator="kind"),
]


class FormBlock(BaseModel):
    kind: Literal["form"] = "form"
    elements: list[FormElement]


UIBlock = Annotated[TextBlock | FormBlock, Field(discriminator="kind")]
