# ADR-003 — Deterministic scoring with bounded AI enrichment

**Status:** accepted · **Date:** 2026-11-26

## Context
An LLM asked for "a score out of 100" is non-reproducible, unexplainable, and can be talked
into inflating a resume. Users must be able to trust and act on a score.

## Decision
Compute every measurable dimension in Python from explicit inputs (keyword coverage against the
domain taxonomy, section presence, bullet metrics, spelling/grammar hit counts, ATS layout
rules). The LLM contributes only qualitative observations that are schema-validated and mapped
to bounded adjustments (max ±8 points on content quality, ±5 on experience relevance).

## Consequences
- Same input, same score: tests can assert exact numbers.
- Every score can show its inputs, satisfying FR-7.4.
- Weights are configurable by admins and validated to sum to 100.
