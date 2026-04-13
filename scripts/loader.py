import logging
import os
from contextlib import contextmanager

import pandas as pd
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "housing"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "123456"),
    )


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

    rows = [
        (
            row.date_of_sale,
            row.address if pd.notna(row.address) else None,
            row.county,
            row.eircode if pd.notna(row.eircode) else None,
            float(row.price_eur),
            bool(row.is_new),
            bool(row.is_full_market),
            row.property_description if pd.notna(row.property_description) else None,
            row.size_description if pd.notna(row.size_description) else None,
            int(row.year),
            row.quarter if pd.notna(row.quarter) else None,
        )
        for row in df.itertuples(index=False)
    ]

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

if __name__ == "__main__":
    pass