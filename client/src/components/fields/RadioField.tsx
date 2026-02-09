import type { RadioElement } from "../../types/ui-blocks";

interface RadioFieldProps {
  element: RadioElement;
  value: string;
  onChange: (value: string) => void;
  errors: string[];
}

export function RadioField({ element, value, onChange, errors }: RadioFieldProps) {
  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">{element.label}</label>
      <div className="space-y-1">
        {element.options.map((opt) => (
          <label key={opt.value} className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name={element.binding}
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              className="text-blue-600 focus:ring-blue-500"
            />
            {opt.label}
          </label>
        ))}
      </div>
      {errors.map((err, i) => (
        <p key={i} className="mt-1 text-xs text-red-600">
          {err}
        </p>
      ))}
    </div>
  );
}
