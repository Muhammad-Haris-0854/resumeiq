#!/usr/bin/env python3
"""Parse every migration and the seed file with a real PostgreSQL grammar.

Catches syntax errors in CI without needing a database. Semantic checks (constraints, policy
behaviour) still require applying them to a project.
"""

from __future__ import annotations

import glob
import sys

import pglast


def main() -> int:
    paths = sorted(glob.glob("supabase/migrations/*.sql")) + ["supabase/seed.sql"]
    failures = 0
    for path in paths:
        try:
            pglast.parse_sql(open(path, encoding="utf-8").read())
            print(f"ok   {path}")
        except Exception as exc:  # noqa: BLE001 - report every failure, not the first
            failures += 1
            print(f"FAIL {path}: {str(exc)[:300]}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
