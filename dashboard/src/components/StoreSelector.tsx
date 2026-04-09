import { STORE_NAMES } from "../types";

export interface StoreSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

export default function StoreSelector({ value, onChange }: StoreSelectorProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-700 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-600 focus:border-brand-600"
      aria-label="Sélectionner un magasin"
    >
      {STORE_NAMES.map((name) => (
        <option key={name} value={name}>
          {name}
        </option>
      ))}
    </select>
  );
}
