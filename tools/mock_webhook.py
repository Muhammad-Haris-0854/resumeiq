#!/usr/bin/env python3
"""Send a signed webhook event to the local mock payment provider.

Usage:
    python tools/mock_webhook.py --user <uuid> --plan pro --type checkout.completed

Reads PAYMENT_WEBHOOK_SECRET and API_BASE_URL from the environment (defaults match
`docker compose up`). This exists so the subscription lifecycle is testable locally without a
real gateway; it is not part of the deployed app.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.request
import uuid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True, help="Supabase user id (uuid)")
    parser.add_argument("--plan", default="pro", choices=["pro", "premium"])
    parser.add_argument("--interval", default="month", choices=["month", "year"])
    parser.add_argument(
        "--type",
        default="checkout.completed",
        choices=["checkout.completed", "subscription.renewed", "subscription.canceled", "payment.failed"],
    )
    parser.add_argument("--amount", type=int, default=1200)
    args = parser.parse_args()

    secret = os.environ.get("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret").encode()
    base = os.environ.get("API_BASE_URL", "http://localhost:8000")

    body = {
        "type": args.type,
        "user_id": args.user,
        "plan_code": args.plan,
        "interval": args.interval,
        "amount_cents": args.amount,
        "subscription_id": f"mock_sub_{uuid.uuid4().hex[:12]}",
        "transaction_id": f"mock_tx_{uuid.uuid4().hex[:12]}",
    }
    payload = json.dumps(body).encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()

    request = urllib.request.Request(
        f"{base}/v1/billing/webhook/mock",
        data=payload,
        headers={"Content-Type": "application/json", "X-Signature": signature},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        print(response.status, response.read().decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
