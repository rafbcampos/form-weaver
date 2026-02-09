import type { InputElement } from "../../types/ui-blocks";

interface TextFieldProps {
  element: InputElement;
  value: string;
  onChange: (value: string) => void;
  errors: string[];
}

export function TextField({ element, value, onChange, errors }: TextFieldProps) {
  const inputType =
    element.type === "integer" || element.type === "float"
      ? "number"
      : element.type === "email"
        ? "email"
        : element.type === "date"
          ? "date"
          : element.type === "phone"
            ? "tel"
            : "text";

  const step = element.type === "float" ? "any" : undefined;

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">{element.label}</label>
      <input
        type={inputType}
        step={step}
        value={value}
        placeholder={element.placeholder ?? ""}
        onChange={(e) => onChange(e.target.value)}
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
