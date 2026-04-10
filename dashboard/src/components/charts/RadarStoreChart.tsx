import type { TooltipProps } from "recharts";
import type {
  ValueType,
  NameType,
} from "recharts/types/component/DefaultTooltipContent";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface RadarDimension {
  dimension: string;
  store: number;
  network: number;
}

export interface RadarStoreChartProps {
  storeData: RadarDimension[];
}

function RadarTooltip({
  active,
  payload,
  label,
}: TooltipProps<ValueType, NameType>) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-xs">
      <p className="font-semibold text-gray-800 mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey as string} className="text-gray-600">
          <span
            className="inline-block w-2 h-2 rounded-full mr-1.5"
            style={{ backgroundColor: entry.color }}
          />
          {entry.name} :{" "}
          {typeof entry.value === "number" ? entry.value.toFixed(1) : "—"}
        </p>
      ))}
    </div>
  );
}

export default function RadarStoreChart({ storeData }: RadarStoreChartProps) {
  if (storeData.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-sm text-gray-400">
        Aucune donnée disponible.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart
        data={storeData}
        margin={{ top: 8, right: 24, bottom: 8, left: 24 }}
        aria-label="Performance du magasin vs moyenne réseau"
      >
        <title>Performance magasin vs réseau</title>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fontSize: 11, fill: "#6b7280" }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fontSize: 9, fill: "#9ca3af" }}
          tickCount={4}
        />
        <Radar
          name="Réseau"
          dataKey="network"
          stroke="#9ca3af"
          strokeDasharray="4 3"
          fill="#9ca3af"
          fillOpacity={0.1}
          dot={false}
        />
        <Radar
          name="Magasin"
          dataKey="store"
          stroke="#1d4ed8"
          fill="#1d4ed8"
          fillOpacity={0.3}
          dot={false}
        />
        <Tooltip content={<RadarTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span className="text-xs text-gray-600">{value}</span>
          )}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
