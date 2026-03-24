from __future__ import annotations

import argparse
import json
from time import perf_counter
from typing import Callable

from .regex_detector import RegexDetector
from .service import PIIService

DEFAULT_SAMPLES = [
    "Email jane.doe@example.com, card 4111 1111 1111 1111, phone (212) 555-0100, IP 192.168.10.4",
    "SSN 123-45-6789 appears next to a backup address of support@example.org on 2025-05-11",
    "Reach Alice on June 14, 2025 at alice@example.net or 212-555-0199 for follow-up.",
]
DEFAULT_STRATEGY_OVERRIDES = {
    "EMAIL": "partial",
    "PHONE": "partial",
    "SSN": "hash",
    "CREDIT_CARD": "mask",
    "DEFAULT": "mask",
}


def _summarize_timing(
    label: str,
    iterations: int,
    sample_count: int,
    elapsed: float,
    total_matches: int,
) -> dict[str, float | int | str]:
    operations = iterations * sample_count
    return {
        "label": label,
        "iterations": iterations,
        "samples": sample_count,
        "total_operations": operations,
        "total_matches": total_matches,
        "elapsed_seconds": round(elapsed, 6),
        "operations_per_second": round(operations / elapsed, 2) if elapsed else 0.0,
    }


def _benchmark_operation(
    label: str,
    texts: list[str],
    iterations: int,
    operation: Callable[[str], int],
) -> dict[str, float | int | str]:
    for sample in texts:
        operation(sample)

    start = perf_counter()
    total_matches = 0
    for _ in range(iterations):
        for sample in texts:
            total_matches += operation(sample)
    elapsed = perf_counter() - start
    return _summarize_timing(
        label=label,
        iterations=iterations,
        sample_count=len(texts),
        elapsed=elapsed,
        total_matches=total_matches,
    )


def benchmark_regex(texts: list[str] | None = None, iterations: int = 1000) -> dict[str, float | int | str]:
    samples = list(texts or DEFAULT_SAMPLES)
    detector = RegexDetector()
    return _benchmark_operation(
        label="regex_detect",
        texts=samples,
        iterations=iterations,
        operation=lambda sample: len(detector.detect(sample)),
    )


def benchmark_service_detect(
    texts: list[str] | None = None,
    iterations: int = 1000,
    *,
    enable_spacy: bool = True,
    enable_presidio: bool = True,
) -> dict[str, float | int | str | list[str] | dict[str, bool]]:
    samples = list(texts or DEFAULT_SAMPLES)
    service = PIIService(enable_spacy=enable_spacy, enable_presidio=enable_presidio)
    last_detectors_run: list[str] = []

    def operation(sample: str) -> int:
        nonlocal last_detectors_run
        result = service.detect(sample)
        last_detectors_run = [source.value for source in result.detectors_run]
        return result.total_matches

    metrics = _benchmark_operation(
        label="service_detect",
        texts=samples,
        iterations=iterations,
        operation=operation,
    )
    metrics["configured_detectors"] = {
        "regex": True,
        "spacy": enable_spacy,
        "presidio": enable_presidio,
    }
    metrics["last_detectors_run"] = last_detectors_run
    return metrics


def benchmark_service_redact(
    texts: list[str] | None = None,
    iterations: int = 1000,
    *,
    enable_spacy: bool = True,
    enable_presidio: bool = True,
    strategy_overrides: dict[str, str] | None = None,
) -> dict[str, float | int | str | dict[str, bool]]:
    samples = list(texts or DEFAULT_SAMPLES)
    service = PIIService(enable_spacy=enable_spacy, enable_presidio=enable_presidio)
    overrides = strategy_overrides or DEFAULT_STRATEGY_OVERRIDES

    metrics = _benchmark_operation(
        label="service_redact",
        texts=samples,
        iterations=iterations,
        operation=lambda sample: len(service.redact(sample, strategy_overrides=overrides).matches),
    )
    metrics["configured_detectors"] = {
        "regex": True,
        "spacy": enable_spacy,
        "presidio": enable_presidio,
    }
    return metrics


def run_benchmarks(texts: list[str] | None = None, iterations: int = 1000) -> dict[str, object]:
    samples = list(texts or DEFAULT_SAMPLES)
    return {
        "samples": samples,
        "regex_detect": benchmark_regex(samples, iterations=iterations),
        "service_detect_regex_only": benchmark_service_detect(
            samples,
            iterations=iterations,
            enable_spacy=False,
            enable_presidio=False,
        ),
        "service_redact_regex_only": benchmark_service_redact(
            samples,
            iterations=iterations,
            enable_spacy=False,
            enable_presidio=False,
        ),
        "service_detect_full_stack": benchmark_service_detect(samples, iterations=iterations),
        "service_redact_full_stack": benchmark_service_redact(samples, iterations=iterations),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark PII detect() and redact() paths.")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of iterations to run for each sample.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(json.dumps(run_benchmarks(iterations=args.iterations), indent=2))
