import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RTB_DIR = PROJECT_ROOT / "datasets" / "rtb"
RTB_PAGE_URL = "https://rtb.ie/data-insights/rtb-data-hub/rtb-esri-rent-index-data-set/"
FIGURES_WANTED = {1, 3}


def dismiss_cookie_banner(page):
    for selector in ["button:has-text('Accept All')", "button:has-text('Accept')", "button:has-text('Allow')",
        "button:has-text('Agree')", "[id*='cookie'] button", "[class*='consent'] button", ]:
        try:
            page.click(selector, timeout=3_000)
            page.wait_for_timeout(1_000)
            return
        except Exception:
            continue


def download_rtb_files(out_dir=None):
    from playwright.sync_api import sync_playwright

    if out_dir is None:
        out_dir = RTB_DIR

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(RTB_PAGE_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2_000)
        dismiss_cookie_banner(page)

        links = page.eval_on_selector_all("a[href*='Figure']", "els => els.map(e => e.href)")

        xlsx_links = {}
        for href in links:
            if not href.lower().endswith(".xlsx"):
                continue
            m = re.search(r"Figure-(\d+)\.xlsx", href, re.IGNORECASE)
            if m:
                fig_num = int(m.group(1))
                if fig_num in FIGURES_WANTED:
                    xlsx_links[fig_num] = href

        logger.info("Found figures: %s", list(xlsx_links.keys()))

        for fig_num, href in sorted(xlsx_links.items()):
            filename = Path(href).name
            out_path = out_dir / filename

            if out_path.exists():
                logger.info("Figure %d already exists — skipping", fig_num)
                downloaded.append((fig_num, out_path))
                continue

            with page.expect_download(timeout=60_000) as dl_info:
                page.evaluate(f"window.location.href = '{href}'")

            dl_info.value.save_as(out_path)
            logger.info("Saved %s (%d KB)", filename, out_path.stat().st_size // 1024)
            downloaded.append((fig_num, out_path))

            page.goto(RTB_PAGE_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(1_000)

        browser.close()

    return downloaded


def latest_files(rtb_dir=None):
    if rtb_dir is None:
        rtb_dir = RTB_DIR

    result = {}
    for fig_num in FIGURES_WANTED:
        matches = sorted(Path(rtb_dir).glob(f"*Figure-{fig_num}.xlsx"))
        if matches:
            result[fig_num] = matches[-1]

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    files = download_rtb_files()
    for fig_num, path in files:
        print(f"Downloaded Figure {fig_num}: {path.name}")
