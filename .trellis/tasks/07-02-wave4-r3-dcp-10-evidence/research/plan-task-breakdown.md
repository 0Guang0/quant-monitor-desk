# Plan Task Breakdown — R3-DCP-10

## Overview

Wave 4 R3-DCP-10 closes **one** Layer5 factual evidence vertical slice with real Tier A fetch provenance (mootdx bar → security_bar_1d → Layer5 foundation/lineage).

## Architecture Decisions

- **ADR-031:** P0 anchor + provenance field mapping (schema_hash via source_dataset_ids)
- Reuse DCP-05 mootdx incremental path; no new migration
- Extend `bundle_layer5_provenance` (additive); avoid SourceProvenance schema break

## Task List

| ID | Description | AC | Verification | Dependencies | Files likely touched | Scope |
| --- | --- | --- | --- | --- | --- | --- |
| S00 | Execute boot | validate-execute-boot | task.py | — | jsonl only | S |
| S01 | Provenance bridge | unit test GREEN | pytest bridge | S00 | `evidence_bundle.py`, `layer5_evidence/provenance.py`, test | M |
| S02 | Mootdx e2e | e2e GREEN | pytest e2e | S01 | e2e test, maybe orchestrator hook read bundle path | M |
| S03 | Ledger close | 待修复清单 G5 | doc + pytest -q | S02 | `docs/quality/待修复清单.md` | S |

## Checkpoints

1. S01 unit — provenance map matches bundle
2. S02 e2e — no staged placeholders
3. S03 — ACC G5 subset + full pytest

## Risks

| Risk | Mitigation |
| --- | --- |
| Orchestrator 不暴露 bundle 路径 | e2e 从 raw_root 读 `cn_market_evidence.json`（与 incremental 同 layout） |
| schema_hash 无一等字段 | ADR-031 dataset id 编码 |
| 与 DCP-07/08 并行冲突 | 仅 touch layer5_evidence + normalizers + tests |

## Open Questions

- None — P0 竖切已在 plan-boot 定案（mootdx / sh.600519）
