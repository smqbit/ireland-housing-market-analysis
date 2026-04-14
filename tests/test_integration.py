# Integration test — API 

import unittest

import requests

BASE = "http://localhost:8080/api"


def get(path, params=None):
    resp = requests.get(f"{BASE}{path}", params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


class TestNationalTrend(unittest.TestCase):
    """
    Frontend: getNationalTrend() → GET /api/national/trend
    Used by: Home.jsx TrendChart, YieldChart
    """

    def setUp(self):
        self.data = get("/national/trend")

    def test_required_fields(self):
        row = self.data[0]
        for field in ["quarter", "national_median_price", "national_real_price", "total_transactions",
                      "avg_rental_yield"]:
            self.assertIn(field, row)

    def test_prices_are_numbers(self):
        row = self.data[0]
        if row["national_median_price"] is not None:
            self.assertIsInstance(row["national_median_price"], (int, float))
        if row["national_real_price"] is not None:
            self.assertIsInstance(row["national_real_price"], (int, float))

    def test_quarter_format(self):
        # TrendChart uses quarter as XAxis key
        for row in self.data:
            self.assertRegex(row["quarter"], r"^\d{4}Q[1-4]$")

    def test_from_to_filter(self):
        filtered = get("/national/trend", {"from": "2021Q1", "to": "2022Q4"})
        for row in filtered:
            self.assertGreaterEqual(row["quarter"], "2021Q1")
            self.assertLessEqual(row["quarter"], "2022Q4")


class TestCounties(unittest.TestCase):
    """
    Frontend: getCounties() → GET /api/counties
    Used by: Home.jsx CountyList
    """

    def setUp(self):
        self.data = get("/counties")

    def test_required_fields(self):
        # CountyList renders county, median_price, rental_yield_pct
        row = self.data[0]
        for field in ["county", "median_price", "rental_yield_pct"]:
            self.assertIn(field, row)

    def test_median_price_is_number(self):
        # CountyList does Math.round(c.median_price) — must be numeric
        for row in self.data:
            if row["median_price"] is not None:
                self.assertIsInstance(row["median_price"], (int, float))

    def test_yield_is_number(self):
        # CountyList does c.rental_yield_pct?.toFixed(2) — must be numeric
        for row in self.data:
            if row["rental_yield_pct"] is not None:
                self.assertIsInstance(row["rental_yield_pct"], (int, float))

    def test_26_counties(self):
        self.assertEqual(len(self.data), 26)


class TestCountyHistory(unittest.TestCase):
    """
    Frontend: getCountyHistory(name) → GET /api/county/<name>/history
    Used by: County.jsx, Home.jsx when county selected
    """

    def setUp(self):
        self.data = get("/county/Dublin/history")

    def test_required_fields(self):
        row = self.data[0]
        for field in ["county", "quarter", "median_price", "real_median_price"]:
            self.assertIn(field, row)

    def test_ordered_by_quarter(self):
        quarters = [r["quarter"] for r in self.data]
        self.assertEqual(quarters, sorted(quarters))

    def test_case_insensitive(self):
        # API should handle lowercase county name from URL params
        lower = get("/county/dublin/history")
        self.assertGreater(len(lower), 0)

    def test_from_filter(self):
        filtered = get("/county/Dublin/history", {"from": "2021Q1"})
        for row in filtered:
            self.assertGreaterEqual(row["quarter"], "2021Q1")

    def test_unknown_county_returns_404(self):
        resp = requests.get(f"{BASE}/county/SomeEntity/history", timeout=5)
        self.assertEqual(resp.status_code, 404)


class TestFilters(unittest.TestCase):
    """
    Frontend: getFilters() → GET /api/filters
    Used by: Home.jsx — filters.counties.slice(0, 10)
    """

    def setUp(self):
        self.data = get("/filters")

    def test_counties_is_list_of_strings(self):
        self.assertIsInstance(self.data["counties"], list)
        for c in self.data["counties"]:
            self.assertIsInstance(c, str)

    def test_quarters_sorted(self):
        quarters = self.data["quarters"]
        self.assertEqual(quarters, sorted(quarters))

    def test_sliceable(self):
        # Home.jsx does filters.counties.slice(0, 10)
        top10 = self.data["counties"][:10]
        self.assertEqual(len(top10), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
