# R3Y-AUD-08 — Go/no-go gate（v2 协调者合成）

**Result:** WARN → **`WARN_ALLOW_WITH_CONTROLS`**

> 基准：`master` @ `61436a51` · 只读审计 · 2026-06-23  
> 输入：v2 模块 agent `R3Y-AUD-01…07`（非 v0 monolithic）

---

## Issue 汇总

| Issue                    | Result | 一句话                                                                |
| ------------------------ | ------ | --------------------------------------------------------------------- |
| R3Y-AUD-01 closed claims | WARN   | PROMPT_15 73 项闭合证据链薄；SYNC-001 adapter 旁路仍存                |
| R3Y-AUD-02 source route  | WARN   | 主链 fail-closed；sync `adapter=` 旁路 HIGH                           |
| R3Y-AUD-03 write gate    | WARN   | clean write 主路径闭合；`register_staged_file_registry_rows` API 残留 |
| R3Y-AUD-04 staged pilot  | WARN   | 无 production 旁路；`proof_status=VERIFIED` 语义过宽                  |
| R3Y-AUD-05 lineage       | WARN   | L2 staged 可信；VR/fetch_log 绑定未闭合                               |
| R3Y-AUD-06 registry      | WARN   | 三 registry 主路径 OK；LINEAGE defer 缺行 + Plan 索引滞后             |
| R3Y-AUD-07 test quality  | WARN   | 伞测偏结构性；runtime-strong 比例不足                                 |

**无 BLOCK 级 issue** — 主路径修复已进入 runtime，残留为旁路/证据/测试深度。

---

## 跨模块 HIGH 主题（v2 共识）

1. **Sync `adapter=` 旁路**（AUD-01 F-02 · AUD-02 HIGH · AUD-03 reconcile WARN）— `run_incremental`/`run_backfill`/`reconcile` 可跳过 `DataSourceService` + route/capability。
2. **`proof_status=VERIFIED` 假安全**（AUD-04 HIGH）— DB 存在即 VERIFIED，hash/row-count 失败仍可能标 VERIFIED。
3. **`ADV-R3X-LINEAGE-001` registry 缺登记**（AUD-06 HIGH）— Batch 4/5 defer 未入三 registry SSOT。
4. **PROMPT_15 证据链不完整**（AUD-01 F-01 · AUD-07）— 18 伞测 vs 73 声称闭合；无 execute `*-green.txt`。

---

## 必跑 pytest 汇总（v2 各 issue 已执行）

| 套件                                                        | 通过    |
| ----------------------------------------------------------- | ------- |
| `test_r3x_residual_open_items_closure.py`                   | 18      |
| `test_datasource_service.py` + route + capabilities         | 31      |
| `test_db_validation_gate.py` + write_manager + raw_store    | 54      |
| `test_staged_pilot.py`                                      | 26      |
| `test_layer2_sensor_loader.py` + layer5_evidence_foundation | 38      |
| `test_round3_audit_registry_alignment.py`                   | 18      |
| **合计（去重前加总）**                                      | **185** |

`scripts/check_doc_links.py` — v0 已 OK；v2 未复跑（非阻塞）。

---

## Gate 决策

### 最终 gate

**`WARN_ALLOW_WITH_CONTROLS`**

### PROMPT_19 staged pilot v2

**允许，受控扩样** — 条件：

- 保持 `R3-B2.75-REQ2-EM` **DEFERRED**；不得声称 production-live
- 扩样前确认无生产 CLI 使用 sync `adapter=`
- closeout 不得仅引用 `proof_status=VERIFIED`；须附 hash/row-count 明细或修复 AUD-04 HIGH
- 授权链 + sandbox WriteManager 路径维持现状

### PROMPT_20 read-only data health v1

**允许，受控实现** — 条件：

- 只读；无 clean write / migration / live fetch
- health CLI 不得经 `adapter=` 或 `register_staged_file_registry_rows` 旁路
- 与 registry 对齐：刷新 Plan 索引前不得将 `R2-RISK-3`/`R3-AUDIT-DEF-03` 当 OPEN

### Sandbox clean-write rehearsal

**允许，非 production DB** — 条件：

- 须经 WriteManager + ValidationGate
- metadata-only file_registry 策略须文档化（AUD-03 WARN）
- Layer2 lineage 合成 ID 不得冒充 VR 绑定（AUD-05 WARN）

---

## 建议控件（下一修复波次，非本 audit 分支）

| 优先级 | 控件                                              | 来源         |
| ------ | ------------------------------------------------- | ------------ |
| P1     | 生产入口禁止 sync `adapter=`（或 runtime guard）  | AUD-01/02/03 |
| P1     | 修复 `mutation_proof` VERIFIED 语义               | AUD-04       |
| P1     | registry 登记 `ADV-R3X-LINEAGE-001` DEFERRED      | AUD-06       |
| P2     | 退役或私有化 `register_staged_file_registry_rows` | AUD-03       |
| P2     | PROMPT_15 补 execute green.txt + checklist 映射   | AUD-01/07    |
| P2     | 刷新 `UNRESOLVED_ITEM_TASK_COVERAGE` 等 Plan 索引 | AUD-06       |
| P3     | Layer2 VR→lineage 绑定（021+）                    | AUD-05       |

---

## 证据完整性

- AUD-01：`R3Y-AUD-01-closed-claims.md` + `closed-claim-matrix.md` ✓
