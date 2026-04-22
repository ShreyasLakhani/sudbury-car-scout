from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
import psycopg2
import os
import logging
import time
from collections import defaultdict
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
import uvicorn

load_dotenv()
app = FastAPI()
logger = logging.getLogger(__name__)

# --- Models ---

class Alert(BaseModel):
    email: EmailStr
    target_price: int = Field(..., ge=500, le=500_000)
    keyword: str = Field(..., min_length=1, max_length=100)


# --- Middleware ---

allowed_origins = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:5174",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# --- Simple in-memory rate limiter ---

_alert_timestamps: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 5       # max requests
_RATE_WINDOW = 3600   # per hour


def _check_rate_limit(client_id: str) -> None:
    now = time.time()
    window_start = now - _RATE_WINDOW
    hits = [t for t in _alert_timestamps[client_id] if t > window_start]
    if len(hits) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many alert requests. Please try again later.",
        )
    hits.append(now)
    _alert_timestamps[client_id] = hits


# --- DB ---

def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        return psycopg2.connect(db_url)
    except psycopg2.OperationalError as exc:
        logger.error("Database connection failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


# --- Helpers ---

def _parse_price(raw: str) -> float:
    return float(raw.replace("$", "").replace(",", "").strip())


def _parse_mileage(raw: str) -> float:
    return float(raw.replace("km", "").replace(",", "").strip())


def analyze_market(cars: list[dict]) -> RandomForestRegressor | None:
    df = pd.DataFrame(cars)
    if len(df) < 5:
        return None
    try:
        df["p_val"] = df["price"].astype(str).apply(
            lambda v: float(v.replace("$", "").replace(",", "").strip())
        )
        df["m_val"] = df["mileage"].astype(str).apply(
            lambda v: float(v.replace("km", "").replace(",", "").strip())
        )
    except (ValueError, KeyError):
        return None

    if df["m_val"].nunique() < 2 or df["p_val"].nunique() < 2:
        return None

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(df[["m_val"]], df["p_val"])
    return model


def _deal_rating(diff: float) -> tuple[str, str]:
    if diff > 3000:
        return "GREAT DEAL", "green"
    if diff > 500:
        return "GOOD DEAL", "teal"
    if diff < -3000:
        return "OVERPRICED", "red"
    return "FAIR PRICE", "gray"


# --- Routes ---

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Sudbury Car Scout API"}


@app.get("/cars")
def get_listings(
    keyword: str = Query(default="", max_length=100),
    min_price: int = Query(default=0, ge=0),
    max_price: int = Query(default=0, ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, price, mileage, link FROM cars ORDER BY created_at DESC;"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    cars = [
        {"id": r[0], "title": r[1], "price": r[2], "mileage": r[3], "link": r[4]}
        for r in rows
    ]

    # Keyword filter
    if keyword:
        kw = keyword.lower()
        cars = [c for c in cars if kw in c["title"].lower()]

    # Price filter
    if min_price > 0 or max_price > 0:
        filtered = []
        for car in cars:
            try:
                p = _parse_price(car["price"])
                if min_price > 0 and p < min_price:
                    continue
                if max_price > 0 and p > max_price:
                    continue
                filtered.append(car)
            except (ValueError, KeyError):
                pass
        cars = filtered

    total = len(cars)

    # Pagination
    offset = (page - 1) * limit
    cars = cars[offset : offset + limit]

    # ML deal rating
    model = analyze_market(cars)
    if model:
        for car in cars:
            try:
                m_val = _parse_mileage(car["mileage"])
                p_val = _parse_price(car["price"])
                fair_price = model.predict(pd.DataFrame([[m_val]], columns=["m_val"]))[0]
                diff = fair_price - p_val
                car["deal_rating"], car["deal_color"] = _deal_rating(diff)
            except (ValueError, KeyError, TypeError) as exc:
                logger.warning("Skipping deal analysis for '%s': %s", car.get("title"), exc)
                car.setdefault("deal_rating", "N/A")
                car.setdefault("deal_color", "gray")
    else:
        for car in cars:
            car.setdefault("deal_rating", "N/A")
            car.setdefault("deal_color", "gray")

    return {"cars": cars, "total": total, "page": page, "limit": limit}


@app.get("/stats")
def get_stats():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT price, mileage FROM cars;")
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return {
            "total_listings": 0,
            "avg_price": None,
            "median_price": None,
            "avg_mileage": None,
            "price_range": {"min": None, "max": None},
        }

    prices, mileages = [], []
    for price_raw, mileage_raw in rows:
        try:
            prices.append(_parse_price(price_raw))
        except (ValueError, AttributeError):
            pass
        try:
            mileages.append(_parse_mileage(mileage_raw))
        except (ValueError, AttributeError):
            pass

    df_p = pd.Series(prices)
    df_m = pd.Series(mileages)

    return {
        "total_listings": len(rows),
        "avg_price": round(df_p.mean(), 2) if not df_p.empty else None,
        "median_price": round(df_p.median(), 2) if not df_p.empty else None,
        "avg_mileage": round(df_m.mean(), 2) if not df_m.empty else None,
        "price_range": {
            "min": int(df_p.min()) if not df_p.empty else None,
            "max": int(df_p.max()) if not df_p.empty else None,
        },
    }


@app.post("/alert", status_code=201)
def create_alert(alert: Alert, x_forwarded_for: str = None):
    client_id = x_forwarded_for or "default"
    _check_rate_limit(client_id)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO price_alerts (email, target_price, keyword) VALUES (%s, %s, %s)",
            (alert.email, alert.target_price, alert.keyword),
        )
        conn.commit()
    except psycopg2.Error as exc:
        conn.rollback()
        logger.error("Failed to create alert: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save alert.")
    finally:
        conn.close()

    return {"status": "success", "message": "Alert created. You will be notified when a match appears."}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
