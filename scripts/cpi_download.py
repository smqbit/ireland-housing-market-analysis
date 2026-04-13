import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSO_DIR = PROJECT_ROOT / "datasets" / "cso"

CPM20_URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/CPM20/CSV/1.0/en"


def download_cpi(out_dir=None):
    if out_dir is None:
        out_dir = CSO_DIR

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "cpi.csv"

    logger.info("Fetching CPM20 from CSO PxStat...")
    resp = requests.get(CPM20_URL, timeout=60)
    resp.raise_for_status()

    out_path.write_bytes(resp.content)
    logger.info("Saved cpi.csv (%d KB)", out_path.stat().st_size // 1024)
    return out_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    path = download_cpi()
    print(f"Downloaded: {path}")