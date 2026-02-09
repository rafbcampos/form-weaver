import type { TextareaElement } from "../../types/ui-blocks";

interface TextareaFieldProps {
  element: TextareaElement;
  value: string;
  onChange: (value: string) => void;
  errors: string[];
}

export function TextareaField({ element, value, onChange, errors }: TextareaFieldProps) {
  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">{element.label}</label>
      <textarea
        value={value}
        placeholder={element.placeholder ?? ""}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          errors.length > 0 ? "border-red-400 focus:ring-red-500" : "border-gray-300"
        }`}
      />
      {errors.map((err, i) => (
        <p key={i} className="mt-1 text-xs text-red-600">
          {err}
        </p>
      ))}
    </div>
  );
}
