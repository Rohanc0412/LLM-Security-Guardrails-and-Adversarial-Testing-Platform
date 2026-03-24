
# AGENTS.md

## Project

LLM Security Guardrails

## Active scope

Phase 1 only

## Phase 1 goals

- Set up project infrastructure
- Build a production-grade PII detection and redaction engine
- Implement core backend wiring and minimal schema setup
- Expose PII detection and redaction API endpoints
- Add comprehensive tests
- Run a first performance and profiling pass

## Phase 1 deliverables

- Docker environment configured
- PostgreSQL schema deployed
- Redis available for local development
- FastAPI app boots locally
- Health endpoint works
- PII Redaction Engine complete
  - Pattern-based detection using regex
  - spaCy-based NER detection
  - Microsoft Presidio integration
  - Hybrid redaction strategies:
    - mask
    - hash
    - partial
    - synthetic
  - Performance optimization for typical prompts
  - Unit tests and edge case handling
- PII API endpoints:
  - POST /pii/detect
  - POST /pii/redact
- Comprehensive tests
- Benchmark or profiling helper

## Technology expectations for Phase 1

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy async
- Alembic
- Redis
- pytest
- spaCy
- Microsoft Presidio

## Architecture rules

- Keep PII logic separate from API route handlers
- Route handlers should call a service layer
- Keep code production-oriented, simple, and testable
- Prefer small focused modules over large files
- Avoid broad refactors during worker tasks
- If a needed change is outside your allowed scope, do not edit it. Report it instead.

## Worker ownership

### Chat A: Orchestrator and integrator

Owns:

- architecture decisions
- file ownership decisions
- merge order
- final API integration
- final hardening
- benchmark pass
- acceptance checklist

### Chat B: Infra and backend foundation

Allowed:

- docker-compose.yml
- .env.example
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/api/**
- backend/app/models/**
- backend/app/core/**
- alembic/**
- tests/api/**
- tests/conftest.py
- dependency files if needed for backend bootstrapping

Forbidden:

- backend/app/security/pii/**
- tests/pii/**
- frontend/**
- dashboard/**

### Chat C: PII engine

Allowed:

- backend/app/security/pii/**
- tests/pii/**
- dependency files only if needed for the PII engine

Forbidden:

- docker-compose.yml
- .env.example
- backend/app/main.py
- backend/app/config.py
- backend/app/database.py
- backend/app/api/**
- backend/app/models/**
- alembic/**
- tests/api/**
- frontend/**
- dashboard/**

## Phase 1 technical requirements

### Infra requirements

- Docker Compose with API, PostgreSQL, Redis
- Async database session setup
- Alembic configuration and runnable migrations
- Health endpoint
- PII route stubs before integration
- Basic API test scaffolding

### PII requirements

- Regex pattern library with compilation and caching
- PII categories should include at least:
  - SSN
  - credit card
  - email
  - phone
  - IPv4
  - date if practical
  - room for passport or driver license patterns if useful
- spaCy wrapper with lazy loading
- Presidio wrapper with normalized output
- Shared result schema
- Merge and dedup logic for overlapping spans
- Context-aware hooks for false positives such as May, June, Will
- Redaction strategies:
  - MASK
  - HASH
  - PARTIAL
  - SYNTHETIC
- Service API:
  - detect(text)
  - redact(text, strategy_overrides=None)
  - detect_and_redact(text, strategy_overrides=None)

## Testing expectations

- Add broad unit coverage
- Include edge cases:
  - empty input
  - multiline text
  - overlapping spans
  - duplicate detections across detectors
  - already-redacted text
  - malformed values
  - deterministic hashing behavior
  - synthetic replacements
  - false-positive prone examples
- Add API tests after integration
- Aim for strong Phase 1 coverage with many focused tests

## Performance expectations

- Regex path should be the fast path
- Compile and cache regex patterns
- Avoid repeated heavy model initialization
- Add a benchmark or profiling helper
- Report likely bottlenecks clearly
- Phase 1 target is low latency for typical prompts

## Output contract for every Codex task

At the end of each task, return exactly:

1. Summary of changes
2. Files changed
3. Commands to run
4. Blockers or open issues
5. Suggested next step

## Merge policy

- Chat B and Chat C must not edit the same files
- Chat B creates API stubs and infra only
- Chat C creates the PII package only
- Chat A performs final integration after both branches are merged

## Acceptance checklist for Phase 1

Phase 1 is complete when:

- Docker Compose runs API, PostgreSQL, Redis
- FastAPI app starts cleanly
- Alembic migrations run
- /health works
- /pii/detect works
- /pii/redact works
- Regex detection works for common PII
- spaCy integration works
- Presidio integration works
- Redaction supports mask, hash, partial, synthetic
- Overlapping spans are handled safely
- Tests pass
- Benchmark or profiling helper exists
- A measured latency baseline exists for typical prompts
