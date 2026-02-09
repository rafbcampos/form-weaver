import type { FormElement } from "../../types/ui-blocks";
import { ArrayField } from "./ArrayField";
import { CheckboxField } from "./CheckboxField";
import { NumberField } from "./NumberField";
import { RadioField } from "./RadioField";
import { SelectField } from "./SelectField";
import { TextField } from "./TextField";
import { TextareaField } from "./TextareaField";

interface FieldRendererProps {
  element: FormElement;
  value: unknown;
  onChange: (value: unknown) => void;
  errors: string[];
  allErrors?: Record<string, string[]>;
}

export function FieldRenderer({
  element,
  value,
  onChange,
  errors,
  allErrors = {},
}: FieldRendererProps) {
  switch (element.kind) {
    case "input":
      if (element.type === "integer" || element.type === "float") {
        return (
          <NumberField
            element={element}
            value={(value as number | "") ?? ""}
            onChange={onChange}
            errors={errors}
          />
        );
      }
      return (
        <TextField
          element={element}
          value={(value as string) ?? ""}
          onChange={onChange}
          errors={errors}
        />
      );
    case "select":
      return (
        <SelectField
          element={element}
          value={(value as string) ?? ""}
          onChange={onChange}
          errors={errors}
        />
      );
    case "radio":
      return (
        <RadioField
          element={element}
          value={(value as string) ?? ""}
          onChange={onChange}
          errors={errors}
        />
      );
    case "checkbox":
      return (
        <CheckboxField
          element={element}
          value={(value as boolean) ?? false}
          onChange={onChange}
          errors={errors}
        />
      );
    case "textarea":
      return (
        <TextareaField
          element={element}
          value={(value as string) ?? ""}
          onChange={onChange}
          errors={errors}
        />
      );
    case "array":
      return (
        <ArrayField
          element={element}
          items={(value as Record<string, unknown>[]) ?? []}
          onChange={onChange}
          errors={allErrors}
        />
      );
  }
}
