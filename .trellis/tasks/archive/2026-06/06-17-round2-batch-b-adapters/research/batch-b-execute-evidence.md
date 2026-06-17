# Batch B Execute 证据汇总

> Execute 阶段 §8 RED/GREEN 与 §10 验收命令输出摘要

## §8.0

- **RED:** exit 4 — `tests/test_adapter_skeletons.py` 不存在
- **GREEN:** exit 0 — `1 test collected` (`test_adapterPackage_importable`)

## §8.1

- **RED:** exit 1 — `ModuleNotFoundError: fetch_port`
- **GREEN:** exit 0 — 8 passed（success + FileRegistry + 6× parametrized PortError）

## §8.2–§8.5

- **GREEN:** `pytest tests/test_adapter_skeletons.py -v` → **25 passed**（初版 18 + 补测 7）

## §8.6 / §10

| 命令 | 结果 |
|------|------|
| `pytest -q --cov=backend --cov-fail-under=75` | 200 passed · **93.72%** cov |
| `ruff check .` | All checks passed |
| `python -m compileall backend scripts tests` | exit 0 |
| grep WriteManager in adapters | 无匹配 |
| `init_db` ×2 | applied none (幂等) |
| `QMD_DATA_ROOT=data ci_ingestion_smoke` | ok |
| `QMD_DATA_ROOT=data pytest -q` | 200 passed |
| `node .gitnexus/run.cjs analyze` | 2605 nodes indexed |

## Audit 独立环境（`.audit-sandbox/data`）— 补跑 2026-06-17

| 命令 | 结果 |
|------|------|
| `QMD_DATA_ROOT=.audit-sandbox/data init_db` ×2 | applied none（幂等） |
| `QMD_DATA_ROOT=.audit-sandbox/data ci_ingestion_smoke` | ok · tables fetch_log+source_registry |
| `pytest tests/test_adapter_skeletons.py --basetemp=.audit-sandbox/pytest` | **18 passed** |
| 端到端 `create_adapter` → fetch → 磁盘 raw 抽检 | SUCCESS · 1 raw file @ `.audit-sandbox/data/raw/...` |

> **说明：** Execute §10 用的是 `QMD_DATA_ROOT=data`（repo prod-path），**不是** audit-sandbox。上表为独立环境补验。

## 基线对比

- Plan 冻结基线：**182** collected
- Execute 完成：**207** collected（+25 adapter · 基线 182）
