import { useCallback } from "react";
import type { ArrayElement } from "../../types/ui-blocks";
import { FieldRenderer } from "./FieldRenderer";

interface ArrayFieldProps {
  element: ArrayElement;
  items: Record<string, unknown>[];
  onChange: (items: Record<string, unknown>[]) => void;
  errors: Record<string, string[]>;
}

export function ArrayField({ element, items, onChange, errors }: ArrayFieldProps) {
  const addItem = useCallback(() => {
    const empty: Record<string, unknown> = {};
    for (const el of element.item_elements) {
      empty[el.binding] = el.kind === "checkbox" ? false : "";
    }
    onChange([...items, empty]);
  }, [element.item_elements, items, onChange]);

  const removeItem = useCallback(
    (index: number) => {
      onChange(items.filter((_, i) => i !== index));
    },
    [items, onChange],
  );

  const updateItem = useCallback(
    (index: number, field: string, value: unknown) => {
      const updated = items.map((item, i) => (i === index ? { ...item, [field]: value } : item));
      onChange(updated);
    },
    [items, onChange],
  );

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-2">{element.label}</label>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="relative rounded-md border border-gray-200 bg-gray-50 p-3">
            <button
              type="button"
              onClick={() => removeItem(index)}
              className="absolute top-2 right-2 text-gray-400 hover:text-red-500 text-sm"
              aria-label="Remove"
            >
              Remove
            </button>
            {element.item_elements.map((el) => {
              const bindingPath = `${element.binding}[${index}].${el.binding}`;
              const fieldErrors = errors[bindingPath] ?? [];
              return (
                <FieldRenderer
                  key={el.binding}
                  element={el}
                  value={item[el.binding] ?? (el.kind === "checkbox" ? false : "")}
                  onChange={(v) => updateItem(index, el.binding, v)}
                  errors={fieldErrors}
                />
              );
            })}
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={addItem}
        className="mt-2 text-sm text-blue-600 hover:text-blue-800"
      >
        + {element.add_label}
      </button>
    </div>
  );
}
