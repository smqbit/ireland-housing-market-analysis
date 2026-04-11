import io
import urllib.request

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def clean_rtb_national(df):
    logger.info("RTB national clean: %d rows in", len(df))
    df = df.iloc[:, :2].copy()
    df.columns = ["quarter", "rent_eur"]
    df = df.dropna(subset=["quarter", "rent_eur"])
    df = df[df["quarter"].astype(str).str.match(r"^Q[1-4] \d{4}$")]
    df["rent_eur"] = pd.to_numeric(df["rent_eur"], errors="coerce").round(2)
    df = df.dropna(subset=["rent_eur"])
    df["quarter"] = df["quarter"].apply(lambda q: f"{q.split()[1]}Q{q.split()[0][1]}")
    logger.info("RTB national clean: %d rows out", len(df))
    return df


def load_rtb_national_xlsxs(fig1_path):
    src = io.BytesIO(urllib.request.urlopen(fig1_path).read()) if str(fig1_path).startswith("http") else fig1_path
    df_new = pd.read_excel(src, sheet_name="RIQ325 new", header=1, engine="openpyxl")
    df_existing = pd.read_excel(src, sheet_name="RIQ325 existing", header=1, engine="openpyxl")
    new = clean_rtb_national(df_new).rename(columns={"rent_eur": "new_rent_eur"})
    existing = clean_rtb_national(df_existing).rename(columns={"rent_eur": "existing_rent_eur"})
    df = new.merge(existing, on="quarter", how="left")
    df["rent_gap_eur"] = (df["new_rent_eur"] - df["existing_rent_eur"]).round(2)
    df["rent_gap_pct"] = ((df["rent_gap_eur"] / df["existing_rent_eur"]) * 100).round(2)

    logger.info("RTB national: %d quarters", len(df))
    return df


def clean_rtb_county(fig3_path_or_df, df_existing=None):
    if isinstance(fig3_path_or_df, pd.DataFrame):
        df_new = fig3_path_or_df
    else:
        df_new = pd.read_excel(fig3_path_or_df, sheet_name="RIQ325 New", header=1, engine="openpyxl")
        df_existing = pd.read_excel(fig3_path_or_df, sheet_name="RIQ325 Existing", header=1, engine="openpyxl")

    def clean_sheet(df, col_name):
        df = df.iloc[:, :2].copy()
        df.columns = ["county", col_name]
        df = df.dropna(subset=["county", col_name])
        df = df[df["county"].astype(str).str.match(r"^[A-Z][a-z]")]
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce").round(2)
        return df.dropna(subset=[col_name])

    new = clean_sheet(df_new, "new_rent_eur")
    existing = clean_sheet(df_existing, "existing_rent_eur")

    df = new.merge(existing, on="county", how="left")
    df["quarter"] = "2025Q3"
    df["rent_gap_eur"] = (df["new_rent_eur"] - df["existing_rent_eur"]).round(2)
    df["rent_gap_pct"] = ((df["rent_gap_eur"] / df["existing_rent_eur"]) * 100).round(2)

    logger.info("RTB county clean: %d counties out", len(df))
    return df

load_rtb_county_xlsxs = clean_rtb_county