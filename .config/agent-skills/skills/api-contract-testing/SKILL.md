---
name: api-contract-testing
description: Validate backend API changes end-to-end. Use when adding or changing HTTP endpoints, request/response contracts, auth behavior, generated docs, API tests, or client-facing DTOs.
---

# API Contract Testing

## What this skill does
- Turns API changes into verified contracts instead of implementation-only patches.
- Adds or updates comprehensive tests for request shape, response shape, status codes, auth behavior, side effects, and error envelopes.
- Runs the backend locally and validates representative requests against the real server after automated tests pass.

## When to use it
- Trigger phrases: "add endpoint", "API change", "contract test", "request schema", "response schema", "run the server locally", "validate endpoint behavior".
- Use when changing HTTP handlers, DTOs, routes, auth/session behavior, generated API docs, client-facing response fields, or black-box API tests.

## Default stance
- Contract behavior is user-visible product behavior. Verify it at the HTTP boundary, not only inside services.
- Prefer repo-native test layers and Make targets over new test infrastructure.
- Keep coverage practical and high-signal: happy path, required validation failures, auth/authorization, missing resources, and important side effects first.
- Do not generate Postman collections unless the user explicitly asks for Postman.

## Workflow

### 1. Identify the contract
- Method, route, auth/session requirements, content type, request body, query params, path params, and relevant headers.
- Success response status, response DTO fields, optional/null behavior, pagination/filtering/sorting semantics, and side effects.
- Error response status codes and response body shape for invalid input, unauthenticated, unauthorized, not found, conflicts, provider failures, and rate limits when relevant.
- Backward-compatibility impact for existing iOS/backend clients. If a breaking change is intentional, call it out explicitly.

### 2. Check current repo patterns
- Read nearby handlers, route registration, service methods, repository code, and tests before adding new patterns.
- Search for existing contract/API tests for the same feature family.
- Check generated docs or schemas if this endpoint is documented.
- Reuse existing auth helpers, fixtures, test users, database setup, and response assertion helpers.

### 3. Add or update tests
Choose the narrowest useful set, then expand only where contract risk justifies it.

- Unit or handler tests: request parsing, validation, status codes, and error mapping.
- Service/repository tests: persistence, authorization boundaries, side effects, and edge cases that are hard to express through HTTP.
- Integration tests: database-backed behavior and multi-step flows.
- API contract tests: black-box HTTP behavior that client code depends on.
- Streaming/SSE tests: event shape, lifecycle events, error events, flush behavior, and cancellation semantics when the endpoint streams.
- Generated docs/schema tests: only when the endpoint participates in generated docs or client contracts.

### 4. Validate automatically
- Run the most focused test package first.
- Then run the broader repo target that matches the changed surface.
- Prefer documented Make targets from the repository root. In Plato AI, likely candidates are `make go-test`, `make go-integration`, `make api-test-fast`, and any endpoint-specific integration commands documented in `AGENTS.md`, `tests/AGENTS.md`, or the Makefile.

### 5. Validate against a local server
- Start the backend with the repo-supported local workflow, usually `make dev` for the full stack or the documented host-only server target when dependencies are already available.
- Inspect live request/server logs while exercising the endpoint so validation includes both client-visible behavior and backend-side handling. Confirm the expected route, status, auth identity, request IDs, structured errors, and side effects are logged as intended, and that no unexpected panics, retries, noisy warnings, or leaked sensitive fields appear.
- Exercise representative requests against the real HTTP endpoint:
  - happy path
  - invalid input
  - unauthenticated or unauthorized request
  - not found or conflict path when applicable
  - pagination/filtering edge when applicable
  - streaming lifecycle when applicable
- Use existing scripts or fixtures when available. Avoid inventing ad hoc secrets or credentials.

### 6. Final handoff
- Report the endpoint contract that changed.
- List automated tests added or updated.
- List local-server scenarios exercised, observed results, and any live request/server log evidence inspected.
- Call out docs/generated artifacts updated or intentionally left unchanged.
- Call out any unsupported edge cases or follow-up coverage that should be tracked separately.

## Review Checklist
- Request parsing rejects malformed, missing, and type-invalid inputs with actionable errors.
- Response fields match the intended DTO contract, including omitted/null fields.
- Auth and authorization behavior is explicitly covered.
- Persistence side effects are verified where the endpoint writes data.
- Error mapping is stable and does not leak internals.
- Tests do not depend on order, wall-clock flakiness, or undeclared external services.
- Local-server validation proves the route is wired, not only that lower-level code compiles.
- Live logs were inspected for expected request handling and absence of unexpected backend errors or sensitive data leaks.
