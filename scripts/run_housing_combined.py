import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from ppr_clean_transform import load_ppr_csvs, clean_ppr, aggregate_ppr
from housing_combined_clean_transform import derive_rental_yield, derive_real_price
from loader import get_conn, load_housing_combined, apply_schema

PPR_DIR = PROJECT_ROOT / "datasets" / "ppr"

raw = load_ppr_csvs(PPR_DIR)
cleaned = clean_ppr(raw)
ppr_agg = aggregate_ppr(cleaned)

conn = get_conn()
apply_schema(conn)

with conn.cursor() as cur:
    cur.execute("SELECT quarter, new_rent_eur, existing_rent_eur, rent_gap_eur, rent_gap_pct FROM rtb_national")
    rtb_national = pd.DataFrame(cur.fetchall(), columns=["quarter", "new_rent_eur", "existing_rent_eur", "rent_gap_eur",
                                                         "rent_gap_pct"])

    cur.execute("SELECT county, new_rent_eur, existing_rent_eur, rent_gap_eur, rent_gap_pct FROM rtb_county")
    rtb_county = pd.DataFrame(cur.fetchall(),
                              columns=["county", "new_rent_eur", "existing_rent_eur", "rent_gap_eur", "rent_gap_pct"])

    cur.execute("SELECT year, month, index_value FROM cso_cpi ORDER BY year, month")
    cpi = pd.DataFrame(cur.fetchall(), columns=["year", "month", "index_value"])

numeric_cols = ["new_rent_eur", "existing_rent_eur", "rent_gap_eur", "rent_gap_pct"]
for df in [rtb_national, rtb_county]:
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

cpi["index_value"] = pd.to_numeric(cpi["index_value"], errors="coerce")

combined = derive_rental_yield(ppr_agg, rtb_national, rtb_county)
combined = derive_real_price(combined, cpi)

inserted = load_housing_combined(conn, combined)
conn.close()

print(f"Done. {inserted} rows in housing_combined.")
