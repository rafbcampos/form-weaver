/**
 * Parse a binding path like "user.children[0].name" into segments.
 */
function parsePath(path: string): (string | number)[] {
  const parts: (string | number)[] = [];
  let current = "";
  let i = 0;

  while (i < path.length) {
    const ch = path[i]!;
    if (ch === ".") {
      if (current) {
        parts.push(current);
        current = "";
      }
    } else if (ch === "[") {
      if (current) {
        parts.push(current);
        current = "";
      }
      const j = path.indexOf("]", i);
      parts.push(parseInt(path.slice(i + 1, j), 10));
      i = j;
    } else {
      current += ch;
    }
    i++;
  }

  if (current) {
    parts.push(current);
  }

  return parts;
}

/**
 * Resolve a value at a dot-notation path in an object.
 */
export function getByPath(obj: Record<string, unknown>, path: string): unknown {
  const parts = parsePath(path);
  let current: unknown = obj;

  for (const part of parts) {
    if (current == null) return undefined;
    if (typeof part === "number") {
      if (!Array.isArray(current)) return undefined;
      current = current[part];
    } else {
      if (typeof current !== "object") return undefined;
      current = (current as Record<string, unknown>)[part];
    }
  }

  return current;
}

/**
 * Immutably set a value at a dot-notation path, returning a new object.
 */
export function setByPath(
  obj: Record<string, unknown>,
  path: string,
  value: unknown,
): Record<string, unknown> {
  const parts = parsePath(path);
  if (parts.length === 0) return obj;

  const root = structuredClone(obj) as Record<string, unknown>;
  let current: unknown = root;

  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i]!;
    const nextPart = parts[i + 1]!;

    if (typeof part === "number") {
      const arr = current as unknown[];
      while (arr.length <= part) {
        arr.push(typeof nextPart === "number" ? [] : {});
      }
      current = arr[part];
    } else {
      const rec = current as Record<string, unknown>;
      if (rec[part] == null) {
        rec[part] = typeof nextPart === "number" ? [] : {};
      }
      current = rec[part];
    }
  }

  const last = parts[parts.length - 1]!;
  if (typeof last === "number") {
    const arr = current as unknown[];
    while (arr.length <= last) {
      arr.push(undefined);
    }
    arr[last] = value;
  } else {
    (current as Record<string, unknown>)[last] = value;
  }

  return root;
}

/**
 * Convert a flat binding map to a nested object.
 * { "user.name": "John", "user.age": 25 } → { user: { name: "John", age: 25 } }
 */
export function expandBindings(flat: Record<string, unknown>): Record<string, unknown> {
  let result: Record<string, unknown> = {};
  for (const [path, value] of Object.entries(flat)) {
    result = setByPath(result, path, value);
  }
  return result;
}
