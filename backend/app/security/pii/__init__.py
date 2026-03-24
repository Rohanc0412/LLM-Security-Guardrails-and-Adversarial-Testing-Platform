from .models import (
    DetectorSource,
    PIIDetectionResult,
    PIIMatch,
    PIIRedactionResult,
    RedactionRecord,
    RedactionStrategy,
)
from .presidio_detector import PresidioDetector
from .regex_detector import RegexDetector
from .service import PIIService
from .spacy_detector import SpacyDetector


def benchmark_regex(*args, **kwargs):
    from .benchmark import benchmark_regex as _benchmark_regex

    return _benchmark_regex(*args, **kwargs)


def benchmark_service_detect(*args, **kwargs):
    from .benchmark import benchmark_service_detect as _benchmark_service_detect

    return _benchmark_service_detect(*args, **kwargs)


def benchmark_service_redact(*args, **kwargs):
    from .benchmark import benchmark_service_redact as _benchmark_service_redact

    return _benchmark_service_redact(*args, **kwargs)


def run_benchmarks(*args, **kwargs):
    from .benchmark import run_benchmarks as _run_benchmarks

    return _run_benchmarks(*args, **kwargs)


__all__ = [
    "DetectorSource",
    "PIIDetectionResult",
    "PIIMatch",
    "PIIRedactionResult",
    "PIIService",
    "PresidioDetector",
    "RedactionRecord",
    "RedactionStrategy",
    "RegexDetector",
    "SpacyDetector",
    "benchmark_regex",
    "benchmark_service_detect",
    "benchmark_service_redact",
    "run_benchmarks",
]
