from fastapi.testclient import TestClient
import sys
import os

# Add scraper/src to path so we can import api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scraper/src')))

from api import app

client = TestClient(app)

def test_read_main():
    response = client.get("/cars")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_alert_creation():
    response = client.post("/alert", json={
        "email": "test@test.com",
        "target_price": 15000,
        "keyword": "Civic"
    })
    assert response.status_code == 200