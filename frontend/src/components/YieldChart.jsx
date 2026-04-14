import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function YieldChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500">No data available</p>;
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis dataKey="quarter" />
          <YAxis />
          <Tooltip />

          <Line
            type="monotone"
            dataKey="avg_rental_yield"
            name="Rental Yield %"
            stroke="#f59e0b"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}