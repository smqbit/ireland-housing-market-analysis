import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "pipeline"))

from cpi_download import download_cpi
from cpi_clean_transform import clean_cpi
from loader import get_conn, apply_schema, load_cpi

cpi_path = download_cpi()
raw = pd.read_csv(cpi_path, dtype=str)
cleaned = clean_cpi(raw)

conn = get_conn()
apply_schema(conn)
inserted = load_cpi(conn, cleaned)
conn.close()

print(f"Done. {inserted} CPI rows inserted.")