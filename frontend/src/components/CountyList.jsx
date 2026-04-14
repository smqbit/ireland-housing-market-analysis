import { useNavigate } from "react-router-dom";

export default function CountyList({ data }) {
  const navigate = useNavigate();

  return (
    <div className="space-y-3">
      {data.map((c) => (
        <div
          key={c.county}
          onClick={() => navigate(`/county/${c.county}`)}
          className="p-3 bg-gray-100 rounded-xl flex justify-between cursor-pointer active:scale-95"
        >
          <span className="font-medium">{c.county}</span>

          <div className="text-right">
            <div className="text-sm font-semibold">
              €{Math.round(c.median_price).toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">
              {c.rental_yield_pct?.toFixed(2)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}