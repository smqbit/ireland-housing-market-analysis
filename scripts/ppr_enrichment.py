import os
import json
import time
import re
import requests
import pandas as pd
from pathlib import Path
import hashlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]

API_KEY = os.getenv("BRAVE_API_KEY")
if not API_KEY:
    raise ValueError("BRAVE_API_KEY not set")

BASE_URL = "https://api.search.brave.com/res/v1/llm/context"

INPUT_DIR = PROJECT_ROOT / "datasets" / "ppr"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "ppr"
RAW_JSON_DIR = PROJECT_ROOT / "raw_responses"
PROCESSED_FILE = PROJECT_ROOT / "datasets" / "ppr" / "processed_addresses.json"

MAX_API_CALLS = int(os.getenv("BRAVE_MAX_API_CALLS") or 10)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(RAW_JSON_DIR, exist_ok=True)

if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r") as f:
        processed_addresses = set(json.load(f))
else:
    processed_addresses = set()

api_calls_made = 0

#  BER Ratings
VALID_BER = {
    "A1","A2","A3",
    "B1","B2","B3",
    "C1","C2","C3",
    "D1","D2",
    "E1","E2",
    "F","G"
}

BER_CONTEXT_REGEX = re.compile(
    r"(?:BER|Energy\s*Rating|rated)\s*[:\-]?\s*(A[1-3]|B[1-3]|C[1-3]|D[1-2]|E[1-2]|F|G)",
    re.IGNORECASE
)

BER_FALLBACK_REGEX = re.compile(
    r"\b(A[1-3]|B[1-3]|C[1-3]|D[1-2]|E[1-2]|F|G)\b"
)

BED_REGEX = re.compile(r"(\d+)\s*(bed|beds|bedroom|bedrooms)", re.IGNORECASE)
BATH_REGEX = re.compile(r"(\d+)\s*(bath|baths|bathroom|bathrooms)", re.IGNORECASE)

AREA_REGEX = re.compile(
    r"(\d+(?:\.\d+)?)\s*(m²|sqm|sq\.?\s?m|m2|meters2|sqft|sq ft)",
    re.IGNORECASE
)

def normalize_area(value, unit):
    unit = unit.lower()
    if unit in ["sqft", "sq ft"]:
        return round(value * 0.092903, 2)
    return value

def extract_ber(text):
    m = BER_CONTEXT_REGEX.search(text)
    if m:
        val = m.group(1).upper()
        if val in VALID_BER:
            return val

    matches = BER_FALLBACK_REGEX.findall(text)
    for val in matches:
        val = val.upper()
        if val in VALID_BER:
            return val

    return None

def extract_year_month(file_path):
    name = Path(file_path).stem
    try:
        _, ym = name.split("_")
        y, m = ym.split("-")
        return int(y), int(m)
    except:
        return (0, 0)

def extract_features(snippets_with_source):
    ber = beds = baths = area = None
    credible = []
    other = []

    for item in snippets_with_source:
        url = item["url"]
        snippets = item["snippets"]

        if any(d in url for d in ["daft.ie", "myhome.ie", "socproperty.ie", "blueskyproperty.ie"]):
            credible.extend(snippets)
        else:
            other.extend(snippets)

    ordered = credible + other
    text = " ".join(ordered)

    for s in ordered:
        try:
            data = json.loads(s)
            table = data.get("table")

            if isinstance(table, list):
                for row in table:
                    if isinstance(row, dict):

                        if not beds and "Beds" in row:
                            m = BED_REGEX.search(row["Beds"])
                            if m:
                                beds = int(m.group(1))

                        if not area and "Size" in row:
                            m = AREA_REGEX.search(row["Size"])
                            if m:
                                area = normalize_area(float(m.group(1)), m.group(2))

                        if not ber and "Energy Rating" in row:
                            val = extract_ber(row["Energy Rating"])
                            if val:
                                ber = val

            elif isinstance(table, dict):
                if not ber and "Energy Rating" in table:
                    val = extract_ber(table["Energy Rating"])
                    if val:
                        ber = val
        except:
            continue

    if not ber:
        ber = extract_ber(text)

    if not beds:
        m = BED_REGEX.search(text)
        if m:
            beds = int(m.group(1))

    if not baths:
        m = BATH_REGEX.search(text)
        if m:
            baths = int(m.group(1))

    if not area:
        m = AREA_REGEX.search(text)
        if m:
            area = normalize_area(float(m.group(1)), m.group(2))

    return {
        "ber_rating": ber,
        "bedrooms": beds,
        "bathrooms": baths,
        "floor_area": area,
    }

def fetch_property_data(query):
    global api_calls_made

    if api_calls_made >= MAX_API_CALLS:
        return None

    headers = {
        "X-Subscription-Token": API_KEY,
        "Accept": "application/json"
    }

    try:
        r = requests.get(BASE_URL, headers=headers, params={"q": query}, timeout=10)
        r.raise_for_status()
        api_calls_made += 1
        print(f"API calls: {api_calls_made}/{MAX_API_CALLS}")
        return r.json()
    except Exception as e:
        print(f"Something went wrong: {e}")
        return None

def process_csv(file_path):
    global api_calls_made

    print(f"\nProcessing {file_path.name}")
    df = pd.read_csv(file_path)

    for col in ["ber_rating", "bedrooms", "bathrooms", "floor_area"]:
        if col not in df.columns:
            df[col] = None

    priority_indices = list(df.index)
    if "year" in df.columns and "month" in df.columns:
        priority_indices = sorted(
            df.index,
            key=lambda i: (df.at[i, "year"], df.at[i, "month"]),
            reverse=True
        )

    for idx in priority_indices:
        if api_calls_made >= MAX_API_CALLS:
            break

        address = str(df.at[idx, "address"])
        eircode = str(df.at[idx, "eircode"]) if "eircode" in df.columns else ""

        if address in processed_addresses:
            continue

        if pd.notna(df.at[idx, "ber_rating"]):
            continue

        query = f"{address} {eircode} Ireland"
        print(f"{query}")

        data = fetch_property_data(query)
        if not data:
            continue

        # # Save raw JSON
        # fname = hashlib.md5(address.encode()).hexdigest()
        # with open(os.path.join(RAW_JSON_DIR, f"{fname}.json"), "w") as f:
        #     json.dump(data, f, indent=2)

        snippets_with_source = []
        for item in data.get("grounding", {}).get("generic", []):
            snippets_with_source.append({
                "url": item.get("url", ""),
                "snippets": item.get("snippets", [])
            })

        features = extract_features(snippets_with_source)

        # Update only if present
        if features["ber_rating"]:
            df.at[idx, "ber_rating"] = features["ber_rating"]

        if features["bedrooms"]:
            df.at[idx, "bedrooms"] = features["bedrooms"]

        if features["bathrooms"]:
            df.at[idx, "bathrooms"] = features["bathrooms"]

        if features["floor_area"]:
            df.at[idx, "floor_area"] = features["floor_area"]

        processed_addresses.add(address)
        time.sleep(1)

    out_path = os.path.join(OUTPUT_DIR, file_path.name)
    df.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

def main():
    global api_calls_made

    files = list(Path(INPUT_DIR).glob("*.csv"))
    files.sort(key=lambda x: extract_year_month(x), reverse=True)

    for f in files:
        print(f" - {f.name}")

    for f in files:
        if api_calls_made >= MAX_API_CALLS:
            break
        process_csv(f)

    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed_addresses), f, indent=2)

    print("\nCompleted execution")

if __name__ == "__main__":
    main()