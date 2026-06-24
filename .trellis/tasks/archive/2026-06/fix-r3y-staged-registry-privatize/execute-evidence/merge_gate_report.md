# Merge Gate — fix/r3y-staged-registry-privatize (β-2)

**Branch:** `fix/r3y-staged-registry-privatize`  
**Date:** 2026-06-24  
**Model:** composer-2.5 (adversarial audit re-run)

## Commands

| Command                                                               | Result                       |
| --------------------------------------------------------------------- | ---------------------------- |
| `uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q` | **71 passed**, exit 0        |
| `uv run pytest -q`                                                    | **full suite green**, exit 0 |

## Diff scope (allowed)

| File                                             | Change                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `backend/app/storage/staged_evidence.py`         | Privatize `_register_staged_file_registry_rows`; `__all__`; R3Y metadata-only 注释 |
| `tests/test_raw_store.py`                        | 公开旁路守卫、phase 门禁、生产零引用扫描                                           |
| `tests/test_r3x_ponytail_pilot_prep_bucket_a.py` | import 对齐（略超 MAP，见 AA-03）                                                  |

**Not touched:** `backend/app/ops/**`, `layer4_markets/**`, registry trio.

## §8.4 closure checklist

| Row                                         | Status                                                                       |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `register_staged_file_registry_rows` 私有化 | PASS                                                                         |
| metadata-only 策略注释                      | PASS (`staged_evidence.py` L15–21)                                           |
| staged pilot WriteManager 路径              | PASS (`test_stagedPilot_mockFetchSuccess_usesWriteManagerStagedQualityFlag`) |
| `backend/` 无生产引用旁路符号               | PASS (`test_stagedEvidence_noProductionReferenceToRegistryBypass`)           |
| Registry `R3Y-STAGED-REG-001` 行更新        | **Deferred** — 主会话批处理                                                  |

## Evidence files

- `β2-red.txt`
- `β2-green.txt`
- `adversarial-audit.report.md`
