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

The lower bound is exclusive and upper bound inclusive. Selection uses record timestamps, so an old session resumed during the window remains eligible. Calls before the lower bound can supply context for results inside it. Missing timestamps are reported as gaps. The input limits apply across all roots, not separately to each session. Additional positive limits are `--max-line-bytes`, `--max-sessions`, `--max-pending-calls`, and `--max-directory-entries`; run `--help` for defaults.

Files are streamed; oversized records stop that file with a gap. A complete EOF-terminated JSON record is accepted even without a newline; an undecodable trailing record remains a gap for the next rescan. Its detail reference remains valid only while the unterminated record still ends at EOF. Identical records across copied/archived files are deduplicated within a session, while source-file provenance is retained. All source gaps, truncation reasons, skipped sidecars, unsupported records and evicted call contexts are reported. A result at the cap can conservatively report truncation even when that cap coincides with EOF.

Repeated identical records within one file retain their occurrence count; copies of those occurrences in other files are collapsed. Opposite message envelopes with the same nonempty text, role and available turn identity are matched one-for-one within one second, without crossing the lower window boundary. This is a mirror heuristic, not proof of recurrence: absent turn identifiers leave ambiguity, and same-envelope repetitions remain separate. Matched mirror references remain available for inspection. Merged events and call/result pairing use timestamp order. Pairing metadata is bounded by scan limits; `--max-pending-calls` applies to unmatched calls, not already completed pairs.

The default index omits prompts, arguments, output text, previews and session titles. It still contains private metadata such as file paths, session identifiers and tool names. Store and share it accordingly. Do not infer success from a text-extracted exit code or classify a denial without inspecting authorization and surrounding context.

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

## Deferred acceptance

- Durable per-session incremental offsets, checkpoint acknowledgment, source rotation/truncation recovery and concurrency-safe state are not implemented. Each invocation rescans the approved roots; no audit checkpoint is advanced by this script.
- Archive-transition database metadata is not integrated. Newly archived chats with no in-window record activity are not selected by archive time. Treat this coverage as pending, not as proof that archive timestamps do not exist.
- This is not the central multi-host collector/reviewer. Host transport restrictions, cross-host copied-session reconciliation, inventory/memory ingestion, review persistence and notification remain separate work.
- The index does not replace contextual analysis. User corrections, successful but wasteful operations, expected denials and already-fixed guidance require bounded detail and comparison with current owner assets.

Review readiness applies only to the implemented bounded collector. Do not treat it as a completed collector or deploy it as the central reviewer until the remaining issue acceptance and a bounded manual comparison are reviewed. Synthetic validation lives in `scripts/test_scan_codex_sessions.py`; no live transcripts belong in fixtures.
