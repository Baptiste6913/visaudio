import { useRole } from "../utils/roles";
import type { Role } from "../types";

const ROLES: { value: Role; label: string }[] = [
  { value: "direction", label: "Direction" },
  { value: "manager", label: "Manager" },
];

export default function RoleSwitcher() {
  const { role, setRole, setStore } = useRole();

  const handleSwitch = (next: Role) => {
    setRole(next);
    if (next === "manager") {
      setStore("Avranches");
    }
  };

  return (
    <div className="flex items-center border border-gray-200 rounded overflow-hidden">
      {ROLES.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => handleSwitch(value)}
          className={[
            "px-3 py-1.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600",
            role === value
              ? "bg-brand-600 text-white"
              : "bg-white text-gray-600 border-r border-gray-200 last:border-r-0 hover:bg-gray-50",
          ].join(" ")}
          aria-pressed={role === value}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
