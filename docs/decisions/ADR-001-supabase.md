# ADR-001 — Supabase as the backend-as-a-service layer

**Status:** accepted · **Date:** 2026-11-26

## Context
We need auth (email, OAuth, verification, recovery), a relational store, private file storage,
and row-level isolation for a multi-tenant SaaS, built by a small team on a student budget.

## Decision
Use Supabase for auth, Postgres, Storage and RLS. Keep all business logic in FastAPI so the
compute layer stays portable.

## Consequences
- Fast delivery of auth and storage with battle-tested primitives.
- RLS gives defence in depth at the database.
- The API must scope every query itself, because it uses the service role and bypasses RLS.
- Migrating off Supabase later means re-implementing auth and storage adapters, but not the
  domain logic.
