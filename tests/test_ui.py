from fastapi.testclient import TestClient

from app.main import app


def test_ui_page_returns_200():
    client = TestClient(app)
    response = client.get('/ui')
    assert response.status_code == 200
