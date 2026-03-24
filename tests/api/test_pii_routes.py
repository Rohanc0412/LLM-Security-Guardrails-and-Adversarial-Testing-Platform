def test_detect_stub_exists_and_returns_not_implemented(client):
    response = client.post("/pii/detect", json={"text": "Contact me at user@example.com"})

    assert response.status_code == 501

    payload = response.json()
    assert payload["status"] == "not_implemented"
    assert payload["matches"] == []
    assert "integration pending" in payload["message"].lower()


def test_redact_stub_exists_and_returns_not_implemented(client):
    response = client.post(
        "/pii/redact",
        json={"text": "Call me at 555-123-4567", "strategy_overrides": {"PHONE": "mask"}},
    )

    assert response.status_code == 501

    payload = response.json()
    assert payload["status"] == "not_implemented"
    assert payload["matches"] == []
    assert payload["redacted_text"] == "Call me at 555-123-4567"
