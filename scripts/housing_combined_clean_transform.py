import logging

import pandas as pd

logger = logging.getLogger(__name__)


def derive_rental_yield(ppr_agg, rtb_national, rtb_county):
    df = ppr_agg.merge(rtb_county[["county", "new_rent_eur", "existing_rent_eur", "rent_gap_eur", "rent_gap_pct"]],
                       on="county", how="left", suffixes=("", "_county")).merge(
        rtb_national[["quarter", "new_rent_eur", "existing_rent_eur", "rent_gap_eur", "rent_gap_pct"]], on="quarter",
        how="left", suffixes=("_county", "_national"))

    df["monthly_rent"] = df["new_rent_eur_county"].fillna(df["new_rent_eur_national"])
    df["existing_rent"] = df["existing_rent_eur_county"].fillna(df["existing_rent_eur_national"])
    df["rent_gap_eur"] = df["rent_gap_eur_county"].fillna(df["rent_gap_eur_national"])
    df["rent_gap_pct"] = df["rent_gap_pct_county"].fillna(df["rent_gap_pct_national"])
    df["rent_source"] = df["new_rent_eur_county"].apply(lambda x: "county" if pd.notna(x) else "national")
    df["rental_yield_pct"] = ((df["monthly_rent"] * 12) / df["median_price"].astype(float) * 100).round(2)

    drop = [c for c in df.columns if c.endswith("_county") or c.endswith("_national")]
    df = df.drop(columns=drop)

    logger.info("Rental yield: %d rows", len(df))
    return df


def derive_real_price(housing_df, cpi_df):
    # Join on year — CPI is annual average per year
    # cpi_df has year, month, index_value — take December reading as the year's index
    cpi_annual = (cpi_df.sort_values("month").groupby("year")["index_value"].last().reset_index().rename(
        columns={"index_value": "cpi_index"}))
    cpi_annual["cpi_index"] = pd.to_numeric(cpi_annual["cpi_index"], errors="coerce")

    housing_df["year"] = housing_df["year"].astype(int)
    df = housing_df.merge(cpi_annual, on="year", how="left")
    df["real_median_price"] = (df["median_price"].astype(float) / (df["cpi_index"] / 100)).round(0)

    logger.info("Real price: %d rows, %d with CPI", len(df), df["cpi_index"].notna().sum())
    return df
