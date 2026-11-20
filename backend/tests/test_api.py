import json
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

os.environ["JWT_SECRET"] = "test-secret-pulsepilot-at-least-32-chars"
os.environ["AI_PROVIDER"] = "gemini"

from backend.app.main import app
from backend.app.core.security import hash_password, verify_password, issue_token, read_token

# In-memory mock storage for MongoDB tests
MOCK_USERS = {}
MOCK_POSTS = []
MOCK_QUERIES = []

SAMPLE_LLM_OUTPUT = {
    "overall_score": 84,
    "executive_summary": (
        "Strong product launch announcement with clear value, though the opening hook "
        "can be sharpened with a concrete metric to boost LinkedIn dwell time."
    ),
    "reach_potential": {
        "score": 82,
        "tier": "High",
        "hook_strength": 76,
        "algorithm_alignment": "Well-suited for LinkedIn feed discussions if paired with a direct question.",
        "virality_drivers": ["Timely AI product launch", "Clear audience relevance"],
        "reach_limiters": ["Generic opening phrase ('Excited to launch')", "No quantitative proof point"],
    },
    "content_value": {
        "score": 86,
        "clarity_score": 90,
        "originality_score": 78,
        "engagement_depth_score": 85,
        "value_proposition": "Introduces an AI analytics capability that helps creators optimize reach.",
        "target_audience_fit": "Social media strategists, founders, and growth marketers.",
        "sentiment": "Inspirational",
    },
    "actionable_improvements": {
        "suggested_hooks": [
            "Most creators guess why a post flops. Here is how to score reach before hitting publish:",
            "We cut post-editing time in half with one change to how we evaluate hooks.",
        ],
        "improvements": [
            {
                "priority": "High",
                "category": "Hook",
                "issue": "Starts with 'Excited to launch', which is overused in LinkedIn feeds.",
                "action": "Open with the core problem your AI analytics feature solves in 12 words or fewer.",
                "expected_impact": "Increases 'See more' click-through rate and early dwell time.",
            },
            {
                "priority": "Medium",
                "category": "Call to Action",
                "issue": "Lacks a closing prompt for comments.",
                "action": "End with a specific question asking readers which metric they struggle with most.",
                "expected_impact": "Drives comment velocity in the first 60 minutes.",
            },
        ],
        "optimized_rewrite": (
            "Most creators guess why a post flops.\n\n"
            "Today we are launching our new AI analytics feature to evaluate reach potential, "
            "content value, and exact edits before you publish.\n\n"
            "Which metric do you find hardest to predict: reach or saves?"
        ),
        "cta_suggestion": "Ask readers which metric they struggle to predict before publishing.",
        "hashtags": ["#SocialMediaStrategy", "#ContentAnalytics", "#AI", "#GrowthMarketing"],
    },
}


def mock_create_user(name, email, password_hash):
    if email in MOCK_USERS:
        return None
    user_id = f"user_{len(MOCK_USERS) + 1}"
    MOCK_USERS[email] = {
        "_id": user_id,
        "name": name,
        "email": email,
        "password_hash": password_hash
    }
    return user_id


def mock_get_user_by_email(email):
    return MOCK_USERS.get(email)


def mock_create_post(user_id, payload):
    post_id = f"post_{len(MOCK_POSTS) + 1}"
    post = {"id": post_id, "user_id": user_id, **payload}
    MOCK_POSTS.append(post)
    return post_id


def mock_list_posts(user_id):
    return [p for p in reversed(MOCK_POSTS) if p.get("user_id") == user_id]


def mock_save_query(user_id, content, platform, provider, model, analysis_result, attachment_id=None):
    qid = f"query_{len(MOCK_QUERIES) + 1}"
    query = {
        "id": qid,
        "user_id": user_id,
        "content": content,
        "platform": platform,
        "provider": provider,
        "model": model,
        "analysis": analysis_result
    }
    MOCK_QUERIES.append(query)
    return qid


def mock_list_queries(user_id, limit=20):
    return [q for q in reversed(MOCK_QUERIES) if q.get("user_id") == user_id][:limit]


def test_health_check():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["service"] == "pulsepilot"


def test_password_hashing_and_token():
    pw = "supersecret123"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

    token = issue_token("user_12345")
    user_id = read_token(token)
    assert user_id == "user_12345"


@patch("backend.app.api.routes.mongodb.create_user", side_effect=mock_create_user)
@patch("backend.app.api.routes.mongodb.get_user_by_email", side_effect=mock_get_user_by_email)
@patch("backend.app.api.routes.mongodb.create_post", side_effect=mock_create_post)
@patch("backend.app.api.routes.mongodb.list_posts", side_effect=mock_list_posts)
@patch("backend.app.api.routes.mongodb.save_query", side_effect=mock_save_query)
@patch("backend.app.api.routes.mongodb.list_queries", side_effect=mock_list_queries)
@patch("backend.app.services.provider.httpx.Client")
def test_full_auth_and_ollama_analysis_flow(
    m_httpx, m_queries, m_save_q, m_list_p, m_create_p, m_get_u, m_create_u
):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": json.dumps(SAMPLE_LLM_OUTPUT)}
    m_httpx.return_value.__enter__.return_value.post.return_value = mock_resp

    with TestClient(app) as client:
        # 1. Register user
        reg_res = client.post("/api/auth/register", json={
            "name": "Jane Developer",
            "email": "jane@example.com",
            "password": "password123"
        })
        assert reg_res.status_code == 200
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Login user
        login_res = client.post("/api/auth/login", json={
            "email": "jane@example.com",
            "password": "password123"
        })
        assert login_res.status_code == 200
        login_token = login_res.json()["access_token"]
        assert read_token(login_token) is not None

        # 3. Create post
        post_res = client.post("/api/posts", headers=headers, json={
            "content": "Excited to launch our new AI analytics feature!",
            "platform": "linkedin",
            "impressions": 500,
            "engagement": 45
        })
        assert post_res.status_code == 200
        assert len(client.get("/api/posts", headers=headers).json()) >= 1

        # 4. Run AI analysis with Ollama provider (mocked HTTP)
        analysis_res = client.post("/api/analysis", headers=headers, json={
            "content": "Excited to launch our new AI analytics feature!",
            "platform": "linkedin",
            "provider": "ollama",
            "target_audience": "Growth marketers",
            "goal": "reach",
        })
        assert analysis_res.status_code == 200
        analysis_data = analysis_res.json()
        assert analysis_data["provider"] == "ollama"
        assert analysis_data["overall_score"] == 84
        assert analysis_data["reach_potential"]["tier"] == "High"
        assert analysis_data["content_value"]["sentiment"] == "Inspirational"
        assert len(analysis_data["actionable_improvements"]["improvements"]) == 2
        assert len(analysis_data["actionable_improvements"]["hashtags"]) == 4

        # 5. Verify query was persisted to MongoDB
        queries_res = client.get("/api/queries", headers=headers)
        assert queries_res.status_code == 200
        queries_list = queries_res.json()
        assert len(queries_list) >= 1
        assert queries_list[0]["content"] == "Excited to launch our new AI analytics feature!"


def test_rejects_demo_provider():
    """Verify 'demo' provider is no longer accepted by the schema."""
    with TestClient(app) as client:
        token = issue_token("user_123")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post("/api/analysis", headers=headers, json={
            "content": "Testing that demo provider is rejected",
            "platform": "linkedin",
            "provider": "demo"
        })
        assert res.status_code == 422


def test_rejects_unauthenticated_requests():
    with TestClient(app) as client:
        assert client.get("/api/posts").status_code == 401
        assert client.get("/api/queries").status_code == 401
        assert client.post("/api/analysis", json={"content": "test", "platform": "x"}).status_code == 401


def test_gemini_missing_api_key_error():
    """Verify informative error message when Gemini API key is missing."""
    with TestClient(app) as client:
        token = issue_token("user_123")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post("/api/analysis", headers=headers, json={
            "content": "Testing Gemini without API key",
            "platform": "linkedin",
            "provider": "gemini"
        })
        assert res.status_code == 400
        assert "Gemini API key is not configured" in res.json()["detail"]


def test_ollama_connection_error_message():
    """Verify informative error message when Ollama is unreachable on localhost."""
    with TestClient(app) as client:
        token = issue_token("user_123")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post("/api/analysis", headers=headers, json={
            "content": "Testing Ollama without local server",
            "platform": "x",
            "provider": "ollama"
        })
        assert res.status_code == 502
        assert "Could not connect to Ollama" in res.json()["detail"]
