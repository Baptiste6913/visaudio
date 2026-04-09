import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { fmtKEur } from "../../utils/format";

export interface WaterfallChartProps {
  data: { name: string; value: number }[];
}

const POSITIVE_COLOR = "#22c55e";
const NEGATIVE_COLOR = "#ef4444";

export default function WaterfallChart({ data }: WaterfallChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-sm text-gray-400">
        Aucune donnée disponible.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 16, left: 16, bottom: 4 }}
        aria-label="Graphique en cascade"
      >
        <XAxis
          dataKey="name"
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
        <ReferenceLine y={0} stroke="#e5e7eb" />
        <Tooltip
          formatter={(v: number | string) => [fmtKEur(Number(v)), "Variation"]}
          cursor={{ fill: "rgba(0,0,0,0.04)" }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.value >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
