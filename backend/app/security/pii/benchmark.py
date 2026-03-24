from __future__ import annotations

import json
from time import perf_counter

from .regex_detector import RegexDetector


def benchmark_regex(texts: list[str] | None = None, iterations: int = 1000) -> dict[str, float | int]:
    samples = texts or [
        "Email jane.doe@example.com, card 4111 1111 1111 1111, phone (212) 555-0100, IP 192.168.10.4",
        "SSN 123-45-6789 appears next to a backup address of support@example.org on 2025-05-11",
    ]
    detector = RegexDetector()
    start = perf_counter()
    match_count = 0
    for _ in range(iterations):
        for sample in samples:
            match_count += len(detector.detect(sample))
    elapsed = perf_counter() - start
    operations = iterations * len(samples)
    return {
        "iterations": iterations,
        "samples": len(samples),
        "total_operations": operations,
        "total_matches": match_count,
        "elapsed_seconds": round(elapsed, 6),
        "operations_per_second": round(operations / elapsed, 2) if elapsed else 0.0,
    }


if __name__ == "__main__":
    print(json.dumps(benchmark_regex(), indent=2))
