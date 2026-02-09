import type { ValidationRule } from "../types/schema";

export function validateField(value: unknown, rules: ValidationRule[]): string[] {
  const errors: string[] = [];

  for (const rule of rules) {
    const err = checkRule(value, rule);
    if (err) {
      errors.push(err);
    }
  }

  return errors;
}

function checkRule(value: unknown, rule: ValidationRule): string | null {
  const custom = rule.message;
  const param = rule.param;

  if (rule.type === "required") {
    if (value == null || value === "" || (Array.isArray(value) && value.length === 0)) {
      return custom ?? "This field is required.";
    }
    return null;
  }

  // Skip further checks if value is absent
  if (value == null || value === "") return null;

  switch (rule.type) {
    case "min":
      if (typeof value === "number" && value < (param as number)) {
        return custom ?? `Must be at least ${param}.`;
      }
      break;
    case "max":
      if (typeof value === "number" && value > (param as number)) {
        return custom ?? `Must be at most ${param}.`;
      }
      break;
    case "min_length":
      if (typeof value === "string" && value.length < (param as number)) {
        return custom ?? `Must be at least ${param} characters.`;
      }
      break;
    case "max_length":
      if (typeof value === "string" && value.length > (param as number)) {
        return custom ?? `Must be at most ${param} characters.`;
      }
      break;
    case "pattern":
      if (typeof value === "string" && !new RegExp(param as string).test(value)) {
        return custom ?? `Must match pattern ${param}.`;
      }
      break;
    case "one_of": {
      const allowed = (param as string[]) ?? [];
      if (!allowed.includes(value as string)) {
        return custom ?? `Must be one of: ${allowed.join(", ")}.`;
      }
      break;
    }
  }

  return null;
}
