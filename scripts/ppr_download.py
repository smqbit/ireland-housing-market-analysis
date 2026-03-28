# Download PPR monthly CSVs
import argparse
import calendar
import io
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PPR_FORM_URL = (
    "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/"
    "PPRDownloads?OpenForm"
)

KEEP_COLS = [
    "date_of_sale",
    "address",
    "county",
    "eircode",
    "price_eur",
    "not_full_market_price",
    "vat_exclusive",
    "property_description",
    "size_description",
]

# Site dropdowns: try several selectors in case attribute names change.
SELECTORS = {
    "county": [
        "select[name*='County' i]",
        "select[name*='county' i]",
        "select >> nth=0",
    ],
    "year": [
        "select[name*='Year' i]",
        "select[name*='year' i]",
        "select >> nth=1",
    ],
    "month": [
        "select[name*='Month' i]",
        "select[name*='month' i]",
        "select >> nth=2",
    ],
}

START_YEAR = 2010
START_MONTH = 1
DEFAULT_TIMEOUT_MS = 120_000


def set_dropdown(page, field_name, value):
    for selector in SELECTORS[field_name]:
        try:
            page.select_option(selector, value=value, timeout=5000)
            return
        except Exception:
            pass
    raise RuntimeError(f"Could not set dropdown {field_name} to {value!r}.")


def set_month_on_form(page, month_number):
    for label in (
        str(month_number),
        f"{month_number:02d}",
        calendar.month_name[month_number],
        calendar.month_abbr[month_number],
    ):
        if not label:
            continue
        try:
            set_dropdown(page, "month", label)
            return label
        except RuntimeError:
            pass
    raise RuntimeError(f"Could not select month {month_number} in the month dropdown.")


def open_ppr_form(page, timeout_ms):
    from playwright.sync_api import TimeoutError as PlaywrightTimeout

    try:
        page.goto(PPR_FORM_URL, wait_until="networkidle", timeout=timeout_ms)
    except PlaywrightTimeout:
        page.goto(PPR_FORM_URL, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(2000)


def normalize_columns(dataframe):
    new_names = {}
    for original in dataframe.columns:
        name = original.strip()
        lower = name.lower()
        if "date" in lower and "sale" in lower:
            new_names[original] = "date_of_sale"
        elif name == "Address":
            new_names[original] = "address"
        elif name == "County":
            new_names[original] = "county"
        elif name == "Eircode":
            new_names[original] = "eircode"
        elif name.startswith("Price"):
            new_names[original] = "price_eur"
        elif "full market" in lower:
            new_names[original] = "not_full_market_price"
        elif "vat" in lower:
            new_names[original] = "vat_exclusive"
        elif "description of property" in lower:
            new_names[original] = "property_description"
        elif "size" in lower:
            new_names[original] = "size_description"

    out = dataframe.rename(columns=new_names)
    present = []
    for col in KEEP_COLS:
        if col in out.columns:
            present.append(col)
    return out[present].copy()


def download_ppr_on_page(page, year, month, timeout_ms=None):
    if month < 1 or month > 12:
        raise ValueError(f"month must be 1-12, got {month}")

    if timeout_ms is None:
        timeout_ms = DEFAULT_TIMEOUT_MS

    open_ppr_form(page, timeout_ms)
    set_dropdown(page, "county", "ALL")
    set_dropdown(page, "year", str(year))
    set_month_on_form(page, month)

    with page.expect_download(timeout=timeout_ms) as download_event:
        page.click("input[type='submit']", timeout=5000)
        try:
            page.click("text=CLICK HERE TO DOWNLOAD THE FILE", timeout=25000)
        except Exception:
            try:
                page.click("text=Perform Download", timeout=5000)
            except Exception:
                page.click("text=CLICK HERE TO DOWNLOAD", timeout=5000)

    download = download_event.value
    temp_path = download.path()
    if not temp_path:
        raise RuntimeError("Download did not produce a file path.")
    with open(temp_path, "rb") as f:
        raw_bytes = f.read()

    df = pd.read_csv(io.BytesIO(raw_bytes), encoding="cp1252", dtype=str)
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df = normalize_columns(df)
    df["year"] = year
    df["month"] = month
    return df


def download_ppr_month(year, month, headless=True, timeout_ms=None):
    from playwright.sync_api import sync_playwright

    if timeout_ms is None:
        timeout_ms = DEFAULT_TIMEOUT_MS

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            ignore_https_errors=True,
            accept_downloads=True,
        )
        page = context.new_page()
        try:
            return download_ppr_on_page(page, year, month, timeout_ms=timeout_ms)
        finally:
            page.close()
            browser.close()


def previous_calendar_month(today):
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def main():
    parser = argparse.ArgumentParser(
        description="Download missing PPR files from Jan 2010"
    )
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument("--end-month", type=int, default=None)
    parser.add_argument("--out-dir", default=PROJECT_ROOT / "datasets" / "ppr")
    parser.add_argument("--no-headless", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    end_year, end_month = previous_calendar_month(date.today())

    if args.end_year is not None or args.end_month is not None:
        if args.end_year is None or args.end_month is None:
            print("Error: use --end-year and --end-month together.", file=sys.stderr)
            sys.exit(1)
        if args.end_month < 1 or args.end_month > 12:
            print("Error: --end-month must be between 1 and 12.", file=sys.stderr)
            sys.exit(1)
        end_year, end_month = args.end_year, args.end_month

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if (end_year, end_month) < (START_YEAR, START_MONTH):
        print("Nothing to do (end before Jan 2010).")
        return

    pending = []
    skipped = 0
    year, month = START_YEAR, START_MONTH
    while (year, month) <= (end_year, end_month):
        out_path = out_dir / f"ppr_{year:04d}-{month:02d}.csv"
        if out_path.exists() and not args.force:
            skipped += 1
            print(f"Skip {out_path.name}")
        else:
            pending.append((year, month, out_path))

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    if len(pending) == 0:
        print(f"Done. 0 downloaded, {skipped} skipped.")
        return

    from playwright.sync_api import sync_playwright

    headless = not args.no_headless
    downloaded = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            ignore_https_errors=True,
            accept_downloads=True,
        )
        try:
            for year, month, out_path in pending:
                page = context.new_page()
                try:
                    df = download_ppr_on_page(page, year, month)
                    df.to_csv(out_path, index=False)
                    downloaded += 1
                    print(f"Saved {out_path.name}")
                finally:
                    page.close()
        finally:
            browser.close()

    print(f"Done. {downloaded} downloaded, {skipped} skipped.")


if __name__ == "__main__":
    main()
