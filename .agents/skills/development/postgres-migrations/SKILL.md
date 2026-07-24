---
name: postgres-migrations
description: Plan, write, review, and validate PostgreSQL schema and data migrations safely. Use when adding tables, changing columns, indexes, constraints, backfills, rollbacks, or deploy sequencing.
---

# PostgreSQL Migrations

A migration that only works on an empty local database is not done. Treat lock time, table size, deploy ordering, and rollback behavior as part of the design. Inspect the repo's migration tool and nearby migrations before writing.

## Deploy pattern

Prefer expand/contract whenever compatibility or data volume matters:

1. **Expand:** add nullable columns, tables, and indexes without breaking old code.
2. **Backfill:** deterministic, bounded, repeatable batches.
3. **Switch:** deploy app reads/writes to the new shape.
4. **Contract:** remove the old shape only after the new path is proven — as a later cleanup migration.

A single migration is fine only when the change is small, reversible, and safe for the deployment model.

## Writing rules

- Follow existing filename, ordering, transaction, and comment conventions; include `Up` and `Down`, or document why rollback is irreversible or lossy.
- `IF EXISTS` / `IF NOT EXISTS` only when it matches repo style and does not hide real drift.
- No unbounded full-table rewrites on large tables without accepted risk; watch for defaults and non-null transitions that rewrite existing rows.
- Consider concurrent index creation and staged constraint validation where the migration tool's transaction behavior allows.

## Validate locally

Apply → inspect resulting schema and indexes → run affected tests → roll back → re-apply → focused smoke or query check. If rollback is unsupported or unsafe, say so explicitly and validate forward-only.

## Review checklist

- Matches the repository's migration tool and style.
- Lock duration, transaction scope, and table-rewrite risk identified.
- Destructive changes split from compatibility changes when needed.
- Index and constraint changes match actual query and validation needs.
- Backfills deterministic and bounded where table size matters.
- Old and new app versions both work through the deploy window; migration order relative to app deploys is explicit.
- Apply/rollback/re-apply validation run when possible.
