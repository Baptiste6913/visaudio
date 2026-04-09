import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { fmtKEur } from "../../utils/format";

export interface RevenueBarChartProps {
  data: { name: string; value: number }[];
  label?: string;
  color?: string;
}

const DEFAULT_COLOR = "#1d4ed8"; // brand-600

export default function RevenueBarChart({
  data,
  label,
  color = DEFAULT_COLOR,
}: RevenueBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-sm text-gray-400">
        Aucune donnée disponible.
      </div>
    );
  }

  return (
    <div>
      {label && (
        <p className="text-sm font-medium text-gray-600 mb-2">{label}</p>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          layout="horizontal"
          margin={{ top: 4, right: 16, left: 16, bottom: 4 }}
          aria-label={label ?? "Graphique à barres"}
        >
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12 }}
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
            formatter={(v: number | string) => [fmtKEur(Number(v)), label ?? "CA"]}
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
            {data.map((_, i) => (
              <Cell key={i} fill={color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
