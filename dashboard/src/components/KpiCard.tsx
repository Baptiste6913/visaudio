export interface KpiCardProps {
  label: string;
  value: string;
  subtitle?: string;
  delta?: number;
}

export default function KpiCard({ label, value, subtitle, delta }: KpiCardProps) {
  const hasPositiveDelta = delta !== undefined && delta > 0;
  const hasNegativeDelta = delta !== undefined && delta < 0;

  return (
    <div className="animate-slide-up bg-gradient-to-b from-white to-gray-50/50 rounded-lg shadow-sm border border-gray-100 border-l-4 border-l-brand-500 p-4 flex flex-col gap-1 min-w-0 hover:shadow-md transition-all duration-200">
      <span className="text-sm text-gray-500 truncate">{label}</span>
      <span className="text-2xl font-bold text-gray-900 leading-tight">{value}</span>
      {subtitle && (
        <span className="text-xs text-gray-400 truncate">{subtitle}</span>
      )}
      {delta !== undefined && (
        <span
          className={[
            "text-sm font-medium",
            hasPositiveDelta ? "text-green-600" : "",
            hasNegativeDelta ? "text-red-600" : "",
            delta === 0 ? "text-gray-400" : "",
          ].join(" ")}
        >
          {hasPositiveDelta && "↑ +"}
          {hasNegativeDelta && "↓ "}
          {delta === 0 && "— "}
          {Math.abs(delta).toLocaleString("fr-FR", { maximumFractionDigits: 1 })}
        </span>
      )}
    </div>
  );
}
