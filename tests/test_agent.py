def test_agent_requires_auth(client):
    response = client.get("/api/v1/agent/llm-status")

    assert response.status_code == 401


def test_llm_status_with_auth(client, auth_headers):
    response = client.get(
        "/api/v1/agent/llm-status",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "provider" in data
    assert "model" in data
    assert "api_key_configured" in data