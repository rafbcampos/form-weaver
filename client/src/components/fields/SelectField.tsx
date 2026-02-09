import type { SelectElement } from "../../types/ui-blocks";

interface SelectFieldProps {
  element: SelectElement;
  value: string;
  onChange: (value: string) => void;
  errors: string[];
}

export function SelectField({ element, value, onChange, errors }: SelectFieldProps) {
  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">{element.label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          errors.length > 0 ? "border-red-400 focus:ring-red-500" : "border-gray-300"
        }`}
      >
        <option value="">Select...</option>
        {element.options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {errors.map((err, i) => (
        <p key={i} className="mt-1 text-xs text-red-600">
          {err}
        </p>
      ))}
    </div>
  );
}
