import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from scraper.src.api import app

client = TestClient(app)

SAMPLE_ROWS = [
    (1, "2019 Honda Civic", "$15,000", "80,000 km", "https://example.com/1"),
    (2, "2020 Toyota Corolla", "$18,500", "45,000 km", "https://example.com/2"),
    (3, "2018 Ford F-150", "$32,000", "110,000 km", "https://example.com/3"),
    (4, "2021 Mazda CX-5", "$27,000", "30,000 km", "https://example.com/4"),
    (5, "2017 Hyundai Elantra", "$11,000", "140,000 km", "https://example.com/5"),
    (6, "2022 Kia Sportage", "$29,500", "20,000 km", "https://example.com/6"),
]


def _make_mock_db(rows=SAMPLE_ROWS):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


# --- Health check ---

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# --- GET /cars ---

def test_get_cars_returns_list():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars")
    assert response.status_code == 200
    body = response.json()
    assert "cars" in body
    assert "total" in body
    assert isinstance(body["cars"], list)


def test_get_cars_has_deal_rating():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars")
    body = response.json()
    for car in body["cars"]:
        assert "deal_rating" in car
        assert "deal_color" in car


def test_get_cars_keyword_filter():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?keyword=civic")
    body = response.json()
    assert all("Civic" in c["title"] or "civic" in c["title"].lower() for c in body["cars"])


def test_get_cars_price_filter():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?max_price=20000")
    body = response.json()
    for car in body["cars"]:
        price = int(car["price"].replace("$", "").replace(",", ""))
        assert price <= 20000


def test_get_cars_pagination():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?page=1&limit=2")
    body = response.json()
    assert len(body["cars"]) <= 2
    assert body["page"] == 1
    assert body["limit"] == 2


def test_get_cars_invalid_page():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?page=0")
    assert response.status_code == 422


def test_get_cars_limit_too_large():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.get("/cars?limit=9999")
    assert response.status_code == 422


def test_get_cars_empty_db():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=[])):
        response = client.get("/cars")
    body = response.json()
    assert body["cars"] == []
    assert body["total"] == 0


# --- GET /stats ---

STATS_ROWS = [(r[2], r[3]) for r in SAMPLE_ROWS]  # (price, mileage) only


def test_get_stats_returns_summary():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=STATS_ROWS)):
        response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total_listings" in body
    assert "avg_price" in body
    assert "median_price" in body
    assert "avg_mileage" in body
    assert "price_range" in body


def test_get_stats_empty_db():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db(rows=[])):
        response = client.get("/stats")
    body = response.json()
    assert body["total_listings"] == 0
    assert body["avg_price"] is None


# --- POST /alert ---

def test_alert_creation_success():
    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        response = client.post(
            "/alert",
            json={"email": "test@example.com", "target_price": 15000, "keyword": "Civic"},
        )
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_alert_rejects_invalid_email():
    response = client.post(
        "/alert",
        json={"email": "not-an-email", "target_price": 15000, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_price_too_low():
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 100, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_price_too_high():
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 999_999, "keyword": "Civic"},
    )
    assert response.status_code == 422


def test_alert_rejects_empty_keyword():
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 15000, "keyword": ""},
    )
    assert response.status_code == 422


def test_alert_rejects_keyword_too_long():
    response = client.post(
        "/alert",
        json={"email": "a@b.com", "target_price": 15000, "keyword": "x" * 101},
    )
    assert response.status_code == 422


def test_alert_rate_limiting():
    from scraper.src.api import _alert_timestamps
    _alert_timestamps.clear()

    with patch("scraper.src.api.get_db", return_value=_make_mock_db()):
        for _ in range(5):
            r = client.post(
                "/alert",
                json={"email": "spam@test.com", "target_price": 15000, "keyword": "Car"},
                headers={"x-forwarded-for": "1.2.3.4"},
            )
        # 6th request must be rate-limited
        r = client.post(
            "/alert",
            json={"email": "spam@test.com", "target_price": 15000, "keyword": "Car"},
            headers={"x-forwarded-for": "1.2.3.4"},
        )
    assert r.status_code == 429

    _alert_timestamps.clear()
