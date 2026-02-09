export type ValidationRuleType =
  | "required"
  | "min"
  | "max"
  | "min_length"
  | "max_length"
  | "pattern"
  | "one_of";

export interface ValidationRule {
  type: ValidationRuleType;
  param?: unknown;
  message?: string;
}

export type ConditionOp =
  | "eq"
  | "neq"
  | "in"
  | "not_in"
  | "gt"
  | "lt"
  | "gte"
  | "lte"
  | "exists"
  | "not_exists";

export interface Condition {
  field: string;
  op: ConditionOp;
  value?: unknown;
}

export interface SelectOption {
  value: string;
  label: string;
}

export type FieldType =
  | "string"
  | "text"
  | "integer"
  | "float"
  | "boolean"
  | "date"
  | "enum"
  | "object"
  | "array";

export interface FieldSchema {
  type: FieldType;
  label?: string;
  description?: string;
  validation: ValidationRule[];
  conditions: Condition[];
  options: SelectOption[];
  fields: Record<string, FieldSchema>;
  item_schema?: FieldSchema;
}

export interface InterviewSchema {
  fields: Record<string, FieldSchema>;
}
