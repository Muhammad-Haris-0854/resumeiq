# ADR-006 — Celery + Redis for background work

**Status:** accepted · **Date:** 2026-11-26

## Context
OCR and LLM calls take seconds to minutes. Blocking an HTTP request would break NFR-1 and
exhaust worker threads.

## Decision
Celery with Redis. Separate `default` and `ai` queues, plus `ai_priority` for Premium.

## Consequences
- The API returns 202 immediately and the client polls.
- Jobs must be idempotent and resumable; each task re-reads state before writing.
- Operationally we now run Redis and worker processes (covered by `docker-compose.yml`).
