import logging

import pandas as pd

logger = logging.getLogger(__name__)

COUNTY_NORMALISE = {"Co. Dublin": "Dublin", "Co Dublin": "Dublin", "Co. Cork": "Cork", "Co Cork": "Cork",
                    "Co. Galway": "Galway", "Co Galway": "Galway", "Co. Kerry": "Kerry", "Co. Kildare": "Kildare",
                    "Co. Limerick": "Limerick", "Co. Mayo": "Mayo", "Co. Meath": "Meath", "Co. Wexford": "Wexford",
                    "Co. Wicklow": "Wicklow", "Co. Tipperary": "Tipperary", "Co. Clare": "Clare", "Co. Louth": "Louth",
                    "Co. Waterford": "Waterford", "Co. Sligo": "Sligo", "Co. Longford": "Longford",
                    "Co. Westmeath": "Westmeath", "Co. Offaly": "Offaly", "Co. Laois": "Laois", "Co. Cavan": "Cavan",
                    "Co. Monaghan": "Monaghan", "Co. Roscommon": "Roscommon", "Co. Leitrim": "Leitrim",
                    "Co. Donegal": "Donegal", "Co. Carlow": "Carlow", "Co. Kilkenny": "Kilkenny", }


def clean_ppr(df):
    logger.info("PPR clean: %d rows in", len(df))
    df = df.copy()

    # Parse date
    df["date_of_sale"] = pd.to_datetime(df["date_of_sale"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date_of_sale"])

    # Cast price to float
    df["price_eur"] = (
        df["price_eur"].astype(str).str.replace("€", "", regex=False).str.replace(",", "", regex=False).str.strip())
    df["price_eur"] = pd.to_numeric(df["price_eur"], errors="coerce")
    df = df.dropna(subset=["price_eur"])
    df = df[(df["price_eur"] >= 5_000) & (df["price_eur"] <= 50_000_000)]

    # Derived flags
    df["is_new"] = df["property_description"].astype(str).str.contains("New Dwelling", case=False, na=False)
    df["is_full_market"] = df["not_full_market_price"].astype(str).str.strip().str.lower() == "no"

    # Keep only full market sales
    df = df[df["is_full_market"]]

    # Quarter e.g. "2021Q1"
    df["quarter"] = df["date_of_sale"].dt.year.astype(str) + "Q" + df["date_of_sale"].dt.quarter.astype(str)

    # Normalise county
    df["county"] = df["county"].astype(str).str.strip().str.title().replace(COUNTY_NORMALISE)

    # Clean eircode
    df["eircode"] = df["eircode"].astype(str).str.strip().str.upper()
    df.loc[df["eircode"].isin(["", "NAN", "NONE", "N/A"]), "eircode"] = None

    keep = ["date_of_sale", "address", "county", "eircode", "price_eur", "is_new", "is_full_market",
            "property_description", "size_description", "year", "quarter"]
    df = df[[c for c in keep if c in df.columns]].copy()

    logger.info("PPR clean: %d rows out", len(df))
    return df


def load_ppr_csvs(ppr_dir):
    # Reads all ppr_YYYY-MM.csv files from the given directory
    from pathlib import Path

    files = sorted(Path(ppr_dir).glob("ppr_*.csv"))
    if not files:
        raise FileNotFoundError(f"No ppr_*.csv files found in {ppr_dir}")

    frames = []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        frames.append(df)
        logger.info("Loaded %s (%d rows)", f.name, len(df))

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Total rows loaded: %d from %d files", len(combined), len(files))
    return combined


def aggregate_ppr(df):
    logger.info("PPR aggregate: %d rows in", len(df))

    agg = (df.groupby(["county", "year", "quarter"]).agg(median_price=("price_eur", "median"),
                                                         mean_price=("price_eur", "mean"),
                                                         min_price=("price_eur", "min"), max_price=("price_eur", "max"),
                                                         transaction_count=("price_eur", "count"),
                                                         pct_new=("is_new", "mean"), ).reset_index())

    agg["median_price"] = agg["median_price"].round(2)
    agg["mean_price"] = agg["mean_price"].round(2)
    agg["pct_new"] = (agg["pct_new"] * 100).round(2)

    logger.info("PPR aggregate: %d county/quarter rows out", len(agg))
    return agg


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ppr_dir = "../datasets/ppr"

    raw = load_ppr_csvs(ppr_dir)
    cleaned = clean_ppr(raw)

    print(cleaned.head(3).to_string())
    print(cleaned.dtypes)
    print("Done.")
