import decimal
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from loader import get_conn

app = Flask(__name__)
CORS(app)


def query(sql, params=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows


def clean(rows):
    result = []
    for row in rows:
        result.append({k: float(v) if isinstance(v, decimal.Decimal) else v for k, v in row.items()})
    return result


@app.route("/api/national/trend")
def national_trend():
    from_q = request.args.get("from")
    to_q = request.args.get("to")
    sql = "SELECT * FROM v_national_trend WHERE 1=1"
    params = []
    if from_q:
        sql += " AND quarter >= %s"
        params.append(from_q)
    if to_q:
        sql += " AND quarter <= %s"
        params.append(to_q)
    return jsonify(clean(query(sql + " ORDER BY quarter", params)))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(debug=os.getenv("FLASK_ENV") == "development", host="0.0.0.0", port=port)
