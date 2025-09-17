import pytest
import requests

def test_health_endpoint():
    response = requests.get('http://localhost:5001/health')
    assert response.status_code == 200
    assert response.json() == {"ok": True}

if __name__ == "__main__":
    test_health_endpoint()
    print("✅ Health endpoint test passed")
