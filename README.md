# Ireland Housing Market Analysis

A full-stack data pipeline and public dashboard for the Irish residential property market. Combines transaction-level sale prices, official inflation data, and standardised rent indices into a single analytical dataset with a REST API and interactive dashboard.

**Live data sources:**
- [Property Price Register](https://www.propertypriceregister.ie/) — every residential sale in Ireland 2010–2025
- [CSO CPM20](https://data.cso.ie/table/CPM20) — Consumer Price Index (base Dec 2016 = 100)
- [RTB/ESRI Rent Index](https://rtb.ie/data-insights/rtb-data-hub/rtb-esri-rent-index-data-set/) — quarterly national and county rent data

---

## Project Structure

```
ireland-housing-market-analysis/
├── api/                  Flask REST API
│   ├── app.py
│   └── Dockerfile
├── db/
│   └── schema.sql        PostgreSQL schema — 6 tables, 3 views
├── frontend/             React + Vite + Tailwind dashboard
│   ├── src/
│   └── Dockerfile
├── scripts/              Data acquisition and pipeline run scripts
│   ├── ppr_download.py   PPR via Playwright (IBM Domino automation)
│   ├── rtb_download.py   RTB XLSX files via Playwright
│   ├── cso_download.py   CSO CPI via PxStat REST API
│   ├── run_ppr.py
│   ├── run_rtb.py
│   ├── run_cso.py
│   ├── run_ppr_aggregated.py
│   └── run_housing_combined.py
├── tests/
│   ├── test_transformers.py   25 unit tests
│   └── test_integration.py    API contract tests
├── datasets/             Downloaded data files (gitignored)
├── docker-compose.yml    4 services: db, api, frontend, nginx
├── Makefile
└── pyproject.toml
```

---

## Derived Metrics

| Metric | Formula | Description |
|---|---|---|
| `rental_yield_pct` | `(monthly_rent × 12 / median_price) × 100` | County-level rent vs sale price |
| `real_median_price` | `median_price / (cpi_index / 100)` | Inflation-adjusted to Dec 2016 € |
| `rent_gap_eur/pct` | `new_rent - existing_rent` | Premium new tenants pay over existing |

---

## Setup

**Requirements:** Python 3.12+, PostgreSQL, Node.js 20+, [uv](https://astral.sh/uv)

```bash
# Install uv
curl -Ls https://astral.sh/uv/install.sh | sh

# Install dependencies and set up the project
make setup
```

**Environment variables** — copy and fill in:
```bash
cp .env.example .env
```

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=housing
DB_USER=housing
DB_PASSWORD=yourpassword
BRAVE_API_KEY=          # optional — for BER/bedrooms enrichment
```

---

## Running the Pipeline

Run each step in order. Each script is idempotent — safe to re-run.

```bash
# 1. Download and load PPR data (2010–2025)
#    Requires Playwright — opens headless Chromium to automate the PPR download form
uv run scripts/run_ppr.py

# 2. Download RTB rent index files and load to DB
uv run scripts/run_rtb.py

# 3. Download CSO CPI and load to DB
uv run scripts/run_cso.py

# 4. Aggregate PPR to county/quarter level
uv run scripts/run_ppr_aggregated.py

# 5. Build housing_combined (rental yield + real price)
uv run scripts/run_housing_combined.py
```

Or run everything at once:
```bash
make run
```

---

## API

Start the Flask API:
```bash
uv run api/app.py
```

| Endpoint | Description |
|---|---|
| `GET /api/national/trend` | National price, real price, yield by quarter |
| `GET /api/counties?sort=rental_yield_pct` | Latest snapshot all 26 counties |
| `GET /api/county/<n>` | Single county latest stats |
| `GET /api/county/<n>/history?from=2020Q1` | Full time series for one county |
| `GET /api/filters` | Available counties and quarters for dropdowns |

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at `http://localhost:5173`. Requires the API running at `http://localhost:8080`.

---

## Tests

```bash
# Unit tests (no DB required)
python -m unittest tests/test_transformers.py -v

# Integration tests (requires API running at localhost:5000)
python -m pytest tests/test_integration.py -v
```

25 unit tests cover all key transformation functions. Integration tests verify the API contract matches what the frontend client expects.

---

## Docker Deployment

```docker compose up --build```

## Data Sources and Licences

| Source | Licence | Notes |
|---|---|---|
| Property Price Register | [PSI Licence](https://www.gov.ie/en/circular/2c1b4-open-data-initiative/) | Statutory register under Property Services (Regulation) Act 2011 |
| CSO CPM20 | [PSI Licence](https://www.gov.ie/en/circular/2c1b4-open-data-initiative/) | Central Statistics Office open data |
| RTB/ESRI Rent Index | Public use | Published by Residential Tenancies Board |

No personal data is stored. PPR addresses are already public register data. The Brave Search API enrichment is rate-limited to 50 calls.
