import type { FormBlock as FormBlockType } from "../types/ui-blocks";
import { useFormBlock } from "../hooks/useFormBlock";
import { FieldRenderer } from "./fields/FieldRenderer";

interface FormBlockProps {
  block: FormBlockType;
  onSubmit: (data: Record<string, unknown>) => void;
  serverErrors: Record<string, string[]>;
  disabled: boolean;
}

export function FormBlock({ block, onSubmit, serverErrors, disabled }: FormBlockProps) {
  const { formData, setField, errors, getFieldValue } = useFormBlock(block);

  const combinedErrors = { ...errors, ...serverErrors };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
    >
      {block.elements.map((element) => (
        <FieldRenderer
          key={element.binding}
          element={element}
          value={getFieldValue(element.binding)}
          onChange={(v) => setField(element.binding, v)}
          errors={combinedErrors[element.binding] ?? []}
          allErrors={combinedErrors}
        />
      ))}
      <button
        type="submit"
        disabled={disabled}
        className="mt-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {disabled ? "Submitting..." : "Continue"}
      </button>
    </form>
  );
}
