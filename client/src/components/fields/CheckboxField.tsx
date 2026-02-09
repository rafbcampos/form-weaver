import type { CheckboxElement } from "../../types/ui-blocks";

interface CheckboxFieldProps {
  element: CheckboxElement;
  value: boolean;
  onChange: (value: boolean) => void;
  errors: string[];
}

export function CheckboxField({ element, value, onChange, errors }: CheckboxFieldProps) {
  return (
    <div className="mb-3">
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => onChange(e.target.checked)}
          className="rounded text-blue-600 focus:ring-blue-500"
        />
        <span className="font-medium text-gray-700">{element.label}</span>
      </label>
      {errors.map((err, i) => (
        <p key={i} className="mt-1 text-xs text-red-600">
          {err}
        </p>
      ))}
    </div>
  );
}
