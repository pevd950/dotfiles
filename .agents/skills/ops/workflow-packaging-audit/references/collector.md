# Bounded session collector

`scripts/scan_codex_sessions.py` produces a private, metadata-only index of supported Codex records. It reads native `session_meta.payload` identities and string/object source forms, classic and custom tool calls/results, user messages, and assistant messages. It does not recursively interpret quoted JSON inside messages or tool output as fresh events. Correction, friction and denial signals are candidates for contextual assessment, not verdicts or occurrence counts.

## Scan

Run only for an authorized history review. Supply each approved active/archive root, a source-host label, the current session ID to exclude, and a private output path. Keep host routes and evidence outside tracked files. The output directory must be owned by the current user with mode `0700`; a new directory is created with that mode. Output files use mode `0600`. The CLI does not print evidence to stdout.

```sh
SKILL_DIR="$HOME/.agents/skills/ops/workflow-packaging-audit"
python3 "$SKILL_DIR/scripts/scan_codex_sessions.py" \
  --authorized --source-host example-host \
  --source-root /approved/sessions --source-root /approved/archived_sessions \
  --checkpoint 2026-09-01T00:00:00Z --upper-bound 2026-09-08T00:00:00Z \
  --exclude-session current-session-id \
  --max-files 100 --max-scan-records 10000 --max-bytes 8388608 \
  --max-events 1000 --output /private/audit/index.json
```

The lower bound is exclusive and upper bound inclusive. Selection uses record timestamps, so an old session resumed during the window remains eligible. Calls before the lower bound can supply context for results inside it. Missing timestamps are reported as gaps. The input limits apply across all roots, not separately to each session. Additional positive limits are `--max-line-bytes`, `--max-sessions`, `--max-pending-calls`, and `--max-directory-entries`; run `--help` for defaults. `--max-line-bytes` cannot exceed the shared 1 MiB detail-retrieval ceiling, so every emitted record remains inspectable.

Files are streamed; oversized records stop that file with a gap. A complete EOF-terminated JSON record is accepted even without a newline; an undecodable trailing record remains a gap for the next rescan. Its detail reference remains valid only while the unterminated record still ends at EOF. Identical records across copied/archived files are deduplicated within a session, while source-file provenance is retained. All source gaps, truncation reasons, skipped sidecars, unsupported records and evicted call contexts are reported. A result at the cap can conservatively report truncation even when that cap coincides with EOF.

Repeated identical records within one file retain their occurrence count; copies of those occurrences in other files are collapsed. Opposite message envelopes with the same nonempty text, role and available turn identity are matched one-for-one within one second, without crossing the lower window boundary. This is a mirror heuristic, not proof of recurrence: absent turn identifiers leave ambiguity, and same-envelope repetitions remain separate. Matched mirror references remain available for inspection. Merged events and call/result pairing use timestamp order. Pairing metadata is bounded by scan limits; `--max-pending-calls` applies to unmatched calls, not already completed pairs.

Collector v3 records a canonical JSON digest for each event (and both digests for a mirrored message). Canonicalization sorts object keys and removes serialization whitespace; raw record hashes in detail references still verify the exact bytes. V2 indexes lack this cross-host identity contract and must be recollected for current intake.

The serialized index, including indentation and final newline, is capped at the same 8 MiB accepted by intake. If it exceeds that ceiling, the collector retains a prefix of whole events in session/event order and marks `max_output_bytes`; emitted counters describe only retained events. Pairing and detail references for retained events remain intact. Diagnostic gaps may also be trimmed if they alone exhaust the budget; the truncation marker always prevents a completeness claim or acknowledgment. Roots and fixed metadata that cannot fit even without events/gaps cause a controlled error. This bounds the artifact, not peak collection memory or full-history coverage.

The default index omits prompts, arguments, output text, previews and session titles. It still contains private metadata such as file paths, session identifiers and tool names. Store and share it accordingly. Do not infer success from a text-extracted exit code or classify a denial without inspecting authorization and surrounding context.

Discovery is bounded by the directory-entry limit. The collector then reads candidate files across all roots in descending modification-time order, with deterministic ties. This prioritizes recent writes, including activity appended to old sessions. Modification time is only an ordering hint: no file is excluded because of its name or modification time, and record timestamps still determine inclusion. Copied files with preserved timestamps remain eligible. A content or discovery cap still means partial coverage; recent-first order cannot guarantee all requested activity fits the budget.

## Targeted detail

Save one event's `source_ref` object as private JSON, then request just that record:

```sh
SKILL_DIR="$HOME/.agents/skills/ops/workflow-packaging-audit"
python3 "$SKILL_DIR/scripts/scan_codex_sessions.py" \
  --authorized --source-host example-host \
  --source-root /approved/sessions --source-root /approved/archived_sessions \
  --detail-ref /private/audit/reference.json --detail-max-chars 4000 \
  --output /private/audit/detail.json
```

Use the same root order as the index. The reference binds a relative file path, byte offset, length and SHA-256; changed content, traversal, symlinks, nonregular files and non-record boundaries are rejected. Detail reads at most one 1 MiB record and emits at most 16,000 characters. Follow a result's `call.source_ref` to inspect the paired call, including prior-window context. Detail redacts common credential formats, URLs, email addresses and private keys, but remains private: heuristic redaction cannot remove all sensitive natural-language content and is not publication clearance.

## Optional archive state

For an authorized database read, add `--archive-db /approved/state/state.sqlite --archive-db-root /approved/state` to the scan. Database access is disabled by default and is not needed for detail retrieval. The adapter requires a standalone, quiescent rollback-journal-format snapshot. It reads the bounded file through a symlink-rejecting descriptor, verifies identity, size and change timestamps before and after the read, then deserializes the bytes into private memory. SQLite never receives the source path and cannot create source sidecars, checkpoint or modify source records. No source database copy is written to disk.

Any WAL, shared-memory or journal sidecar (including an empty file or dangling symlink), a WAL-format main-file header, or an observed concurrent change makes metadata unavailable with an explicit gap. Even a cleanly closed WAL database is unsupported; stopping Codex alone does not produce the required snapshot format. This adapter does not create snapshots or claim consistent live database acquisition. Acquiring a current snapshot is separate authorized work. Supply user-controlled directories; metadata checks cannot prove the absence of every concurrent or malicious change.

The supported schema is a physical `threads` table with `id TEXT`, `rollout_path TEXT`, `archived INTEGER`, and `archived_at INTEGER` (Unix seconds). Extra columns are ignored. A fixed allowlisted projection, query authorizer and progress budget bound query work. `--max-archive-bytes` bounds the source read (64 MiB default, plus one byte to detect overflow); `--max-archive-rows` (10,000 default) and `--max-archive-query-steps` (1,000,000 default) bound this adapter separately from JSONL limits. SQLite deserialization support is required; unavailable support is reported as a gap. No arbitrary SQL or extensions are accepted.

Rows currently marked archived whose archive time falls after the checkpoint and through the upper bound select their allowlisted rollout, after its native session identity is verified. This is unioned with record activity selection: older messages in that rollout become reviewable through the same private detail references. Every emitted event labels `selection_reasons` as `record_activity_in_window`, `session_archived_in_window`, or both. Normal JSONL file, byte, record, session and event caps still apply, including exclusions and sidecar filtering.

Missing/invalid archive timestamps, unsafe or missing rollout paths, mismatched identities, unsupported schemas, query limits and unreached selected rollouts are explicit source gaps. `archive_snapshot_freshness_unverified` remains a gap even on a successful read: current state cannot prove freshness of a copied database or recover earlier archive/unarchive transitions. A row currently unarchived cannot prove it was never archived in the window. No complete historical archive coverage is claimed.

## Deferred acceptance

- Fork files containing a child header followed by an inherited parent `session_meta` header remain unsupported: `session_identity_changed` stops that file and marks coverage partial. Matching `forked_from_id`/`parent_thread_id` proves ancestry, but does not define where copied history ends. Supporting child activity safely requires confirming the producer's `subagent_history_start_ordinal` counting and compaction semantics, then testing parent deduplication and child attribution across that boundary. Do not simply accept or ignore the second identity.
- Durable per-session incremental offsets, checkpoint acknowledgment, source rotation/truncation recovery and concurrency-safe state are not implemented. Each invocation rescans the approved roots; no audit checkpoint is advanced by this script.
- The optional adapter selects archive state from a standalone rollback-journal-format snapshot only. Live WAL acquisition, full archive/unarchive history, independently verified snapshot freshness and live-host acceptance remain unimplemented/unverified.
- This is not the central multi-host collector/reviewer. Host transport restrictions, cross-host copied-session reconciliation, inventory/memory ingestion, review persistence and notification remain separate work.
- The index does not replace contextual analysis. User corrections, successful but wasteful operations, expected denials and already-fixed guidance require bounded detail and comparison with current owner assets.

Review readiness applies only to the implemented bounded collector. Do not treat it as a completed collector or deploy it as the central reviewer until the remaining issue acceptance and a bounded manual comparison are reviewed. Synthetic validation lives in `scripts/test_scan_codex_sessions.py`; no live transcripts belong in fixtures.
