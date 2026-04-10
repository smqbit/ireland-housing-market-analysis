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
        dbname=os.getenv("DB_NAME", ""),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
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


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        conn = get_conn()
        apply_schema(conn)
        with cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) FROM ppr_sales")
            print(f"ppr_sales rows: {cur.fetchone()[0]:,}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if df.empty:
        logger.warning("load_rtb_county: empty dataframe")
        return 0

    rows = [
        (
            row.county,
            row.quarter,
            float(row.new_rent_eur),
            float(row.existing_rent_eur) if pd.notna(row.existing_rent_eur) else None,
            float(row.rent_gap_eur) if pd.notna(row.rent_gap_eur) else None,
            float(row.rent_gap_pct) if pd.notna(row.rent_gap_pct) else None,
        )
        for row in df.itertuples(index=False)
    ]

    sql = """
        INSERT INTO rtb_county (county, quarter, new_rent_eur, existing_rent_eur, rent_gap_eur, rent_gap_pct)
        VALUES %s
        ON CONFLICT (county, quarter) DO UPDATE SET
            new_rent_eur      = EXCLUDED.new_rent_eur,
            existing_rent_eur = EXCLUDED.existing_rent_eur,
            rent_gap_eur      = EXCLUDED.rent_gap_eur,
            rent_gap_pct      = EXCLUDED.rent_gap_pct
    """

    with cursor(conn) as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
        inserted = cur.rowcount

    logger.info("RTB county loaded: %d rows", inserted)
    return inserted
