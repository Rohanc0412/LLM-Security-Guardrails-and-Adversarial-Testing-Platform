from backend.app.api import pii as pii_api


def test_detect_endpoint_returns_normalized_matches(client):
    pii_api.get_pii_service.cache_clear()

    response = client.post("/pii/detect", json={"text": "Contact jane@example.com for access."})

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["total_matches"] >= 1
    assert "regex" in payload["detectors_run"]

    email_match = next(match for match in payload["matches"] if match["entity_type"] == "EMAIL")
    assert email_match["text"] == "jane@example.com"
    assert email_match["primary_source"] == "regex"
    assert "regex" in email_match["sources"]


def test_redact_endpoint_returns_redacted_output(client):
    pii_api.get_pii_service.cache_clear()

    response = client.post(
        "/pii/redact",
        json={
            "text": "Email jane@example.com for access.",
            "strategy_overrides": {"EMAIL": "partial"},
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["total_matches"] >= 1
    assert payload["redacted_text"] == "Email j***@e******.com for access."
    assert payload["redactions"][0]["entity_type"] == "EMAIL"
    assert payload["redactions"][0]["strategy"] == "partial"


def test_detect_endpoint_returns_503_when_service_initialization_fails(client, monkeypatch):
    def broken_builder():
        raise RuntimeError("service init failed")

    pii_api.get_pii_service.cache_clear()
    monkeypatch.setattr(pii_api, "_build_pii_service", broken_builder)

    response = client.post("/pii/detect", json={"text": "Contact jane@example.com"})

    assert response.status_code == 503
    assert response.json() == {"detail": "PII service unavailable"}

    pii_api.get_pii_service.cache_clear()


def test_redact_endpoint_returns_503_when_service_processing_fails(client):
    class BrokenService:
        def redact(self, text, strategy_overrides=None):
            raise RuntimeError("redaction failed")

    client.app.dependency_overrides[pii_api.get_pii_service] = lambda: BrokenService()

    response = client.post(
        "/pii/redact",
        json={"text": "Contact jane@example.com", "strategy_overrides": {"EMAIL": "mask"}},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "PII redaction failed"}

    client.app.dependency_overrides.clear()
