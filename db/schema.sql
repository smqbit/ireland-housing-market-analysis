CREATE TABLE IF NOT EXISTS ppr_sales (
    id                    SERIAL PRIMARY KEY,
    date_of_sale          DATE           NOT NULL,
    address               TEXT,
    county                VARCHAR(50)    NOT NULL,
    eircode               VARCHAR(10),
    price_eur             NUMERIC(12,2)  NOT NULL,
    is_new                BOOLEAN        NOT NULL DEFAULT FALSE,
    is_full_market        BOOLEAN        NOT NULL DEFAULT TRUE,
    property_description  TEXT,
    size_description      VARCHAR(50),
    year                  SMALLINT       NOT NULL,
    quarter               VARCHAR(7),
    ber_rating            VARCHAR(5),
    bedrooms              SMALLINT,
    bathrooms             SMALLINT,
    floor_area_sqm        NUMERIC(8,2),
    enriched_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rtb_national (
    id                SERIAL PRIMARY KEY,
    quarter           VARCHAR(7)   NOT NULL UNIQUE,
    new_rent_eur      NUMERIC(8,2) NOT NULL,
    existing_rent_eur NUMERIC(8,2),
    rent_gap_eur      NUMERIC(8,2),
    rent_gap_pct      NUMERIC(5,2),
    created_at        TIMESTAMPTZ  DEFAULT NOW()
);
 
CREATE TABLE IF NOT EXISTS rtb_county (
    id                SERIAL PRIMARY KEY,
    county            VARCHAR(50)  NOT NULL,
    quarter           VARCHAR(7)   NOT NULL,
    new_rent_eur      NUMERIC(8,2) NOT NULL,
    existing_rent_eur NUMERIC(8,2),
    rent_gap_eur      NUMERIC(8,2),
    rent_gap_pct      NUMERIC(5,2),
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (county, quarter)
);

CREATE TABLE IF NOT EXISTS cso_cpi (
    id           SERIAL PRIMARY KEY,
    year         SMALLINT      NOT NULL,
    month        SMALLINT      NOT NULL,
    index_value  NUMERIC(8,2)  NOT NULL,
    created_at   TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (year, month)
);


CREATE TABLE IF NOT EXISTS ppr_aggregated (
    id                SERIAL PRIMARY KEY,
    county            VARCHAR(50)   NOT NULL,
    year              SMALLINT      NOT NULL,
    quarter           VARCHAR(7)    NOT NULL,
    median_price      NUMERIC(12,2),
    mean_price        NUMERIC(12,2),
    min_price         NUMERIC(12,2),
    max_price         NUMERIC(12,2),
    transaction_count INTEGER       NOT NULL,
    pct_new           NUMERIC(5,2),
    created_at        TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (county, quarter)
);

CREATE TABLE IF NOT EXISTS housing_combined (
    id                  SERIAL PRIMARY KEY,
    county              VARCHAR(50)   NOT NULL,
    year                SMALLINT      NOT NULL,
    quarter             VARCHAR(7)    NOT NULL,
    median_price        NUMERIC(12,2),
    mean_price          NUMERIC(12,2),
    transaction_count   INTEGER,
    pct_new             NUMERIC(5,2),
    real_median_price   NUMERIC(12,2),
    cpi_index           NUMERIC(8,2),
    monthly_rent        NUMERIC(8,2),
    existing_rent       NUMERIC(8,2),
    rent_gap_eur        NUMERIC(8,2),
    rent_gap_pct        NUMERIC(5,2),
    rent_source         VARCHAR(10),
    rental_yield_pct    NUMERIC(5,2),
    affordability_ratio NUMERIC(6,2),
    yoy_growth_pct      NUMERIC(6,2),
    qoq_growth_pct      NUMERIC(6,2),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (county, quarter)
);