---
name: api-contract-testing
description: Validate backend API changes end-to-end. Use when adding or changing HTTP endpoints, request/response contracts, auth behavior, generated docs, API tests, or client-facing DTOs.
---

# API Contract Testing

Contract behavior is user-visible product behavior: verify it at the HTTP boundary, not only inside services. Prefer repo-native test layers and Make targets. Do not generate Postman collections unless explicitly asked.

## Workflow

1. **Pin the contract.** Method, route, auth/session requirements, request shape, success status and DTO fields (including optional/null behavior), pagination/filter/sort semantics, side effects, and error status/body for invalid input, unauthenticated, unauthorized, not found, conflict, provider failure, and rate limits when relevant. Call out any intentional breaking change for existing clients.
2. **Match repo patterns.** Reuse existing auth helpers, fixtures, test users, and assertion helpers; check for existing contract tests in the same feature family and for generated docs or schemas.
3. **Add tests at the narrowest useful layers.** Handler tests for parsing, validation, and status mapping; service or repository tests for persistence, authorization boundaries, and side effects; integration tests for database-backed flows; black-box contract tests for behavior clients depend on; streaming/SSE tests for event shape, lifecycle, errors, flush, and cancellation; docs/schema tests only when the endpoint participates in generated contracts.
4. **Run** the focused package first, then the documented repo target for the changed surface.
5. **Validate against a local server** (usually `make dev` or the documented host-only target). Exercise happy path, invalid input, unauthenticated/unauthorized, not-found or conflict, pagination edges, and streaming lifecycle as applicable — while watching live server logs for the expected route, status, auth identity, structured errors, and the absence of panics, noisy retries, or leaked sensitive fields. This proves the route is wired, not just that lower layers compile. Use existing scripts and fixtures; never invent ad hoc secrets.

## Handoff

Report the contract that changed, tests added or updated, local-server scenarios exercised with observed log evidence, docs or generated artifacts updated or deliberately unchanged, and uncovered edges worth tracking separately.
