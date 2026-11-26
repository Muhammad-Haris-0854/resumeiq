# ADR-004 — Payment provider abstraction

**Status:** accepted · **Date:** 2026-11-26

## Context
Gateway availability depends on the target market and the operator's entity. Hardcoding Stripe
before that is confirmed risks rework, and card availability is limited in some markets.

## Decision
Define `PaymentProvider` (create_checkout, create_portal, cancel, verify_webhook, parse_event).
Ship two adapters: `mock` (fully functional locally, deterministic webhook payloads, no network)
and `stripe` (real Checkout Sessions and signature verification, activated by configuration).
The active provider is chosen by `PAYMENT_PROVIDER`.

## Consequences
- The whole subscription lifecycle is testable offline.
- Switching to Stripe, Paddle or a local gateway touches one module.
- Entitlements never read the frontend: they derive from `subscriptions` written by a verified
  webhook.
