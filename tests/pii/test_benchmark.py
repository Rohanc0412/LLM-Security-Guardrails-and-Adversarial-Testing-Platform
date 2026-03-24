from __future__ import annotations

from backend.app.security.pii.benchmark import run_benchmarks


def test_run_benchmarks_reports_detect_and_redact_metrics() -> None:
    results = run_benchmarks(texts=["Email jane@example.com"], iterations=1)

    assert "regex_detect" in results
    assert "service_detect_regex_only" in results
    assert "service_redact_regex_only" in results
    assert "service_detect_full_stack" in results
    assert "service_redact_full_stack" in results
    assert results["regex_detect"]["total_operations"] == 1
