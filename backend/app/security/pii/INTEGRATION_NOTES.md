# PII Service Integration Notes

- Import `PIIService` from `backend.app.security.pii`.
- The package is self-contained and does not depend on FastAPI, database code, or Redis.
- `PIIService.detect(text)` returns a `PIIDetectionResult` with normalized matches.
- `PIIService.redact(text, strategy_overrides=None)` returns a `PIIRedactionResult`.
- `PIIService.detect_and_redact(text, strategy_overrides=None)` is a convenience alias for the same redaction flow.
- `spaCy` and `presidio_analyzer` are optional at import time. If the dependencies are absent, those detectors no-op and regex detection remains available.
- For endpoint wiring later, instantiate one `PIIService` once and reuse it so optional NLP models stay lazily cached.
- Strategy overrides accept entity keys such as `EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `IPV4`, `DATE`, `PERSON`, plus optional `DEFAULT`.
