import { useMemo } from "react";
import type { TooltipProps } from "recharts";
import type { ValueType, NameType } from "recharts/types/component/DefaultTooltipContent";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface MixPieChartProps {
  data: { name: string; value: number }[];
  title?: string;
}

// Gamme palette — color-blind-safe ordered
const GAMME_COLORS: Record<string, string> = {
  ESSENTIEL: "#94a3b8",
  CONFORT: "#60a5fa",
  PREMIUM: "#2563eb",
  PRESTIGE: "#1e3a8a",
};

const FALLBACK_COLORS = ["#94a3b8", "#60a5fa", "#2563eb", "#1e3a8a"];

function colorForName(name: string, index: number): string {
  return GAMME_COLORS[name.toUpperCase()] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

function makePieTooltip(total: number) {
  return function PieTooltip({ active, payload }: TooltipProps<ValueType, NameType>) {
    if (!active || !payload || payload.length === 0) return null;
    const entry = payload[0];
    const value = typeof entry.value === "number" ? entry.value : 0;
    const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
    return (
      <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-1.5 text-xs">
        <p className="font-medium text-gray-800">{entry.name}</p>
        <p className="text-gray-600">{pct} %</p>
      </div>
    );
  };
}

export default function MixPieChart({ data, title }: MixPieChartProps) {
  const total = useMemo(
    () => data.reduce((acc, d) => acc + d.value, 0),
    [data]
  );

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[260px] text-sm text-gray-400">
        Aucune donnée disponible.
      </div>
    );
  }

  return (
    <div>
      {title && (
        <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={260}>
        <PieChart aria-label={title ?? "Répartition gammes"}>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={2}
          >
            {data.map((entry, i) => (
              <Cell key={entry.name} fill={colorForName(entry.name, i)} />
            ))}
          </Pie>
          <Tooltip content={makePieTooltip(total)} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => (
              <span className="text-xs text-gray-600">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
