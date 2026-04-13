import logging
import os
from contextlib import contextmanager

import pandas as pd
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def get_conn():
    return psycopg2.connect(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "5432")),
                            dbname=os.getenv("DB_NAME", ""), user=os.getenv("DB_USER", ""),
                            password=os.getenv("DB_PASSWORD", ""), )


@contextmanager
def cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def apply_schema(conn, schema_path=None):
    if schema_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        for base in [here, os.path.join(here, ".."), os.path.join(here, "..", "..")]:
            candidate = os.path.join(base, "db", "schema.sql")
            if os.path.exists(candidate):
                schema_path = candidate
                break
        if schema_path is None:
            raise FileNotFoundError("Could not find schema")

    with open(schema_path) as f:
        sql = f.read()

    with cursor(conn) as cur:
        cur.execute(sql)

    logger.info("Schema applied")


def load_ppr(conn, df):
    if df.empty:
        logger.warning("load_ppr: empty dataframe")
        return 0

    # Dedup index — safe to create multiple times
    with cursor(conn) as cur:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ppr_dedup
            ON ppr_sales (date_of_sale, county, price_eur)
        """)

    rows = [(row.date_of_sale, row.address if pd.notna(row.address) else None, row.county,
             row.eircode if pd.notna(row.eircode) else None, float(row.price_eur), bool(row.is_new),
             bool(row.is_full_market), row.property_description if pd.notna(row.property_description) else None,
             row.size_description if pd.notna(row.size_description) else None, int(row.year),
             row.quarter if pd.notna(row.quarter) else None,) for row in df.itertuples(index=False)]

    sql = """
        INSERT INTO ppr_sales (
            date_of_sale, address, county, eircode,
            price_eur, is_new, is_full_market,
            property_description, size_description,
            year, quarter
        ) VALUES %s
        ON CONFLICT (date_of_sale, county, price_eur) DO NOTHING
    """

    inserted = 0
    batch_size = 5_000

    with cursor(conn) as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i: i + batch_size]
            psycopg2.extras.execute_values(cur, sql, batch, page_size=batch_size)
            inserted += cur.rowcount
            logger.info("PPR load: %d / %d", i + len(batch), len(rows))

    logger.info("PPR load done: %d inserted", inserted)
    return inserted


def load_cpi(conn, df):
    if df.empty:
        logger.warning("load_cpi: empty dataframe")
        return 0

    rows = [(int(row.year), int(row.month), float(row.index_value)) for row in df.itertuples(index=False)]

    sql = """
        INSERT INTO cso_cpi (year, month, index_value)
        VALUES %s
        ON CONFLICT (year, month) DO NOTHING
    """

    with cursor(conn) as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
        inserted = cur.rowcount

    logger.info("CPI loaded: %d rows", inserted)
    return inserted


def load_ppr_aggregated(conn, df):
    if df.empty:
        logger.warning("load_ppr_aggregated: empty dataframe")
        return 0

    rows = [
        (row.county, int(row.year), row.quarter, float(row.median_price), float(row.mean_price), float(row.min_price),
         float(row.max_price), int(row.transaction_count), float(row.pct_new),) for row in df.itertuples(index=False)]

    sql = """
        INSERT INTO ppr_aggregated
            (county, year, quarter, median_price, mean_price, min_price, max_price,
             transaction_count, pct_new)
        VALUES %s
        ON CONFLICT (county, quarter) DO UPDATE SET
            median_price      = EXCLUDED.median_price,
            mean_price        = EXCLUDED.mean_price,
            min_price         = EXCLUDED.min_price,
            max_price         = EXCLUDED.max_price,
            transaction_count = EXCLUDED.transaction_count,
            pct_new           = EXCLUDED.pct_new
    """

    with cursor(conn) as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
        inserted = cur.rowcount

    logger.info("PPR aggregated loaded: %d rows", inserted)
    return inserted


def load_housing_combined(conn, df):
    if df.empty:
        logger.warning("load_housing_combined: empty dataframe")
        return 0

    cols = ["county", "year", "quarter", "median_price", "mean_price", "transaction_count", "pct_new", "monthly_rent",
            "existing_rent", "rent_gap_eur", "rent_gap_pct", "rent_source", "rental_yield_pct", "cpi_index",
            "real_median_price"]

    rows = [tuple(None if pd.isna(v) else v for v in row) for row in df[cols].itertuples(index=False)]

    sql = """
        INSERT INTO housing_combined (county, year, quarter, median_price, mean_price,
            transaction_count, pct_new, monthly_rent, existing_rent, rent_gap_eur,
            rent_gap_pct, rent_source, rental_yield_pct, cpi_index, real_median_price)
        VALUES %s
        ON CONFLICT (county, quarter) DO UPDATE SET
            median_price = EXCLUDED.median_price, mean_price = EXCLUDED.mean_price,
            transaction_count = EXCLUDED.transaction_count, pct_new = EXCLUDED.pct_new,
            monthly_rent = EXCLUDED.monthly_rent, existing_rent = EXCLUDED.existing_rent,
            rent_gap_eur = EXCLUDED.rent_gap_eur, rent_gap_pct = EXCLUDED.rent_gap_pct,
            rent_source = EXCLUDED.rent_source, rental_yield_pct = EXCLUDED.rental_yield_pct,
            cpi_index = EXCLUDED.cpi_index, real_median_price = EXCLUDED.real_median_price
    """

    with cursor(conn) as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
        inserted = cur.rowcount

    logger.info("housing_combined loaded: %d rows", inserted)
    return inserted


if __name__ == "__main__":
    pass
