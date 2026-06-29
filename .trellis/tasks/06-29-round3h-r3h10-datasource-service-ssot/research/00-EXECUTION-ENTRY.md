# R3H-10 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**（先读本文件，再完成 §5.2 必读，执行中按 §5.3 情境路由）  
> **任务目录：** `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/`  
> **活卡（Wave 级 · 包外）：** `EXTERNAL-INDEX.md` → `R3H_10_DATASOURCE_SERVICE_SSOT.md`（**不移动**，见 §8）  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`

---

## 1. 任务目的 · 价值 · 完成条件（总入口汇总）

本节仅汇总**跨文件**的「为什么做」；切片步骤与验收细节在 `to-issues-slices.md`。

| 维度         | 内容                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------- |
| **目的**     | 闭合 **C2** `DataSourceService` 产品 fetch SSOT；收敛 **E4** staged/live 双轨；登记 **STAGED-PILOT-SSOT** |
| **价值**     | Wave 2 `R3H-08` 24 源 live 产品化要求 Sync / CLI / 探针一律经 service；若 10 不先闭合，08 会重复改入口    |
| **评级**     | `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`                                          |
| **完成条件** | S10-BOOT..CLOSE 全绿 · 全量 `uv run pytest -q` · audit STAGED-PILOT-SSOT=CLOSED · **解锁 R3H-07**         |
| **不在范围** | R3H-08 真网 live · 新 migration · Round4 API · 删 pilot 模块                                              |

**业务目标详述：** 活卡 `R3H_10_DATASOURCE_SERVICE_SSOT.md` §1（路径见 `EXTERNAL-INDEX.md`）

---

## 2. 约束 · 规则 · 铁律（总入口汇总 + 出处）

| 类别                   | 约束                                                               | 详述位置                              |
| ---------------------- | ------------------------------------------------------------------ | ------------------------------------- |
| **架构 ADR**           | 生产 Sync 未传 `datasource_service=` → **fail-closed**             | **ADR-025**（`EXTERNAL-INDEX.md` §A） |
| **参考采纳**           | `参考项目/**` 只读；禁止 runtime import；OpenBB architecture_only  | `reference-adoption-r3h10.md` §0      |
| **护栏 YAML**          | L1/L2/L3 · forbidden_semantics                                     | `reference_adoption_guardrails.yaml`  |
| **Trellis / GitNexus** | Execute gate · 改 service 前 `impact` · commit 前 `detect_changes` | `AGENTS.md`                           |
| **Boundaries Always**  | 每切片后全量 pytest；TDD RED→GREEN                                 | `plan-spec-gap.md` § Boundaries       |
| **Boundaries Never**   | 默认构造 service；pilot 冒充产品 live；runtime 参考树              | 同上 + ADR-025                        |
| **Wave 串行**          | R3H-10 CLOSED 后才允许 R3H-07                                      | Wave1 INDEX §0                        |

---

## 3. 验证命令

```bash
uv run pytest -q                                    # 每切片 GREEN 后
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot  # S10-CLOSE 前
```

证据：`execute-evidence/9.x-red.txt` → `9.x-green.txt`

---

## 4. ADR 索引（本任务绑定）

| ADR                                                                                        | 标题                                                     | 绑定切片   |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------- | ---------- |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync production fail-closed without `datasource_service` | **S10-01** |

---

## 5. 执行包阅读规则

### 5.1 文件地图（每份写什么 — 登记于 `plan-consolidation.md` Skill 对照表）

| 文件                          | Skill 来源                  | 内容摘要                       |
| ----------------------------- | --------------------------- | ------------------------------ |
| `00-EXECUTION-ENTRY.md`       | trellis-plan 5e             | 本路由                         |
| `EXTERNAL-INDEX.md`           | trellis-plan 5e             | 包外 §A/B/C                    |
| `to-issues-slices.md`         | to-issues                   | 垂直切片 · AC · 证据路径       |
| `bypass-baseline-matrix.md`   | to-issues 扩展              | 旁路基线                       |
| `plan-spec-gap.md`            | spec-driven-development     | Spec 六要素（试点文件名）      |
| `plan-task-sizing.md`         | planning-and-task-breakdown | 规模 · CP · 风险（试点文件名） |
| `plan-context-pack.md`        | context-engineering         | 上下文/情境路由（试点文件名）  |
| `plan-doubt-review.md`        | doubt-driven-development    | 对抗审查                       |
| `reference-adoption-r3h10.md` | trellis-research            | 参考采纳调研                   |
| `plan-consolidation.md`       | trellis-plan 5e             | 分流 · 对照表                  |
| `context-closure.md`          | trellis-execute             | Execute E16 upstream/wiring    |
| `gitnexus-execute-summary.md` | trellis-execute             | Phase 0a impact 摘要           |
| `execute-skill-evaluation.md` | trellis-execute             | §12 skill 评估                 |
| `gitnexus-audit-summary.md`   | trellis-execute / Audit     | Phase 7 detect_changes 摘要    |

### 5.2 切片开工前必读（硬门禁）

**每一次**开始新的 S10-xx 切片（含 S10-BOOT）之前，Execute agent **必须已 Read 全文**下列文件，不得跳过：

#### A. `research/` 包内（全部已登记文件 — 见 §5.1）

1. `00-EXECUTION-ENTRY.md` … `gitnexus-audit-summary.md`（**共 14 份**，不含 `plan-boot.md`）

#### B. `EXTERNAL-INDEX.md` §A 所列包外文档（全部）

见 `EXTERNAL-INDEX.md` **§A — 切片开工前必读（外部）**。

#### C. 当前切片节

`to-issues-slices.md` 中**本切片**对应 §（精读，作为本刀 AC）。

```text
开工检查（口头或 execute-evidence 首行声明）：
[ ] research/ 10 份已读
[ ] EXTERNAL-INDEX §A 已读
[ ] 当前 S10-xx § 已读
→ 然后才允许写测试/改代码
```

### 5.3 执行阶段情境路由（遇到 X → 打开 Y）

**含义：** 编码/调试过程中碰到下表情境时，按路由打开对应路径（多为 §C 源码或 §B 文档）。**不**替代 §5.2 开工必读。

| 情境                                                             | 路由                                                                                                                                |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 改 Sync / `run_incremental` / `adapter=` / `datasource_service=` | `EXTERNAL-INDEX` §C → `orchestrator.py` · `runners.py` · **ADR-025** · `to-issues-slices.md` §3                                     |
| 改 `qmd data` / 契约 status / `route-preview`                    | §C → `datasource_service_contract.yaml` · `test_data_cli_contract.py` · `to-issues-slices.md` §4                                    |
| 写 rehearsal 边界 / pilot 文档                                   | §B → `production_live_pilot_policy.md` · `reference-adoption-r3h10.md` §4.2 · §3                                                    |
| 扩旁路负向测 / `interface_probe`                                 | §C → `interface_probe.py` · `bypass-baseline-matrix.md` 行 8 · §4                                                                   |
| 收敛 staged/live `fetch_ports` 双轨                              | §C → `staged_pilot_fetch_ports.py` · `live_pilot_fetch_ports.py` · `datasources/fetch_ports/` · `plan-doubt-review.md` Cycle 2 · §7 |
| 不确定能否删/改 pilot 模块                                       | `to-issues-slices.md` Out of scope · 活卡 §2                                                                                        |
| 参考项目能否抄                                                   | `reference-adoption-r3h10.md` + `reference_adoption_guardrails.yaml`                                                                |
| 改 `DataSourceService` / `fetch` 链                              | GitNexus `impact` + §C `service.py` · `plan-context-pack.md` Level 3                                                                |
| 登记 STAGED-PILOT-SSOT / audit                                   | §B → `round3h_real_data_production_entry_audit.md` · §8 CLOSE                                                                       |
| Trellis freeze / CLOSE                                           | `plan-consolidation.md` · `validate-plan-freeze`                                                                                    |
| Wave 下游 / 能否开工 R3H-07                                      | §B → Wave1 INDEX §0 · 活卡 §5                                                                                                       |
| 测试 RED 不知测什么                                              | `to-issues-slices.md` 当前 §「建议测试」+ `bypass-baseline-matrix.md`「已存在测试」                                                 |
| 排期 / 是否拆 PR                                                 | `plan-task-sizing.md`（S10-05 单独 PR）                                                                                             |

---

## 6. 本包未覆盖的 GAP

| GAP                                     | 交付时机               |
| --------------------------------------- | ---------------------- |
| `frozen/*.md` + 根 `EXECUTION_INDEX.md` | S10-CLOSE 前（薄指针） |
| `implement.jsonl`                       | `task.py start` 后     |
| `execute-evidence/*`                    | 各切片 GREEN           |

---

## 7. 当前切片指针

| 下一建议     | 位置                                  |
| ------------ | ------------------------------------- |
| 默认下一刀   | `to-issues-slices.md` §2 **S10-BOOT** |
| 下一代码切片 | §3 **S10-01**                         |

---

## 8. 活卡 `R3H_10_DATASOURCE_SERVICE_SSOT.md` 是什么？

| 项                    | 说明                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| **是什么**            | Batch 3H **活任务卡**（Wave 级）：GitHub/issue 追踪、PASS 登记、模块 ID 的**稳定对外名片的**            |
| **放哪**              | `docs/implementation_tasks/.../R3H_10_DATASOURCE_SERVICE_SSOT.md` — ** deliberate，不迁入** `research/` |
| **与 Execute 包关系** | 活卡 = 摘要 + 指针；**可执行规格**在 `research/` 多文件包                                               |
| **是否被索引**        | ✅ `EXTERNAL-INDEX.md` §A · 活卡 §6 回指 `00-EXECUTION-ENTRY.md`                                        |
| **要不要移动**        | **不要**。移动会破坏 `docs/implementation_tasks/` 活卡惯例与 Wave INDEX 链接                            |

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
