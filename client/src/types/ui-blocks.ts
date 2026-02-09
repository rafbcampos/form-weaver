import type { SelectOption } from "./schema";

export interface TextBlock {
  kind: "text";
  value: string;
}

export interface InputElement {
  kind: "input";
  type: "text" | "integer" | "float" | "email" | "date" | "phone";
  label: string;
  binding: string;
  placeholder?: string;
}

export interface SelectElement {
  kind: "select";
  label: string;
  binding: string;
  options: SelectOption[];
}

export interface RadioElement {
  kind: "radio";
  label: string;
  binding: string;
  options: SelectOption[];
}

export interface CheckboxElement {
  kind: "checkbox";
  label: string;
  binding: string;
}

export interface TextareaElement {
  kind: "textarea";
  label: string;
  binding: string;
  placeholder?: string;
}

export interface ArrayElement {
  kind: "array";
  label: string;
  binding: string;
  item_elements: (
    | InputElement
    | SelectElement
    | RadioElement
    | CheckboxElement
    | TextareaElement
  )[];
  add_label: string;
}

export type FormElement =
  | InputElement
  | SelectElement
  | RadioElement
  | CheckboxElement
  | TextareaElement
  | ArrayElement;

export interface FormBlock {
  kind: "form";
  elements: FormElement[];
}

export type UIBlock = TextBlock | FormBlock;
