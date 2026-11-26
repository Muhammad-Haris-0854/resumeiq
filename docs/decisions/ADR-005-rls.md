# ADR-005 — RLS as defence in depth

**Status:** accepted · **Date:** 2026-11-26

## Context
The API connects with the service-role key, which bypasses RLS. It would be easy to assume RLS
is protecting reads that it never sees.

## Decision
Enable RLS on every table and write policies anyway, and additionally scope every repository
query by `user_id` from the verified token. Tests cover both layers.

## Consequences
- A bug in one layer does not become a data breach.
- Any future direct-from-client query (dashboard reads via `supabase-js`) is already safe.
