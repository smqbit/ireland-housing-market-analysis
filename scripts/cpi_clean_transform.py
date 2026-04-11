import io
import urllib.request

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_cpi(df):
    logger.info("CPI clean: %d rows in", len(df))
    df = df.copy()
    df.columns = df.columns.str.strip()
    stat_col = next((c for c in df.columns if "statistic label" in c.lower()), None)
    if stat_col:
        mask = (
            df[stat_col].str.contains("December 2016", na=False) &
            df[stat_col].str.contains("100", na=False)
        )
        df = df[mask].copy()
 
    commodity_col = next((c for c in df.columns if "commodity" in c.lower()), None)
    if commodity_col:
        df = df[df[commodity_col].str.lower().str.contains("all item", na=False)].copy()
 
    month_col = next((c for c in df.columns if "month" in c.lower() or "tlist" in c.lower()), None)
    value_col = next((c for c in df.columns if c.upper() == "VALUE"), None)
 
    df = df[[month_col, value_col]].copy()
    df.columns = ["month", "index_value"]
    df["index_value"] = pd.to_numeric(df["index_value"], errors="coerce")
    df = df.dropna(subset=["index_value"])
 
    # Parse YYYYMM integer 201001 to year=2010, month=1
    def parse_ym(val):
        try:
            s = str(int(float(val)))
            if len(s) == 6:
                yr, mo = int(s[:4]), int(s[4:])
                if 1 <= mo <= 12:
                    return yr, mo
        except Exception:
            pass
        return None, None
 
    df[["year", "month"]] = pd.DataFrame(df["month"].apply(parse_ym).tolist(), index=df.index)
    df = df.dropna(subset=["year", "month"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df = df[df["year"] >= 2010]
    df = df[["year", "month", "index_value"]]
 
    logger.info("CPI clean: %d rows out", len(df))
    return df
    logger.info("CPI clean: %d rows in", len(df))
    df = df.copy()
    df.columns = df.columns.str.strip()

    stat_col = next((c for c in df.columns if "statistic label" in c.lower()), None)
    if stat_col:
        mask = (
            df[stat_col].str.contains("December 2016", na=False) &
            df[stat_col].str.contains("100", na=False)
        )
        df = df[mask].copy()
 
    commodity_col = next((c for c in df.columns if "commodity" in c.lower()), None)
    if commodity_col:
        df = df[df[commodity_col].str.lower().str.contains("all item", na=False)].copy()
 
    month_col = next((c for c in df.columns if "month" in c.lower() or "tlist" in c.lower()), None)
    value_col = next((c for c in df.columns if c.upper() == "VALUE"), None)
 
    df = df[[month_col, value_col]].copy()
    df.columns = ["month", "index_value"]
    df["index_value"] = pd.to_numeric(df["index_value"], errors="coerce")
    df = df.dropna(subset=["index_value"])
 
    # Parse YYYYMM integer e.g. 201001 to "2010 January"
    def parse_month(val):
        try:
            s = str(int(float(val)))
            if len(s) == 6:
                yr, mo = int(s[:4]), int(s[4:])
                if 1 <= mo <= 12:
                    return pd.Timestamp(yr, mo, 1).strftime("%Y %B")
        except Exception:
            pass
        return str(val)
 
    df["month"] = df["month"].apply(parse_month)
    df = df[df["month"].astype(str).apply(lambda m: m[:4].isdigit() and int(m[:4]) >= 2010)]
 
    logger.info("CPI cleaned: %d rows out", len(df))
    return df