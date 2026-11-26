#!/usr/bin/env bash
# Regenerate supabase/setup_all.sql from the migrations and the seed file.
# Run after adding or editing a migration so the one-paste setup stays current.
set -euo pipefail

cd "$(dirname "$0")/.."

OUT="supabase/setup_all.sql"

{
  echo "-- ResumeIQ one-shot setup: schema, policies, storage and seed data."
  echo "-- Paste this whole file into the Supabase SQL editor and run it once on a fresh project."
  echo "-- Generated from supabase/migrations/*.sql + supabase/seed.sql by tools/build_setup_sql.sh."
  echo
  for f in supabase/migrations/*.sql; do
    echo "-- ====================================================================="
    echo "-- $f"
    echo "-- ====================================================================="
    cat "$f"
    echo
  done
  echo "-- ====================================================================="
  echo "-- supabase/seed.sql"
  echo "-- ====================================================================="
  cat supabase/seed.sql
} > "$OUT"

echo "wrote $OUT ($(wc -l < "$OUT") lines)"
