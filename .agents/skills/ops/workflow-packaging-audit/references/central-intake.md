# Local central intake foundation

`scripts/central_intake.py` accepts explicitly selected local collector index bundles and writes one private run ledger. It performs no SSH, network requests, arbitrary commands, source expansion, review or notification. This is one implementation batch for issue #66, not a complete central runner or a deployment.

Create private owned directories with mode `0700` for the state and each input directory. Every input artifact must be an owned regular file with mode `0600` and a single link. Every path component rejects symlinks: supply canonical paths, including `/private/tmp` rather than the `/tmp` alias on macOS. Keep bundles, manifests and state outside tracked dotfiles. The ledger preserves validated collector metadata, including private root paths and identifiers; it is not suitable for publication. No real history belongs in test fixtures.

A private manifest maps each configured host label to an explicit status and window. An available host also supplies its selected bundle path:

```json
{
  "example-host": {
    "status": "available",
    "path": "/private/example-input/index.json",
    "window": {
      "after": "2026-09-01T00:00:00Z",
      "through": "2026-09-02T00:00:00Z"
    }
  }
}
```

Use `offline` or `unavailable` for a configured host without input. The manifest is the complete explicit host set for that run; the program cannot discover omitted hosts. Windows may differ per host to support offline catch-up. They require explicit timezone-aware lower and upper timestamps. The lower bound is exclusive and the upper bound inclusive.

```sh
SKILL_DIR="$HOME/.agents/skills/ops/workflow-packaging-audit"
python3 "$SKILL_DIR/scripts/central_intake.py" --authorized --state /private/example-state \
  intake --run example-run --manifest /private/example-input/manifest.json
```

The command emits no evidence to stdout. Inspect `ledger.json` privately for the run digest and host outcomes. Each run binds its normalized windows, statuses and exact input byte digests. Repeating the same run and input does not write state; reusing its name with changed input fails. A repaired or caught-up input uses a new run name. Missing, denied or malformed inputs are recorded as `invalid_or_denied`; explicit offline/unavailable status is preserved. A valid zero-event bundle remains distinguishable from these gaps.

Events deduplicate conservatively within a run using session identity, raw record SHA-256 and the occurrence ordinal among equal hashes in that host's ordered events. Identical repetitions remain separate; byte-identical copied events across hosts retain every host/reference provenance. Equivalent records with different bytes do not merge. This is not durable per-session offset reconciliation, and separate runs retain their own evidence.

Intake never advances a checkpoint. A separate acknowledgment names the exact run digest, host and expected previous bound:

```sh
SKILL_DIR="$HOME/.agents/skills/ops/workflow-packaging-audit"
python3 "$SKILL_DIR/scripts/central_intake.py" --authorized --state /private/example-state \
  acknowledge --run example-run --digest DIGEST_FROM_PRIVATE_LEDGER \
  --host example-host --previous 2026-09-01T00:00:00Z
```

Only complete supported collector input with empty gaps/truncation, consistent coverage counters and a matching window can be acknowledged. The first acknowledgment explicitly establishes its baseline with `--previous`; later acknowledgments must match the stored bound. A repeat of the same acknowledgment is idempotent. Offline, denied, malformed and partial hosts cannot advance. This state is named `acknowledged_collector_windows`: it records receipt of bounded collector evidence, not completed review, all-source coverage or persistent source offsets. Bounded rescans can miss late/backdated records. The collector's archive freshness gap prevents acknowledgment when present; absent archive integration still does not establish archive completeness. `all_sources_complete` is always false.

One ledger atomically persists runs and acknowledgments under a nonblocking exclusive local advisory lock. A run-files-plus-checkpoints design would scale further but require a multi-file commit/recovery protocol; the single bounded ledger keeps the initial batch simpler and crash-consistent. Reads are bounded to 8 MiB per input, at most 32 hosts, and 32 MiB for the ledger. Capacity exhaustion fails without rewriting the ledger; automatic pruning/rotation is intentionally absent. Inputs that change during a read are rejected.

Writes use a private temporary file, file fsync, atomic replacement and directory fsync. Failure before replacement preserves the previous ledger; failure after replacement can mean the new state is committed but durability is uncertain. Inspect the private ledger and retry the same identity idempotently. Local advisory locking assumes cooperating writers and an owned local filesystem; distributed locking and hostile concurrent filesystem mutation are outside this batch.

Still deferred: constrained transport and access pilot, authenticated source provenance, full archive history/freshness, memory and inventory ingestion, automation/repository context, targeted expansion orchestration, actual review/findings persistence, notification and shadow comparisons. No live installation, permission changes, credentials, services or schedule cutover are authorized by this script or its tests.
