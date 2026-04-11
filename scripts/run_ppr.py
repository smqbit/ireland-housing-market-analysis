import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from ppr_clean_transform import load_ppr_csvs, clean_ppr
from loader import get_conn, apply_schema, load_ppr

PPR_DIR = PROJECT_ROOT / "datasets" / "ppr"

conn = get_conn()
apply_schema(conn)

raw = load_ppr_csvs(PPR_DIR)
cleaned = clean_ppr(raw)
inserted = load_ppr(conn, cleaned)

print(f"Done. {inserted:,} rows inserted.")
conn.close()
