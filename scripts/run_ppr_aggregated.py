import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from ppr_clean_transform import load_ppr_csvs, clean_ppr
from ppr_clean_transform import aggregate_ppr
from loader import get_conn, load_ppr_aggregated

PPR_DIR = PROJECT_ROOT / "datasets" / "ppr"
sys.path.insert(0, str(PROJECT_ROOT / "pipeline"))

raw = load_ppr_csvs(PPR_DIR)
cleaned = clean_ppr(raw)
agg = aggregate_ppr(cleaned)

conn = get_conn()
inserted = load_ppr_aggregated(conn, agg)
conn.close()

print(f"Done. {inserted} county/quarter rows inserted.")
