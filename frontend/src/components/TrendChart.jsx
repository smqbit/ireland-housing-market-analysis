import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function TrendChart({
  data,
  priceKey,
  realPriceKey,
}) {
  if (!data || data.length === 0) {
    return <p className="text-gray-500">No data available</p>;
  }

  return (
    <div className="w-full h-72">
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis dataKey="quarter" />
          <YAxis />
          <Tooltip />
          <Legend />

          <Line
            type="monotone"
            dataKey={priceKey}
            name="Median Price"
            stroke="#2563eb"
            strokeWidth={2}
          />

          <Line
            type="monotone"
            dataKey={realPriceKey}
            name="Real Price"
            stroke="#16a34a"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}