import type { InputElement } from "../../types/ui-blocks";

interface NumberFieldProps {
  element: InputElement;
  value: number | "";
  onChange: (value: number | "") => void;
  errors: string[];
}

export function NumberField({ element, value, onChange, errors }: NumberFieldProps) {
  const step = element.type === "float" ? "any" : "1";

  return (
    <div className="mb-3">
      <label className="block text-sm font-medium text-gray-700 mb-1">{element.label}</label>
      <input
        type="number"
        step={step}
        value={value}
        placeholder={element.placeholder ?? ""}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === "") {
            onChange("");
          } else {
            onChange(element.type === "float" ? parseFloat(raw) : parseInt(raw, 10));
          }
        }}
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
