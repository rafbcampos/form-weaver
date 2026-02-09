import { useCallback, useState } from "react";
import type { FormBlock } from "../types/ui-blocks";
import { getByPath, setByPath } from "../lib/bindings";

interface UseFormBlockReturn {
  formData: Record<string, unknown>;
  setField: (binding: string, value: unknown) => void;
  errors: Record<string, string[]>;
  setErrors: (errors: Record<string, string[]>) => void;
  getFieldValue: (binding: string) => unknown;
  addArrayItem: (binding: string, empty: Record<string, unknown>) => void;
  removeArrayItem: (binding: string, index: number) => void;
  reset: () => void;
}

function buildInitialData(block: FormBlock): Record<string, unknown> {
  const data: Record<string, unknown> = {};
  for (const element of block.elements) {
    if (element.kind === "checkbox") {
      data[element.binding] = false;
    } else if (element.kind === "array") {
      data[element.binding] = [];
    } else {
      data[element.binding] = "";
    }
  }
  return data;
}

export function useFormBlock(block: FormBlock): UseFormBlockReturn {
  const [formData, setFormData] = useState<Record<string, unknown>>(() => buildInitialData(block));
  const [errors, setErrors] = useState<Record<string, string[]>>({});

  const setField = useCallback((binding: string, value: unknown) => {
    setFormData((prev) => setByPath(prev, binding, value));
    setErrors((prev) => {
      if (binding in prev) {
        const next = { ...prev };
        delete next[binding];
        return next;
      }
      return prev;
    });
  }, []);

  const getFieldValue = useCallback((binding: string) => getByPath(formData, binding), [formData]);

  const addArrayItem = useCallback((binding: string, empty: Record<string, unknown>) => {
    setFormData((prev) => {
      const current = (getByPath(prev, binding) as unknown[]) ?? [];
      return setByPath(prev, binding, [...current, empty]);
    });
  }, []);

  const removeArrayItem = useCallback((binding: string, index: number) => {
    setFormData((prev) => {
      const current = (getByPath(prev, binding) as unknown[]) ?? [];
      return setByPath(
        prev,
        binding,
        current.filter((_, i) => i !== index),
      );
    });
  }, []);

  const reset = useCallback(() => {
    setFormData(buildInitialData(block));
    setErrors({});
  }, [block]);

  return {
    formData,
    setField,
    errors,
    setErrors,
    getFieldValue,
    addArrayItem,
    removeArrayItem,
    reset,
  };
}
