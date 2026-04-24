"""
Comprehensive test suite for Sudbury Car Scout API.

Tests cover:
    - Root health check
    - /health endpoint
    - GET /cars (basic, keyword filter, price filter, pagination, edge cases)
    - GET /stats (normal, empty DB)
    - POST /alert (success, validation, rate limiting)
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from scraper.src.api import app, _alert_timestamps

client = TestClient(app)

# ─── Test Data ────────────────────────────────────────────────────────────────

SAMPLE_ROWS = [
    (1, "2019 Honda Civic", "$15,000", "80,000 km", "https://example.com/1"),
    (2, "2020 Toyota Corolla", "$18,500", "45,000 km", "https://example.com/2"),
    (3, "2018 Ford F-150", "$32,000", "110,000 km", "https://example.com/3"),
    (4, "2021 Mazda CX-5", "$27,000", "30,000 km", "https://example.com/4"),
    (5, "2017 Hyundai Elantra", "$11,000", "140,000 km", "https://example.com/5"),
    (6, "2022 Kia Sportage", "$29,500", "20,000 km", "https://example.com/6"),
]


def _make_mock_db(rows=None):
    """Create a mock database connection that returns specified rows."""
    if rows is None:
        rows = SAMPLE_ROWS
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


# ─── Root / Health Check ─────────────────────────────────────────────────────


def test_root_health_check():
    """GET / should return service status."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "Sudbury Car Scout API"


def test_health_endpoint_returns_diagnostics():
    """GET /health should return db, model, and uptime info."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "db" in body
    assert "model" in body
    assert "uptime_seconds" in body
    assert isinstance(body["uptime_seconds"], int)
    assert body["uptime_seconds"] >= 0


# ─── GET /cars ────────────────────────────────────────────────────────────────


def test_get_cars_returns_paginated_response():
    """GET /cars should return cars list with pagination metadata."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars")
    assert response.status_code == 200
    body = response.json()
    assert "cars" in body
    assert "total" in body
    assert "page" in body
    assert "limit" in body
    assert isinstance(body["cars"], list)


def test_get_cars_has_deal_rating():
    """Every car should have deal_rating and deal_color fields."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars")
    body = response.json()
    for car in body["cars"]:
        assert "deal_rating" in car, f"Car {car.get('title')} missing deal_rating"
        assert "deal_color" in car, f"Car {car.get('title')} missing deal_color"


def test_get_cars_keyword_filter():
    """Keyword filter should only return matching cars."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?keyword=civic")
    body = response.json()
    assert all(
        "civic" in c["title"].lower()
        for c in body["cars"]
    ), "Keyword filter should only return matching titles"


def test_get_cars_keyword_filter_no_match():
    """Keyword filter with no matches should return empty list."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?keyword=lamborghini")
    body = response.json()
    assert body["cars"] == []
    assert body["total"] == 0


def test_get_cars_price_filter_max():
    """Max price filter should exclude expensive cars."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?max_price=20000")
    body = response.json()
    for car in body["cars"]:
        price = int(car["price"].replace("$", "").replace(",", ""))
        assert price <= 20000, f"Car {car['title']} price ${price} exceeds max $20000"


def test_get_cars_price_filter_min():
    """Min price filter should exclude cheap cars."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?min_price=25000")
    body = response.json()
    for car in body["cars"]:
        price = int(car["price"].replace("$", "").replace(",", ""))
        assert price >= 25000, f"Car {car['title']} price ${price} below min $25000"


def test_get_cars_pagination():
    """Pagination should limit results per page."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?page=1&limit=2")
    body = response.json()
    assert len(body["cars"]) <= 2
    assert body["page"] == 1
    assert body["limit"] == 2


def test_get_cars_pagination_page_2():
    """Page 2 should return different results than page 1."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        r1 = client.get("/cars?page=1&limit=2")
        r2 = client.get("/cars?page=2&limit=2")
    page1_ids = [c["id"] for c in r1.json()["cars"]]
    page2_ids = [c["id"] for c in r2.json()["cars"]]
    assert page1_ids != page2_ids, "Page 2 should have different cars than page 1"


def test_get_cars_invalid_page_zero():
    """Page 0 should return 422 validation error."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?page=0")
    assert response.status_code == 422


def test_get_cars_limit_too_large():
    """Limit > 100 should return 422 validation error."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?limit=9999")
    assert response.status_code == 422


def test_get_cars_empty_db():
    """Empty database should return empty list with total 0."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=[])):
        response = client.get("/cars")
    body = response.json()
    assert body["cars"] == []
    assert body["total"] == 0


# ─── GET /stats ───────────────────────────────────────────────────────────────

# Stats endpoint receives (price, mileage) tuples
STATS_ROWS = [(r[2], r[3]) for r in SAMPLE_ROWS]


def test_get_stats_returns_summary():
    """GET /stats should return aggregate market analytics."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=STATS_ROWS)):
        response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total_listings" in body
    assert "avg_price" in body
    assert "median_price" in body
    assert "avg_mileage" in body
    assert "price_range" in body
    assert body["total_listings"] == len(STATS_ROWS)
    assert body["avg_price"] > 0
    assert body["median_price"] > 0


def test_get_stats_empty_db():
    """Empty database should return zeroed stats."""
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=[])):
        response = client.get("/stats")
    body = response.json()
    assert body["total_listings"] == 0
    assert body["avg_price"] is None


# ─── POST /alert ──────────────────────────────────────────────────────────────


def test_alert_creation_success():
    """Valid alert should return 201."""
    _alert_timestamps.clear()
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.post(
            "/alert",
            json={"email": "test@example.com", "target_price": 15000, "keyword": "Civic"},
        )
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_alert_rejects_invalid_email():
    """Invalid email should return 422."""
    response = client.post(
        "/alert",
        json={"email": "not-an-email", "target_price": 15000, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_price_too_low():
    """Price below 500 should return 422."""
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 100, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_price_too_high():
    """Price above 500,000 should return 422."""
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 999_999, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_empty_keyword():
    """Empty keyword should return 422."""
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 15000, "keyword": ""},
    )
    assert response.status_code == 422


def test_alert_rejects_keyword_too_long():
    """Keyword > 100 chars should return 422."""
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 15000, "keyword": "x" * 101},
    )
    assert response.status_code == 422


def test_alert_rate_limiting():
    """6th request from same IP within 1 hour should get 429."""
    _alert_timestamps.clear()

    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        # Send 5 valid requests
        for _ in range(5):
            r = client.post(
                "/alert",
                json={"email": "spam@test.com", "target_price": 15000, "keyword": "Car"},
                headers={"x-forwarded-for": "10.0.0.1"},
            )
            assert r.status_code == 201

        # 6th request should be rate-limited
        r = client.post(
            "/alert",
            json={"email": "spam@test.com", "target_price": 15000, "keyword": "Car"},
            headers={"x-forwarded-for": "10.0.0.1"},
        )
    assert r.status_code == 429

    _alert_timestamps.clear()