# Phase A 批次汇总

> 更新：2026-06-24 — Phase A 已合并至 `debt/test-hygiene/integration`；merge gate **PASS**

## 结论

- **全桶 pytest 绿**：各桶桶内验证均 0 failed（G 桶 3 skipped 为 DuckDB/network 预期）
- **注释未改**：全部 agent 声明未修改 docstring/注释
- **deletion candidates**：目前各桶均为 `candidates: []` 或空（符合 §3 禁止删清单）
- **ponytail 模式**：去重复 setup/helper、顶栏 import、共享 `PROJECT_ROOT`/contract_gate_support；**无**为性能 mock 网络或删断言
- **实质性对齐**：L1 补 schema 断言 + 1 条 observation happy-path；DS 记录 `test_userAuthRequired_*` 命名漂移

## 各桶要点

| 桶   | 用例规模         | 改动规模          | 备注                        |
| ---- | ---------------- | ----------------- | --------------------------- |
| SMK  | 1                | 复用 `wm`         | 最小 smoke                  |
| G    | 150 (147+3 skip) | 9 文件 −15 行     | gate/network 门控未动       |
| LOOP | 73               | 6 文件 −6 行      | loop/catalog 断言未弱化     |
| OPS  | 63+1 skip        | 3 文件            | subprocess fail-closed 保留 |
| L1   | 153              | 6 文件 −17 净     | 补覆盖缺口                  |
| L23  | 111              | 5 文件 −66 行     | ResourceGuard/lineage 保留  |
| VAL  | 126              | 5 文件 −67 行     | DuckDB 真实路径保留         |
| AUD  | 69               | 5 文件 −90 行     | §3.5 评估无删候选           |
| DS   | 211              | 9+support −106 行 | 未 mock live/network        |

## Phase B 候选（baseline durations）

1. `test_sync_orchestrator.py`（~2.3s×2）
2. `test_audit_remediation.py`（~2.4s）
3. `test_batch_d_orchestration_flow.py`（~1.9s）
4. `test_ingestion_validation_migration.py`（多项 ~1.0–1.4s）

## 下一步

- ~~MERGE-C：integration 分支~~ ✅ 已完成
- ~~Phase B perf~~ ✅ 见 `phaseB-perf-value-checklist.md`、`phaseB-pytest-durations.txt`
- Phase C deletion：各桶 candidates 均为空
- 可选：integration → master PR / push
