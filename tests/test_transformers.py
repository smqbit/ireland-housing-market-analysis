import unittest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from cpi_clean_transform import clean_cpi
from housing_combined_clean_transform import derive_rental_yield, derive_real_price
from ppr_clean_transform import aggregate_ppr, clean_ppr
from rtbi_clean_transform import clean_rtb_national


def make_ppr():
    return pd.DataFrame({
        "date_of_sale":          ["1 01 2021", "15 06 2021", "1 01 2021"],
        "address":               ["1 Main St", "2 Main St", "3 Main St"],
        "county":                ["Dublin", "Cork", "Dublin"],
        "eircode":               ["D01 AB12", None, "D02 CD34"],
        "price_eur":             ["295000.00", "250000.00", "1000.00"],
        "not_full_market_price": ["No", "No", "Yes"],
        "vat_exclusive":         ["No", "No", "No"],
        "property_description":  [
            "Second-Hand Dwelling house /Apartment",
            "New Dwelling house /Apartment",
            "Second-Hand Dwelling house /Apartment",
        ],
        "size_description": [None, None, None],
        "year": ["2021", "2021", "2021"],
    })


def make_cpi_raw():
    return pd.DataFrame({
        "Statistic Label": [
            "Consumer Price Index (Base Month December 2016 = 100)",
            "Consumer Price Index (Base Month December 2016 = 100)",
            "Consumer Price Index (Base Month November 1996 = 100)",
            "Percentage change over 12 months for Consumer Price Index",
        ],
        "TLIST(M1)": [201001, 201012, 201001, 201001],
        "Month":     [201001, 201012, 201001, 201001],
        "Commodity Group": ["All Items"] * 4,
        "VALUE": [94.7, 95.2, 263.4, -0.2],
    })


class TestCleanPPR(unittest.TestCase):

    def setUp(self):
        self.cleaned = clean_ppr(make_ppr())

    def test_non_market_filtered(self):
        self.assertTrue(self.cleaned["is_full_market"].all())

    def test_below_min_price_filtered(self):
        self.assertTrue((self.cleaned["price_eur"] >= 5_000).all())

    def test_date_parsed(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.cleaned["date_of_sale"]))

    def test_quarter_format(self):
        self.assertTrue(self.cleaned["quarter"].str.match(r"^\d{4}Q[1-4]$").all())

    def test_is_new_flag(self):
        cork = self.cleaned[self.cleaned["county"] == "Cork"]
        self.assertTrue(cork["is_new"].iloc[0])

    def test_row_count(self):
        # row 3: not full market (Yes), filtered
        # row 1 (price 1000) is also not full market so filtered by that first
        # rows 1 and 2 are full market and above min price, so both included
        self.assertEqual(len(self.cleaned), 2)


class TestCleanRTBNational(unittest.TestCase):

    def test_filters_header_and_footer(self):
        df = pd.DataFrame({0: ["Period", "Q3 2007", "Q4 2007", "footer"], 1: ["Rent", 964.08, 992.35, None]})
        result = clean_rtb_national(df)
        self.assertEqual(len(result), 2)

    def test_quarter_format(self):
        df = pd.DataFrame({0: ["Period", "Q3 2007"], 1: ["Rent", 964.08]})
        result = clean_rtb_national(df)
        self.assertEqual(result["quarter"].iloc[0], "2007Q3")

    def test_rent_rounded(self):
        df = pd.DataFrame({0: ["Period", "Q3 2007"], 1: ["Rent", 964.082635]})
        result = clean_rtb_national(df)
        self.assertEqual(result["rent_eur"].iloc[0], 964.08)


class TestCleanCPI(unittest.TestCase):

    def setUp(self):
        self.result = clean_cpi(make_cpi_raw())

    def test_filters_to_dec2016_base_and_all_items(self):
        self.assertEqual(len(self.result), 2)

    def test_year_month_are_integers(self):
        self.assertEqual(self.result["year"].iloc[0], 2010)
        self.assertEqual(self.result["month"].iloc[0], 1)

    def test_only_2010_onwards(self):
        self.assertTrue((self.result["year"] >= 2010).all())


class TestAggregatePPR(unittest.TestCase):

    def setUp(self):
        raw = make_ppr()
        extra = raw.iloc[[0]].copy()
        extra["price_eur"] = "305000.00"
        raw = pd.concat([raw, extra], ignore_index=True)
        self.agg = aggregate_ppr(clean_ppr(raw))

    def test_required_columns(self):
        for col in ["county", "year", "quarter", "median_price", "transaction_count", "pct_new"]:
            self.assertIn(col, self.agg.columns)

    def test_transaction_count(self):
        dublin = self.agg[self.agg["county"] == "Dublin"]
        self.assertEqual(dublin["transaction_count"].iloc[0], 2)

    def test_median_price(self):
        dublin = self.agg[self.agg["county"] == "Dublin"]
        self.assertEqual(dublin["median_price"].iloc[0], 300000.0)


class TestDeriveRentalYield(unittest.TestCase):

    def setUp(self):
        ppr_agg = pd.DataFrame({
            "county": ["Dublin", "Cork"], "year": [2025, 2025],
            "quarter": ["2025Q3", "2025Q3"],
            "median_price": [490000.0, 325000.0], "mean_price": [500000.0, 330000.0],
            "min_price": [300000.0, 200000.0], "max_price": [800000.0, 500000.0],
            "transaction_count": [100, 50], "pct_new": [10.0, 8.0],
        })
        rtb_national = pd.DataFrame({
            "quarter": ["2025Q3"], "new_rent_eur": [1776.0],
            "existing_rent_eur": [1494.0], "rent_gap_eur": [282.0], "rent_gap_pct": [18.88],
        })
        rtb_county = pd.DataFrame({
            "county": ["Dublin"], "new_rent_eur": [2307.0],
            "existing_rent_eur": [1944.0], "rent_gap_eur": [363.0], "rent_gap_pct": [18.7],
        })
        self.result = derive_rental_yield(ppr_agg, rtb_national, rtb_county)

    def test_dublin_uses_county_rent(self):
        dublin = self.result[self.result["county"] == "Dublin"]
        self.assertEqual(dublin["rent_source"].iloc[0], "county")
        self.assertEqual(dublin["monthly_rent"].iloc[0], 2307.0)

    def test_cork_falls_back_to_national(self):
        cork = self.result[self.result["county"] == "Cork"]
        self.assertEqual(cork["rent_source"].iloc[0], "national")
        self.assertEqual(cork["monthly_rent"].iloc[0], 1776.0)

    def test_yield_calculation(self):
        dublin = self.result[self.result["county"] == "Dublin"]
        expected = round((2307.0 * 12) / 490000.0 * 100, 2)
        self.assertAlmostEqual(dublin["rental_yield_pct"].iloc[0], expected, places=2)


class TestDeriveRealPrice(unittest.TestCase):

    def test_real_price(self):
        housing = pd.DataFrame({
            "county": ["Dublin"], "year": [2021], "quarter": ["2021Q1"],
            "median_price": [490000.0],
        })
        cpi = pd.DataFrame({"year": [2021], "month": [12], "index_value": [104.5]})
        result = derive_real_price(housing, cpi)
        self.assertEqual(result["real_median_price"].iloc[0], round(490000.0 / 1.045, 0))

    def test_missing_cpi_gives_null(self):
        housing = pd.DataFrame({
            "county": ["Dublin"], "year": [2005], "quarter": ["2005Q1"],
            "median_price": [300000.0],
        })
        cpi = pd.DataFrame({"year": [2021], "month": [12], "index_value": [104.5]})
        result = derive_real_price(housing, cpi)
        self.assertTrue(pd.isna(result["real_median_price"].iloc[0]))


if __name__ == "__main__":
    unittest.main(verbosity=2)