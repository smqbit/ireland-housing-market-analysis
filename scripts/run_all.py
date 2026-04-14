import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    "scripts/run_ppr.py",
    "scripts/run_rtb.py",
    "scripts/run_cpi.py",
    "scripts/run_ppr_aggregated.py",
    "scripts/run_housing_combined.py",
]

for script in STEPS:
    logger.info("Running %s ...", script)
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script)],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        logger.error("%s failed — stopping pipeline", script)
        sys.exit(1)

logger.info("Pipeline complete.")