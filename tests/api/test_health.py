def test_health_endpoint_returns_application_status(client):
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "LLM Security Guardrails"
    assert payload["environment"] == "test"
    assert payload["dependencies"] == {"database": True, "redis": True}
