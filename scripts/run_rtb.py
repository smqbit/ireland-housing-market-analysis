import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rtbi_clean_transform import clean_rtb_national, clean_rtb_county, load_rtb_national_xlsxs, load_rtb_county_xlsxs
from loader import get_conn, apply_schema, load_rtb_national, load_rtb_county

conn = get_conn()
apply_schema(conn)
cleaned_national = load_rtb_national_xlsxs(PROJECT_ROOT / "datasets" / "rtb" / "RTBRIQ325-Figure-1.xlsx")
inserted = load_rtb_national(conn, cleaned_national)

cleaned_county = load_rtb_county_xlsxs(PROJECT_ROOT / "datasets" / "rtb" / "RTBRIQ325-Figure-3.xlsx")
inserted += load_rtb_county(conn, cleaned_county)

print(f"Done. {inserted:,} rows inserted.")
conn.close()
