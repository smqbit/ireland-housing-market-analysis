import { useEffect, useState } from "react";
import {
  getNationalTrend,
  getCounties,
  getFilters,
  getCountyHistory,
} from "../api/client";

import Header from "../components/Header";
import Card from "../components/Card";
import TrendChart from "../components/TrendChart";
import YieldChart from "../components/YieldChart";
import CountyList from "../components/CountyList";
import Filters from "../components/Filters";

export default function Home() {
  const [trend, setTrend] = useState([]);
  const [counties, setCounties] = useState([]);
  const [filters, setFilters] = useState([]);
  const [selectedCounty, setSelectedCounty] = useState(null);
  const [countyTrend, setCountyTrend] = useState([]);

  useEffect(() => {
    async function load() {
      const [t, c, f] = await Promise.all([
        getNationalTrend(),
        getCounties(),
        getFilters(),
      ]);

      setTrend(t.data);
      setCounties(c.data);
      setFilters(f.data.counties.slice(0, 10));
    }

    load();
  }, []);

  useEffect(() => {
    if (!selectedCounty) return;

    getCountyHistory(selectedCounty).then((res) => {
      const clean = res.data.map((d) => ({
        ...d,
        median_price: Number(d.median_price),
        real_median_price: Number(d.real_median_price),
      }));

      setCountyTrend(clean);
    });
  }, [selectedCounty]);

  const displayData = selectedCounty ? countyTrend : trend;

  return (
    <div>
      <Header />

      <main className="p-4 space-y-4">
        <Filters
          counties={filters}
          selectedCounty={selectedCounty}
          setSelectedCounty={setSelectedCounty}
        />

        <Card>
          <h2 className="font-semibold mb-2">
            {selectedCounty
              ? `${selectedCounty} Price Trend`
              : "National Price Trend"}
          </h2>

          <TrendChart
            data={displayData}
            priceKey={
              selectedCounty
                ? "median_price"
                : "national_median_price"
            }
            realPriceKey={
              selectedCounty
                ? "real_median_price"
                : "national_real_price"
            }
          />
        </Card>

        {!selectedCounty && (
          <Card>
            <h2 className="font-semibold mb-2">
              Rental Yield Trend
            </h2>
            <YieldChart data={trend} />
          </Card>
        )}

        <Card>
          <h2 className="font-semibold mb-2">
            Counties
          </h2>
          <CountyList data={counties} />
        </Card>
      </main>
    </div>
  );
}