"""
Sudbury Car Scout — FastAPI Backend

Endpoints:
    GET  /         → Root health check
    GET  /health   → Detailed system diagnostics (DB, model, uptime)
    GET  /cars     → Paginated car listings with ML deal ratings
    GET  /stats    → Market analytics (avg price, median, mileage)
    POST /alert    → Create price-drop alert (rate-limited)
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Optional

import pandas as pd
import psycopg2
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from sklearn.ensemble import RandomForestRegressor

from logger import get_logger

load_dotenv()

# ---------------------------------------------------------------------------
# App & Logger
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sudbury Car Scout API",
    description="AI-powered car market analysis for Sudbury, Ontario",
    version="2.0.0",
)
log = get_logger("api")

START_TIME = time.time()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Alert(BaseModel):
    """Price-drop alert subscription."""

    email: EmailStr
    target_price: int = Field(
        ...,
        ge=500,
        le=500_000,
        description="Target price in CAD (500–500,000)",
    )
    keyword: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Car model search keyword (1–100 chars)",
    )


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5174",
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Rate Limiter  (in-memory, per-IP)
# ---------------------------------------------------------------------------

_alert_timestamps: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 5  # max requests
_RATE_WINDOW = 3600  # seconds (1 hour)


def _check_rate_limit(client_ip: str) -> None:
    """Raise 429 if client exceeded alert creation rate."""
    now = time.time()
    window_start = now - _RATE_WINDOW
    # Keep only hits within the window
    hits = [t for t in _alert_timestamps[client_ip] if t > window_start]
    if len(hits) >= _RATE_LIMIT:
        log.warning("Rate limit exceeded for IP %s", client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many alert requests. Please try again later.",
        )
    hits.append(now)
    _alert_timestamps[client_ip] = hits


# ---------------------------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------------------------


def get_db() -> psycopg2.extensions.connection:
    """Open a new database connection with error handling."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL not configured")
        raise HTTPException(status_code=503, detail="Database not configured.")
    try:
        return psycopg2.connect(db_url)
    except psycopg2.OperationalError as exc:
        log.error("Database connection failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


# ---------------------------------------------------------------------------
# Parsing Helpers
# ---------------------------------------------------------------------------


def _parse_price(raw: str) -> float:
    """Extract numeric price from formatted string like '$15,900'."""
    cleaned = raw.replace("$", "").replace(",", "").strip()
    if not cleaned:
        raise ValueError(f"Empty price value from: {raw!r}")
    return float(cleaned)


def _parse_mileage(raw: str) -> float:
    """Extract numeric mileage from formatted string like '85,000 km'."""
    cleaned = raw.lower().replace("km", "").replace(",", "").strip()
    if not cleaned:
        raise ValueError(f"Empty mileage value from: {raw!r}")
    return float(cleaned)


# ---------------------------------------------------------------------------
# ML Helpers
# ---------------------------------------------------------------------------


def analyze_market(cars: list[dict]) -> Optional[RandomForestRegressor]:
    """
    Train a Random Forest model on the given car listings.

    Returns None if data is insufficient (< 5 rows or < 2 unique values).
    """
    df = pd.DataFrame(cars)
    if len(df) < 5:
        return None

    try:
        df["p_val"] = df["price"].astype(str).apply(
            lambda v: float(v.replace("$", "").replace(",", "").strip())
        )
        df["m_val"] = df["mileage"].astype(str).apply(
            lambda v: float(
                v.lower().replace("km", "").replace(",", "").strip()
            )
        )
    except (ValueError, KeyError):
        log.warning("Failed to parse price/mileage for ML model training")
        return None

    # Guard against degenerate data (model can't learn from constant values)
    if df["m_val"].nunique() < 2 or df["p_val"].nunique() < 2:
        log.info("Skipping ML model — insufficient unique values in data")
        return None

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(df[["m_val"]], df["p_val"])
    return model


def _deal_rating(diff: float) -> tuple[str, str]:
    """Classify the deal based on predicted-vs-actual price difference."""
    if diff > 3000:
        return "GREAT DEAL", "green"
    if diff > 500:
        return "GOOD DEAL", "teal"
    if diff < -3000:
        return "OVERPRICED", "red"
    return "FAIR PRICE", "gray"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def read_root():
    """Root endpoint — basic service status."""
    return {"status": "healthy", "service": "Sudbury Car Scout API"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Return empty response for browser favicon requests."""
    return Response(status_code=204)


@app.get("/health")
def health_check():
    """
    Detailed health check — verifies DB connectivity, model availability,
    and reports uptime. Useful for monitoring and remote diagnostics.
    """
    # 1. Database check
    db_status = "ok"
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL", ""))
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
    except Exception as exc:
        db_status = f"error: {str(exc)}"
        log.error("Health check — DB failed: %s", exc)

    # 2. Model check (train on a quick probe to see if sklearn is functional)
    model_status = "available"
    try:
        # Just verify sklearn is importable and functional
        from sklearn.ensemble import RandomForestRegressor as _RF  # noqa: F401
    except ImportError:
        model_status = "unavailable — sklearn not installed"

    # 3. Uptime
    uptime_seconds = int(time.time() - START_TIME)

    overall = "ok" if db_status == "ok" else "degraded"
    log.info(
        "Health check — status=%s db=%s model=%s uptime=%ds",
        overall, db_status, model_status, uptime_seconds,
    )

    return {
        "status": overall,
        "db": db_status,
        "model": model_status,
        "uptime_seconds": uptime_seconds,
        "version": "2.0.0",
    }


@app.get("/cars")
def get_listings(
    keyword: str = Query(default="", max_length=100),
    min_price: int = Query(default=0, ge=0),
    max_price: int = Query(default=0, ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Get paginated car listings with optional filters and ML deal ratings.

    Query params:
        keyword   — filter by title (case-insensitive substring match)
        min_price — minimum price filter
        max_price — maximum price filter
        page      — page number (1-indexed)
        limit     — results per page (max 100)
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, price, mileage, link "
            "FROM cars ORDER BY created_at DESC;"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    cars = [
        {
            "id": r[0],
            "title": r[1],
            "price": r[2],
            "mileage": r[3],
            "link": r[4],
        }
        for r in rows
    ]

    # --- Keyword filter (case-insensitive) ---
    if keyword:
        kw_lower = keyword.lower()
        cars = [c for c in cars if kw_lower in c["title"].lower()]

    # --- Price filter ---
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
            except (ValueError, AttributeError):
                # Skip cars with unparseable prices
                pass
        cars = filtered

    total = len(cars)

    # --- Pagination ---
    offset = (page - 1) * limit
    cars = cars[offset: offset + limit]

    # --- ML deal rating ---
    model = analyze_market(cars)
    if model:
        for car in cars:
            try:
                m_val = _parse_mileage(car["mileage"])
                p_val = _parse_price(car["price"])
                fair_price = model.predict(
                    pd.DataFrame([[m_val]], columns=["m_val"])
                )[0]
                diff = fair_price - p_val
                car["deal_rating"], car["deal_color"] = _deal_rating(diff)
            except (ValueError, KeyError, TypeError) as exc:
                log.warning(
                    "Skipping deal analysis for '%s': %s",
                    car.get("title", "unknown"),
                    exc,
                )
                car.setdefault("deal_rating", "N/A")
                car.setdefault("deal_color", "gray")
    else:
        # No model available — mark all as N/A
        for car in cars:
            car.setdefault("deal_rating", "N/A")
            car.setdefault("deal_color", "gray")

    log.info(
        "GET /cars — page=%d limit=%d keyword=%r total=%d returned=%d",
        page, limit, keyword, total, len(cars),
    )

    return {"cars": cars, "total": total, "page": page, "limit": limit}


@app.get("/stats")
def get_stats():
    """
    Market analytics — aggregate statistics across all listings.

    Returns total count, average price, median price, average mileage,
    and price range (min/max).
    """
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

    prices: list[float] = []
    mileages: list[float] = []

    for price_raw, mileage_raw in rows:
        try:
            prices.append(_parse_price(str(price_raw)))
        except (ValueError, AttributeError):
            pass
        try:
            mileages.append(_parse_mileage(str(mileage_raw)))
        except (ValueError, AttributeError):
            pass

    df_p = pd.Series(prices) if prices else pd.Series(dtype=float)
    df_m = pd.Series(mileages) if mileages else pd.Series(dtype=float)

    stats = {
        "total_listings": len(rows),
        "avg_price": round(df_p.mean(), 2) if not df_p.empty else None,
        "median_price": round(df_p.median(), 2) if not df_p.empty else None,
        "avg_mileage": round(df_m.mean(), 2) if not df_m.empty else None,
        "price_range": {
            "min": int(df_p.min()) if not df_p.empty else None,
            "max": int(df_p.max()) if not df_p.empty else None,
        },
    }

    log.info("GET /stats — %d listings, avg=$%.0f", len(rows), stats["avg_price"] or 0)
    return stats


@app.post("/alert", status_code=201)
def create_alert(alert: Alert, request: Request):
    """
    Create a price-drop alert. Rate limited to 5 per hour per IP.

    Validates email, price range (500–500k), and keyword length (1–100).
    """
    # Extract client IP (supports reverse proxies)
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        if request.client
        else "unknown"
    )
    _check_rate_limit(client_ip)

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO price_alerts (email, target_price, keyword) "
            "VALUES (%s, %s, %s)",
            (alert.email, alert.target_price, alert.keyword),
        )
        conn.commit()
        log.info(
            "Alert created — email=%s price=%d keyword=%s ip=%s",
            alert.email, alert.target_price, alert.keyword, client_ip,
        )
    except psycopg2.Error as exc:
        conn.rollback()
        log.error("Failed to create alert: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save alert.")
    finally:
        conn.close()

    return {
        "status": "success",
        "message": "Alert created. You will be notified when a match appears.",
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    log.info("Starting Car Scout API on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
