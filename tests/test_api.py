from fastapi.testclient import TestClient
from api import app 

client = TestClient(app)

def test_health_check():
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
    assert response.json() == {"status": "success"}