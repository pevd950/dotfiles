# Shared context hub routing

1. **Candidate identity.** Take the active host from `AGENT_HOST_ALIAS`, falling back to the local hostname. Treat it as unverified.
2. **Resolve the hub** from ignored local routing or an explicit link: `AGENT_SHARED_CONTEXT_URL`, or the legacy `CRAFT_SHARED_MEMORY_URL`, which is always a Craft-backed route. If both are set and name different roots, routing is ambiguous. With neither set, one fallback is allowed: an exact-title lookup for `Shared Agent Context` in an already-authorized private knowledge provider, accepted only when exactly one result matches and its account or space, owner and scope can be validated.
3. **Provider.** Load the provider's own skill and use its access, write and read-back rules. Private IDs, URLs, host topology and account details stay in private routing, out of this tracked skill.
4. **Validate identity** before reading subject context or writing. The hub's `Routing Directory` (or an equivalent such as `Host Snapshot`) lists one entry per host with a canonical alias and any accepted hostname aliases. The trimmed candidate must match exactly one alias, case-insensitively.
5. **Read narrowly** for the relevant subject, prefer an existing entry over a new one, and verify the fact at its canonical source when practical.
6. **Write** the subject, applicable host or scope, reviewed date, the durable fact or decision, why another host needs it, and the canonical source or verification method. Update in place and prune stale facts. Re-read the target once immediately before writing; if it changed since you planned the edit, merge deliberately instead of overwriting.
7. **Read back** the changed entry once and confirm the result before reporting success.

If routing is missing or ambiguous, the directory is absent, or the identity is unset, unknown or matches more than one host, the hub is unavailable: leave it unread and unmodified, say so, and continue ordinary local work.
