# A1 audit-spec — B3V-OPS Contract Drift & Write Modes

| 字段 | 值 |
| ---- | -- |
| 维度 | A1 trellis-check + Trace Authority |
| 任务 | `round3v-contract-drift-write-modes` / B3V-C01 |
| 审阅提交 | `master` @ `e81e430e`（实现 diff 基线 `d62e8dc4..e81e430e`） |
| 分支 | `fix/round3v-contract-drift-write-modes` |
| 模型 | composer-2.5 |
| 日期 | 2026-06-28 |
| **裁决** | **PASS** |

---

## 1. 执行摘要

实现将 `ops_db_inspect_contract.yaml` 提升为 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` 的 SSOT（import 时 YAML loader），`write_contract.yaml` 新增 `implemented_modes` / `reserved_modes` 分栏，并新增 `tests/test_contract_drift_ops_write.py` 五条漂移/parity 测。`WriteManager` 未改；`db_inspector` 保持只读路径。任务卡 §4 forbidden 与 MASTER AC-BOUND 均满足。registry 闭合（`B02-CLOSE-01`）按 Plan 显式 defer 主会话——非 A1 阻断项。

---

## 2. trellis-check 证据（§3.1）

| 检查项 | 结果 | 证据 |
| ------ | ---- | ---- |
| 1. 变更范围 | PASS | `git diff d62e8dc4..e81e430e --name-only`：生产代码仅 `backend/app/ops/db_inspector.py`、`specs/contracts/write_contract.yaml`、`tests/test_contract_drift_ops_write.py`；附带 `tests/test_catalog.yaml`、`docs/generated/docs_specs_index.generated.md`（loop 惯例） |
| 2. 任务工件 | PASS | 已读 `B02_01_contract_drift_and_write_modes.md`、`MASTER.plan.md` §2/§5/§9、`research/source-index.md` §A–§C |
| 3. 包上下文 | PASS（单包 ops/db 接线） | 变更限于 `backend/app/ops` + `specs/contracts` + `tests/`；未触及 ≥3 层跨层链 |
| 4. Spec Quality | PASS | `db_inspector` loader 复用既有 `quote_ident`；无新公共 API；符合 ponytail「删重复字面量」 |
| 5. 项目检查 | PASS | `uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py tests/test_write_manager.py -q` → **57 passed, 1 skipped**, exit 0（2026-06-28 本 agent 重跑）；`uv run ruff check backend/app/ops/db_inspector.py tests/test_contract_drift_ops_write.py` → All checks passed |
| 6. 跨层 | SKIP | 仅 ops 只读 + 契约 YAML；无 Storage→API→UI 链变更 |
| 7. manifest diff | PASS | `check.jsonl` 仅 AUDIT.plan 索引；`implement.jsonl` 点名文件均在 diff 允许集或 Plan 工件内；**无** `write_manager.py` / migration / registry 三件套 |

---

## 3. Trace Authority 核对（AUDIT.plan §0.1）

| 条目 | 结果 | 证据 |
| ---- | ---- | ---- |
| 原始任务卡 | PASS | `B02_01_contract_drift_and_write_modes.md` §2–§8 → MASTER §2 AC-OPS-DRIFT / AC-WRITE-SPLIT / AC-WRITE-RESERVED / AC-BOUND；`B02-CLOSE-01` → MASTER §3.2 explicit defer |
| task README / manifest | PASS | `BATCH_3V_TASK_CARD_MANIFEST.md` C01；`research/source-index.md` §A AC 映射完整 |
| unresolved coverage | PASS（defer） | `R3-AUDIT-DEF-01` 技术证据由 loader+漂移测闭合；registry 行仍 DEFERRED——MASTER §3.2 + `repair-evidence/registry-ready.md` 主会话收口 |
| round map | PASS | Round 3V.1 · B3V-OPS；`research/original-plan-trace.md` 六切片中 CLOSE 排除 |
| source-index | PASS | `research/source-index.md` §B manifest 与 `implement.jsonl` 一致；§C 六类 `[x]` |
| omission-check | PASS | `research/playbook-32-path-audit.md` 路径对照无遗漏 allowed 文件 |
| integration-ledger | PASS | `research/integration-ledger.md` 与 `context_pack.json` 路由一致 |

---

## 4. 任务卡 / AC 对抗对照

### VR-OPS-001（db_inspector + 契约 SSOT）

| 要求 | 结果 | 证据 |
| ---- | ---- | ---- |
| YAML 为 key_tables / deferred SSOT | PASS | `db_inspector.py:15–55` — `_load_ops_inspect_contract()` + `_key_tables_from_contract` / `_deferred_mapping_from_contract` |
| 漂移测全量 key_tables + deferred | PASS | `test_contract_drift_ops_write.py:31–50` 全量 tuple 相等（非子集） |
| db-inspect 只读、无 mutation、无网络 | PASS | `rg INSERT\|writer\(` → **0**；`_populate_db_contents` 使用 `cm.reader()`（`:188–191`）；`mode: read_only`（`:93`） |

### VR-WRITE-001（write modes 分栏 + parity）

| 要求 | 结果 | 证据 |
| ---- | ---- | ---- |
| implemented / reserved 分栏 | PASS | `write_contract.yaml:3–9` |
| implemented == SUPPORTED_MODES | PASS | `test_writeContract_implementedModes_matchWriteManager`；`WriteManager.SUPPORTED_MODES` = `append_only`, `upsert_by_pk`（`write_manager.py:51`） |
| reserved == UNSUPPORTED_MODES | PASS | `test_writeContract_reservedModes_matchUnsupportedModes`（`:64–72`） |
| reserved 稳定拒绝、无写副作用 | PASS | `test_writeManager_reservedModes_rejectWithoutWrite`；`write_manager.py:394–400` 约定 `ValueError` 文案 |
| 未实现 reserved runtime | PASS | `write_manager.py` **不在** `d62e8dc4..e81e430e` diff 中 |

### Forbidden scope（§4）

| 禁止项 | 结果 | 证据 |
| ------ | ---- | ---- |
| manual_patch / replace_partition / schema_migration 实现 | PASS | 仅契约 enum + 早拒；无新写路径 |
| production clean-write 权限 | PASS | 无 `write_manager` / gate 变更 |
| reserved 模式 API/CLI | PASS | 无新 surface |
| DB 写 / migration | PASS | diff 无 `backend/app/db/migrations/**`；inspect 只读 |

---

## 5. GitNexus

| 动作 | 结果 |
| ---- | ---- |
| `query("db_inspector contract loader KEY_TABLES")` | 命中 `DbInspector`、`test_ops_db_inspector.py`、`interface_probe` 等 inspect 消费方 |
| `impact(KEY_TABLES, upstream)` | **LOW**，`impactedCount: 0`（loader 替换字面量，import 契约不变） |
| `context(_load_ops_inspect_contract)` | 索引未收录（新符号）；以 `git diff` + 调用方 grep 补全：`mutation_proof`、`live_pilot_phase1`、`interface_probe` 仍 `import KEY_TABLES` |

---

## 6. DOUBT（对抗性 scope / Red Flags）

| 问题 | 结论 |
| ---- | ---- |
| 原始 scope / Red Flags 是否进入 MASTER/AUDIT？ | 是——`MASTER.plan.md` §1.5 停止条件、§3.2 out/defer、`AUDIT.plan.md` §1 A3/A7/A8 |
| Plan 外文件是否 scope creep？ | `test_catalog.yaml` + `docs/generated/*` 为新测文件 loop 维护——**NON-BLOCKING**，符合 Trellis loop 惯例 |
| registry 未闭合是否 FAIL？ | 否——任务卡 `B02-CLOSE-01` + MASTER 显式排除 agent 闭合 |
| 漂移测能否抓「只改 YAML」？ | SSOT 设计下 loader 与 YAML 同源；测的是 **loader 规范化逻辑** 与 raw YAML 一致（见 §7 PO-02） |

---

## 7. 计划外发现

> 已对抗搜索：契约 enum 并集、WriteManager bypass、db_inspector mutation、registry diff、production-live 措辞、`FUTURE_PHASE_KEY_TABLES`、Windows basetemp。

| ID | 级别 | 发现 | 处置 |
| -- | ---- | ---- | ---- |
| PO-01 | NON-BLOCKING | `FUTURE_PHASE_KEY_TABLES`（`db_inspector.py:58`）仍为硬编码 frozenset | **wont-fix** — 非 VR-OPS key_tables SSOT；Batch 5 前瞻清单 |
| PO-02 | INFO | 漂移测语义从「硬编码常量 vs YAML」转为「loader 规范化 vs raw YAML」 | **by design** — YAML SSOT 后仍锁定 `_deferred_mapping_from_contract` 逻辑 |
| PO-03 | INFO | `AUDIT.plan` 指定 `--basetemp=.audit-sandbox/pytest` 在 Windows 上 DuckDB `.write.lock` 导致 teardown PermissionError | **环境** — 默认 pytest tmp 下 57 passed；非实现缺陷 |

**BLOCKING：0**

---

## 8. A1 checklist

- [x] trellis-check 步骤 1–7 有证据
- [x] diff vs audit/check manifest
- [x] Trace Authority 已继承或 explicit defer
- [x] 无 Plan omission（地图/轮次/索引）
- [x] GitNexus 已查（query + impact）

---

## 9. 裁决

**PASS** — B3V-OPS 实现符合任务卡 `VR-OPS-001` / `VR-WRITE-001` 技术证据要求；scope 无越界；漂移/parity/reserved 测试与本 agent 重跑 pytest 均绿。计划外 3 项均为 NON-BLOCKING/INFO，不阻断 merge 或 finish-work（待 A2–A8 与主会话 registry 收口）。
