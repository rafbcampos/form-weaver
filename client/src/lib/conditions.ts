import type { Condition } from "../types/schema";
import { getByPath } from "./bindings";

function evaluateCondition(condition: Condition, data: Record<string, unknown>): boolean {
  const value = getByPath(data, condition.field);
  const expected = condition.value;
  const op = condition.op;

  if (op === "exists") return value != null;
  if (op === "not_exists") return value == null;

  if (value == null) return false;

  switch (op) {
    case "eq":
      return value === expected;
    case "neq":
      return value !== expected;
    case "in":
      return Array.isArray(expected) && expected.includes(value);
    case "not_in":
      return Array.isArray(expected) && !expected.includes(value);
    case "gt":
      return (value as number) > (expected as number);
    case "lt":
      return (value as number) < (expected as number);
    case "gte":
      return (value as number) >= (expected as number);
    case "lte":
      return (value as number) <= (expected as number);
    default:
      return false;
  }
}

/**
 * AND logic: all conditions must pass. Empty list → true.
 */
export function evaluateConditions(
  conditions: Condition[],
  data: Record<string, unknown>,
): boolean {
  return conditions.every((c) => evaluateCondition(c, data));
}
