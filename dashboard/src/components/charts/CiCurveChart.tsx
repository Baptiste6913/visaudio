import { useMemo } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Trajectory } from "../../types";
import { fmtKEur } from "../../utils/format";

export interface CiCurveChartProps {
  baseline: Trajectory;
  intervention: Trajectory;
  title?: string;
}

interface ChartRow {
  month: number;
  baseline: number;
  intervention: number;
  ci_lower: number;
  ci_upper: number;
}

function buildRows(
  baseline: Trajectory,
  intervention: Trajectory
): ChartRow[] {
  return baseline.months.map((m, i) => ({
    month: m,
    baseline: baseline.ca_mean[i] ?? 0,
    intervention: intervention.ca_mean[i] ?? 0,
    ci_lower: intervention.ca_lower[i] ?? 0,
    ci_upper: intervention.ca_upper[i] ?? 0,
  }));
}

export default function CiCurveChart({
  baseline,
  intervention,
  title,
}: CiCurveChartProps) {
  const rows = useMemo(
    () => buildRows(baseline, intervention),
    [baseline, intervention]
  );

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-[400px] text-sm text-gray-400">
        Aucune donnée disponible.
      </div>
    );
  }

  return (
    <div>
      {title && (
        <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={rows}
          margin={{ top: 8, right: 16, left: 16, bottom: 4 }}
          aria-label={title ?? "Courbe de trajectoire CA"}
        >
          <XAxis
            dataKey="month"
            label={{ value: "Mois", position: "insideBottomRight", offset: -4, fontSize: 11 }}
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmtKEur}
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={72}
          />
          <Tooltip
            formatter={(v: number | string, name: string) => {
              const labels: Record<string, string> = {
                baseline: "Baseline",
                intervention: "Intervention",
                ci_lower: "IC bas",
                ci_upper: "IC haut",
              };
              return [fmtKEur(Number(v)), labels[name] ?? name];
            }}
            cursor={{ stroke: "#e5e7eb" }}
          />
          <Legend
            formatter={(value) => {
              const labels: Record<string, string> = {
                baseline: "Baseline",
                intervention: "Intervention",
                ci_lower: "",
                ci_upper: "",
              };
              return (
                <span className="text-xs text-gray-600">
                  {labels[value] ?? value}
                </span>
              );
            }}
          />

          {/* CI band for intervention */}
          <Area
            dataKey="ci_upper"
            stroke="none"
            fill="#1d4ed8"
            fillOpacity={0.15}
            legendType="none"
            activeDot={false}
            isAnimationActive={false}
          />
          <Area
            dataKey="ci_lower"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
            legendType="none"
            activeDot={false}
            isAnimationActive={false}
          />

          <Line
            type="monotone"
            dataKey="baseline"
            stroke="#9ca3af"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            name="baseline"
          />
          <Line
            type="monotone"
            dataKey="intervention"
            stroke="#1d4ed8"
            strokeWidth={2}
            dot={false}
            name="intervention"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
