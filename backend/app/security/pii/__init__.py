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
]
