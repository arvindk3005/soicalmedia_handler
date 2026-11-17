import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")
os.environ["JWT_SECRET"] = "test-secret"
from fastapi.testclient import TestClient
from app.main import app

def test_full_demo_flow():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        token = client.post("/api/auth/register", json={"name":"Demo User","email":"demo@example.com","password":"password123"}).json()["access_token"]
        headers={"Authorization": f"Bearer {token}"}
        assert client.post("/api/posts", headers=headers, json={"content":"Excited to share our product launch!","platform":"linkedin","impressions":100,"engagement":15}).status_code == 200
        assert len(client.get("/api/posts", headers=headers).json()) == 1
        result=client.post("/api/analysis", headers=headers, json={"content":"Excited to share our product launch!","platform":"linkedin"})
        assert result.status_code == 200 and result.json()["provider"] == "demo"

def test_rejects_unauthenticated_requests():
    with TestClient(app) as client: assert client.get("/api/posts").status_code == 401
