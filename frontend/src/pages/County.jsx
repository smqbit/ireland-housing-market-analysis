import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getCountyHistory } from "../api/client";
import TrendChart from "../components/TrendChart";

export default function County() {
  const { name } = useParams();
  const [data, setData] = useState([]);

  useEffect(() => {
    getCountyHistory(name).then((res) => {
      const clean = res.data.map((d) => ({
        ...d,
        median_price: Number(d.median_price),
        real_median_price: Number(d.real_median_price),
      }));

      setData(clean);
    });
  }, [name]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">{name}</h1>

      <div className="bg-white p-4 rounded-xl">
        <h2 className="mb-2 font-medium">Price Trend</h2>

        <TrendChart
          data={data}
          priceKey="median_price"
          realPriceKey="real_median_price"
        />
      </div>
    </div>
  );
}