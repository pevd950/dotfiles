---
name: postgres-migrations
description: Plan, write, review, and validate PostgreSQL schema and data migrations safely. Use when adding tables, changing columns, indexes, constraints, backfills, rollbacks, or deploy sequencing.
---

# PostgreSQL Migrations

## What this skill does
- Guides safe PostgreSQL schema and data migrations from planning through validation.
- Helps avoid migrations that only work on empty local databases but are risky against real data.
- Keeps deploy sequencing, locking, rollback behavior, and data-volume assumptions explicit.

## When to use it
- Trigger phrases: "migration", "Postgres migration", "schema change", "add column", "drop column", "backfill", "index", "constraint", "Goose", "rollback".
- Use when creating, modifying, or reviewing PostgreSQL migrations or app changes that require coordinated database rollout.

## Default stance
- Inspect the repository's migration tool and nearby migrations before writing a new migration.
- Prefer additive, reversible changes first. Split risky destructive changes into later cleanup migrations.
- Treat lock time, table size, and deploy ordering as part of the migration design.
- Validate apply and rollback locally when the repository supports rollback.

## Workflow

### 1. Classify the change
Identify the migration type:
- additive table or column
- destructive drop or rename
- data backfill
- index change
- constraint change
- type change
- enum/value-domain change
- large-table rewrite risk
- app-code compatibility change

Capture:
- affected tables, columns, indexes, constraints, and queries
- expected data volume
- whether old and new app versions must both work during deploy
- whether rollback must preserve data
- whether the migration can run inside one transaction

### 2. Choose deploy pattern
Prefer expand/contract when compatibility or data volume matters:
1. Expand: add new nullable columns/tables/indexes without breaking old code.
2. Backfill: migrate data in a bounded, repeatable way.
3. Switch: deploy app reads/writes to the new shape.
4. Contract: remove old columns/tables only after the new path is proven.

Use a single migration only when the change is small, reversible, and safe for the deployment model.

### 3. Write the migration
- Follow existing filename, ordering, transaction, and comment conventions.
- Include both `Up` and `Down` where possible.
- If rollback is intentionally irreversible or lossy, document why in the migration and handoff.
- Use `IF EXISTS` / `IF NOT EXISTS` only when it matches repo style and does not hide real drift.
- Avoid unbounded full-table rewrites for large tables unless the risk is accepted.
- For indexes, consider concurrent creation when supported and compatible with the migration tool's transaction behavior.
- For constraints on large tables, consider staged validation patterns where supported.
- For data backfills, use deterministic transformations and bounded batches when needed.

### 4. Review safety risks
Check:
- lock duration and transaction scope
- table rewrites
- long-running updates
- foreign key and index coverage
- nullable vs non-null transitions
- default values that rewrite existing rows
- rollback data loss
- app compatibility with old and new schema
- migration ordering relative to app deploys

### 5. Validate locally
Run the repository's migration commands. When supported:
1. Apply the migration.
2. Inspect resulting schema and indexes.
3. Run affected tests.
4. Roll back the migration.
5. Re-apply the migration.
6. Run a focused smoke or query check for affected behavior.

If rollback is not supported or unsafe, state that explicitly and validate forward-only behavior.

### 6. Final handoff
Include:
- migration file(s)
- schema/data changes made
- compatibility and deploy-order assumptions
- validation commands and results
- rollback behavior
- lock/data-volume risks
- follow-up cleanup migration if using expand/contract

## Review Checklist
- Migration matches the repository's established migration tool and style.
- `Up` and `Down` are present or irreversible behavior is documented.
- Destructive changes are split from compatibility changes when needed.
- Large-table or long-lock risks are identified.
- Index and constraint changes match actual query/validation needs.
- Data migrations are deterministic and bounded when table size matters.
- Local apply/rollback/re-apply validation was run when possible.
- App code compatibility during deploy is understood.
