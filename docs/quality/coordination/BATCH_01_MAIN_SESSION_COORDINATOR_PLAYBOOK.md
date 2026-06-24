# Batch 01 主会话协调手册

> **性质：** 主会话（merge coordinator）操作剧本，**不替代**任务卡与 `BATCH_01_TASK_CARD_MANIFEST.md` 中的 allowed/forbidden SSOT。  
> **适用：** Batch 01 **协调包**（manifest 五卡 + lineage 债）+ **Wave D 并行轨**（B01-023，开发可并行、合并分轨）。  
> **父路线图：** `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3D / 3E + Batch 3D.3。  
> **批次入口：** `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/README.md`。  
> **对抗性审计：** `docs/quality/coordination/BATCH_01_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`（修复闭环见 **§11**）。  
> **基线：** `master` 最新已合并状态；**本 playbook 须已提交后再开 worktree**。

---

## 0. 范围边界（必读）

| 包 | 包含 | 合并轨道 | 说明 |
| --- | --- | --- | --- |
| **Batch 01 协调包** | `B01-C01`..`C05`（WL/FRED/TDX/SP3/DH2）+ `B01-LIN` | §7 **Track A** | manifest SSOT；六卡 + lineage 卫生债 |
| **Wave D 并行轨** | `B01-023`（full Layer5 evidence chain） | §7 **Track B** | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.3 **Serial**；可与 Batch 01 **worktree 并行开发**，但**不得与 Batch 01 混为同一 merge PR/包**声称 production readiness |

**并行开发：** 七路 Execute 可同时开工（§2.5 文件锁 + registry 主会话排队）。  
**合并开发：** Batch 01 六路按 §7 Track A；023 按 §7 Track B，且须满足 `023_implement_layer5_evidence_chain.md` §16（022 + Layer3/4 集成稳定）与路线图 Batch 3D.1 串行语义。

---

## 1. 这份文件是什么

桌面 `流程—临时文件.txt` 与 Wave C 协调手册的 **Batch 01 扩展版**。

| 角色         | 职责                                                                                                                          |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| **主会话**   | 开 worktree、派发 agent、锁定共享文件组、跑全量测试、收尾提交、§7 双轨合并、**单独批处理 registry 三件套 + COVERAGE**         |
| **子 agent** | **单一分支 + 单一核心文件组**；**模型固定 `composer-2.5`**（§2.3）                                                            |
| **权威边界** | 任务卡 + `BATCH_01_TASK_CARD_MANIFEST.md` §4 + **本手册 §2.5 / §2.6**                                                       |
| **权威输入** | 任务卡 + **`docs/` + `specs/`** → **§3**（不得只读任务卡）                                                                    |

### 1.1 分支业务目的（人话）

| Playbook ID | Manifest ID | 分支 | 业务目的 |
| ----------- | ----------- | ---- | -------- |
| **B01-WL**  | `B01-C01`   | `chore/round3-model-input-whitelist` | 列第一批真实数据「菜单」 |
| **B01-FRED**| `B01-C02`   | `feature/round3-fred-authorized-sandbox-pilot` | FRED 宏观小样本试接（不进正式库） |
| **B01-TDX** | `B01-C03`   | `debt/round3-tdx-manual-probe` | TDX 试连，只当对照样品 |
| **B01-SP3** | `B01-C04`   | `feature/round3-real-data-staged-pilot-v3` | 按菜单扩 A 股/公告样本 |
| **B01-DH2** | `B01-C05`   | `feature/round3-readonly-data-health-v2` | 证据体检报告 |
| **B01-LIN** | _(manifest §1.1)_ | `fix/round3-batch6-lineage-and-layer3-hygiene` | 血缘/Layer3 卫生债 |
| **B01-023** | _(Wave D)_  | `feature/round3-023b-evidence-chain-full` | 完整 Layer5 溯源链（**Wave D，合并分轨**） |

**共同边界：** 不 production clean write；不声称 production-live；不全市场/全历史默认扫描。

---

## 2. 全局铁律

### 2.1 闭环原则

- **阻塞与非阻塞一律修完**，或主会话书面 **re-defer**（owner、phase、closure test）。
- **不得扩大范围**；registry 三件套 + **`UNRESOLVED_ITEM_TASK_COVERAGE.md`** 由主会话批处理，七路 agent **禁止并发直接 commit 闭合**。
- **Batch 01 硬停：** `BATCH_01_HARDENING_RULES.md` §1–§10；冲突取更严规则。

### 2.2 实现与测试

| 规则 | 要求 |
| ---- | ---- |
| **TDD** | 正式代码：先 RED → 再 GREEN；`.cursor/skills/trellis-execute` + `testing-guidelines` |
| **Ponytail（生产）** | `backend/`、`scripts/` 严格遵守（**中文注释不审查**） |
| **Ponytail（测试）** | `tests/**` 同标准 — §2.2.2 |
| **测试注释** | 五字段 docstring — §2.2.1；金样：`tests/test_layer3_snapshot_builder.py` |
| **全量测试** | 修复后 `uv run pytest -q` 全绿 |
| **测试目的** | 可改实现，**不可削弱目的/目标** |

#### 2.2.1 五字段 docstring

| 字段 | 要求 |
| ---- | ---- |
| **覆盖范围** | 场景人话 |
| **测试对象** | 符号/模块/路径 |
| **目的/目标** | 通俗中文 |
| **验证点** | 具体断言 |
| **失败含义** | 变红时业务失去什么保障 |

#### 2.2.2 测试 ponytail

先复用 `conftest.py` / `contract_gate_support.py`；最小 diff；无新依赖；不脆化；RED 后 GREEN 前瘦身 fixture。

### 2.3 Agent 模型

**全部 agent 使用 `composer-2.5`**；禁止 `composer-2.5-fast`；派发记录 `model=composer-2.5`。

### 2.4 工具与 Skill

| 时机 | 动作 |
| ---- | ---- |
| Boot | **`agent-toolchain.md`**（根目录）+ Trellis plan/execute skill |
| 编辑符号前 | GitNexus `impact()` |
| 提交前 | `detect_changes()`；`uv run python scripts/loop_maintain.py`（`--fix` 若触达 docs/backend） |
| Plan | `trellis-plan` + `complex-task-planning-protocol.md` |
| Execute | `trellis-execute` + 逐行 `implement.jsonl` |
| debt-lite | `DEBT.plan.md` / `research/worktree-slices.md` |
| Done | commit 规则 + 全量 pytest |
| 全部 Done | §7 合并 |

### 2.5 核心文件锁（主会话强制执行）

| 核心文件组 | 独占写权限 | 其它分支 |
| ---------- | ---------- | -------- |
| `backend/app/layer5_evidence/**`、`layer5_evidence_contract.yaml` | **B01-023** | 只读；**B01-LIN 不得改** |
| `specs/model_inputs/**`、`model_input_readiness_matrix.md` | **B01-WL** | FRED/SP3/DH2 只读已合并版 |
| `source_registry.yaml` / `source_capabilities.yaml` **fred 行** | **B01-FRED** | 只读 |
| **同文件** `tdx_pytdx` 行 + `adapters/tdx_pytdx.py` + `ops/*tdx*` | **B01-TDX** | 只读 |
| **同文件** baostock/cninfo/akshare 行（非 fred/tdx） | **B01-SP3** | TDX/FRED 只读；**改 registry 须主会话排队** |
| `staged_pilot.py` 主体、`staged_pilot_fetch_ports.py`（非 FRED 独占端口） | **B01-SP3** | FRED 仅增 FRED fetch port |
| `storage/staged_evidence.py`（窄改） | **B01-SP3** | 其它只读 |
| `data_health.py` / `data_health_cli.py` | **B01-DH2** | **FRED 不得改主体**（§8.5 注） |
| `layer3_chains/**`（lineage 债范围） | **B01-LIN** | 与 023 冲突时 **023 优先** |
| Registry 三件套 | **主会话** | agent 仅 proposed delta |

**Live 联网：** FRED/TDX/SP3 须 `BATCH_01_HARDENING_RULES.md` §3 授权 YAML，否则 mocked/dry-run。

### 2.6 Per-branch allowed / forbidden（SSOT 摘要）

> 完整以任务卡 §4/§8 + manifest §4 为准；Execute 前 Agent-2 须抄入 `MASTER`/`DEBT.plan` 的 Boundary 表。

| ID | Owns（可写） | Must not own |
| --- | --- | --- |
| **B01-WL** | `specs/model_inputs/**`、`docs/quality/model_input_readiness_matrix.md`、whitelist 测试 | runtime fetch、migration、adapter 默认启用 |
| **B01-FRED** | `fred` registry 行、FRED pilot/fetch 代码与测试、task evidence | clean write、`data_health.py` 主体、macro 替代 FRED |
| **B01-TDX** | `tdx_pytdx` 行、adapter/探针窄改、TDX 测试与 evidence | production primary、Layer2 production source |
| **B01-SP3** | staged pilot 主体、baostock/cninfo/akshare registry 行、v3 测试/evidence | FRED/TDX/QMT/Yahoo production、clean write |
| **B01-DH2** | `data_health*.py`、v2 测试、readiness 报告 evidence | fetch、`source_health_snapshot`、migration |
| **B01-LIN** | lineage/L3 hygiene 登记范围、对应测试 | `layer5_evidence/**`、schema 扩大 |
| **B01-023** | `layer5_evidence/**`、L5 契约与测试 | live source、production 写入 |

### 2.7 `/to-issues` 与切片证据

- **正式线：** Plan 冻结前必须 `/to-issues` 垂直切片；每切片独立 RED/GREEN + `execute-evidence`。
- **debt-lite：** `DEBT.plan.md` 须列 vertical slices 表（Source ID、AC、allowed、verification）。
- **对抗性审计要求：** `BATCH_01_ADVERSARIAL_AUDIT.md` §6 — 不得单块水平实现。

---

## 3. 权威必读索引

> **追溯规则（与 Wave C 同）：** 读完下表后，按 `MIGRATION_MAP.md`、`specs/context/authority_graph.yaml` **向下追溯**邻接模块；新路径 **补入计划**，禁止口头「到时候再看」。  
> **Plan 冻结：** 复杂任务写入 `MASTER.plan.md` + `implement.jsonl`；debt-lite 写入 `DEBT.plan.md`。Agent-2 按 **§3.10** 输出核对表。

### 3.0 七路分支一览

| Playbook ID | Manifest | 分支 | Worktree（权威） | Trellis task-dir（建议） | 轨道 | 流水线 | 必读 |
| ----------- | -------- | ---- | ---------------- | ------------------------ | ---- | ------ | ---- |
| B01-023 | Wave D | `feature/round3-023b-evidence-chain-full` | `../quant-monitor-desk-wt-023-layer5`（MAP §2.3） | `round3-023b-evidence-chain-full` | complex | §4 | §3.1+§3.2 |
| B01-WL | C01 | `chore/round3-model-input-whitelist` | `../quant-monitor-desk-wt-b01-wl` | `round3-model-input-whitelist` | debt-lite | §5.1 | §3.1+§3.3 |
| B01-FRED | C02 | `feature/round3-fred-authorized-sandbox-pilot` | `../quant-monitor-desk-wt-b01-fred` | `round3-fred-authorized-sandbox-pilot` | complex | §4 | §3.1+§3.4 |
| B01-TDX | C03 | `debt/round3-tdx-manual-probe` | `../quant-monitor-desk-wt-b01-tdx` | `round3-tdx-manual-probe` | debt-lite | §5.2 | §3.1+§3.5 |
| B01-SP3 | C04 | `feature/round3-real-data-staged-pilot-v3` | `../quant-monitor-desk-wt-b01-sp3` | `round3-real-data-staged-pilot-v3` | complex | §4 | §3.1+§3.6 |
| B01-DH2 | C05 | `feature/round3-readonly-data-health-v2` | `../quant-monitor-desk-wt-b01-dh2` | `round3-readonly-data-health-v2` | complex | §4 | §3.1+§3.7 |
| B01-LIN | §1.1 | `fix/round3-batch6-lineage-and-layer3-hygiene` | `../quant-monitor-desk-wt-b01-lin` | `round3-batch6-lineage-hygiene` | debt-lite | §5.3 | §3.1+§3.8 |

**Legacy 绑定（manifest §2）：** L01→TDX；L02/L06→SP3；L03→DH2；L04→FRED；L05→FRED/SP3（018B 边界）；执行时 **legacy + forward 卡同读**。

### 3.1 共用底座（每分支 Plan 前 Read + 摘要）

| 类别 | 路径 |
| ---- | ---- |
| **协调** | 本 playbook · `BATCH_01_MODEL_SOURCE_READINESS/**` · `ROUND_3_DATA_PRODUCTION_READINESS/README.md` |
| **协调** | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.3/§2.6 · `round3-repair-debt-worktree-plan.md` §6 |
| **协调** | `complex-task-planning-protocol.md` Phase 8D · **`agent-toolchain.md`** |
| **审计** | `BATCH_01_ADVERSARIAL_AUDIT.md` · `BATCH_01_HARDENING_RULES.md` · `FIRST_BATCH_SELF_CHECK.md` |
| **Registry** | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` · `UNRESOLVED_ITEM_TASK_COVERAGE.md` |
| **Handoff** | `ROUND3_HANDOFF.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` |
| **质量门** | `staged_acceptance_policy.md` · `production_live_pilot_policy.md` · `BATCH3_STAGED_DOWNSTREAM_GATE.md` |
| **质量门** | `ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md` · `docs/ops/verification_commands.md`（Round 3 gate hygiene） |
| **全局** | `GLOBAL_EXECUTION_RULES.md` · `GLOBAL_TESTING_POLICY.md` · `GLOBAL_RESOURCE_LIMITS.md` · **`GLOBAL_TASK_TEMPLATE.md`** |
| **契约** | `runtime_versions.md` · `write_contract.yaml` · `resource_limits.yaml` · `snapshot_lineage_contract.yaml` |
| **架构** | `module_boundary_matrix.md` · `MIGRATION_MAP.md` · `specs/context/authority_graph.yaml` |

### 3.2 B01-023 — Layer5 Evidence Chain

**任务卡：** `023_implement_layer5_evidence_chain.md` · 归档 `023A_layer5_evidence_foundation.md` / `PROMPT_08`  
**无 PROMPT_023b**；Plan 第一读 = 任务卡 + §16 sequencing + 023A 归档证据。

| 路径 | 用途 |
| ---- | ---- |
| `docs/modules/layer5_security_evidence.md` | L5 权威 |
| `specs/contracts/layer5_evidence_contract.yaml` | 主契约 |
| `docs/modules/data_validation_and_conflict.md` | 冲突/复核 |
| `docs/modules/write_manager.md` | WriteManager |
| `docs/architecture/03_runtime_flows.md` · `04_data_architecture.md` | 运行/数据分层 |
| `docs/quality/final_package_rules.md` | 包规则 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | `R3-PARTIAL-4`、`R2-RISK-2`、`ADV-R3X-LINEAGE-001` 等 |
| `UNRESOLVED_ITEM_TASK_COVERAGE.md` | ID 映射 |
| `backend/app/layer5_evidence/` | 实现 |
| `backend/app/layer3_chains/` · `layer4_markets/` | 上游（只读） |
| `tests/test_layer5_evidence_foundation.py` · `test_layer5_evidence_chain.py` | 测试 |

### 3.3 B01-WL — Model Input Whitelist

**任务卡：** `R3D_model_input_whitelist.md`

| 路径 | 用途 |
| ---- | ---- |
| `specs/datasource_registry/source_registry.yaml` · `source_capabilities.yaml` | 只读对照 |
| `specs/contracts/source_route_contract.yaml` · `source_capability_contract.yaml` · `datasource_service_contract.yaml` | 路由/能力 |
| `specs/contracts/layer2_sensor_contract.yaml` · `layer3_loader_contract.yaml` · `layer4_market_contract.yaml` · `layer5_evidence_contract.yaml` | 各层 |
| `specs/layer1_axes/restructured_axes_v1_1/**` | Layer1 指标 |
| `tests/fixtures/layer2_cross_asset_registry_fixture.yaml` · `layer3_staged_bundle/bundle_manifest.yaml` · `layer4_staged_market/manifest.yaml` | staged 现状 |
| `017`–`022` 历史建模任务卡（任务卡 §3 列表） | 输入对照 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | 历史追踪 |

### 3.4 B01-FRED — FRED Sandbox Pilot

**任务卡：** `R3E_fred_authorized_sandbox_pilot.md` · legacy **B01-L04** `PROMPT_04` · **B01-L05** `018B` · **B01-L03** v1 health（只读）  
**前置：** B01-WL Layer1 P0 macro 白名单已合并或可引用  
**关闭：** `B2.5-O-05`

| 路径 | 用途 |
| ---- | ---- |
| `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml` 等三轴 | P0 series |
| `backend/app/datasources/route_planner.py` · `capability_registry.py` · `service.py` | 路由 |
| `backend/app/ops/staged_pilot.py` · `staged_pilot_fetch_ports.py` · `live_pilot_fetch_ports.py` | pilot |
| `specs/contracts/data_adapter_contract.md` · `data_quality_rules.yaml` | 契约 |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md` | FRED 语义 |

### 3.5 B01-TDX — TDX Manual Probe

**任务卡：** `R3E_tdx_manual_probe_addendum.md` · legacy **B01-L01** `018C_tdx_pytdx_low_cost_probe.md`

| 路径 | 用途 |
| ---- | ---- |
| `R3D_018C_low_cost_source_probe.md` · `R3D_018C_live_manual_probe_plan.md` | reference landing |
| `PROMPT_10_debt_r3b275_018c_live_manual_probe_plan.md` | 计划约束 |
| `backend/app/datasources/adapters/tdx_pytdx.py` · `ops/staged_pilot.py` · `live_pilot_fetch_ports.py` | 实现邻接 |
| `backend/app/layer2_sensors/observation.py` | Layer2 守卫 |
| registry OPEN 行：`R3-B2.75-REQ2-EM`、`R3-PROMPT14-AKSHARE-VAL-01`、`R2.6-IMPL-8` | 不可误关 |

### 3.6 B01-SP3 — Staged Pilot v3

**任务卡：** `R3E_real_data_staged_pilot_v3.md` · legacy **B01-L02** v2 · **B01-L06** v2 addendum · **B01-L05** 018B  
**前置：** `specs/model_inputs/**` 存在，否则 **STOP**

| 路径 | 用途 |
| ---- | ---- |
| `R3X_real_data_staged_pilot.md` · `R3Y_real_data_staged_pilot_v2.md` · `R3Y_staged_pilot_v2_execution_addendum.md` | v1/v2 |
| `docs/quality/prompt14_user_authorization_2026-06-22.md` | 授权语境 |
| `specs/contracts/source_conflict_rules.yaml` | 冲突 dry-run |
| `backend/app/ops/staged_pilot*.py` · `storage/staged_evidence.py` · `validators/data_quality.py` | 实现 |
| `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/` | v2 证据 SSOT |

### 3.7 B01-DH2 — Data Health v2

**任务卡：** `R3E_readonly_data_health_v2.md` · legacy **B01-L03** v1 · `PROMPT_20_feature_round3_readonly_data_health_v1.md`  
**输入：** WL/FRED/TDX/SP3 task-local evidence（可先 fixture，合并前对齐真实路径）

| 路径 | 用途 |
| ---- | ---- |
| 四张兄弟 Batch 01 forward 卡（§3 互引） | 证据 schema |
| `R3Y_readonly_data_health_v1.md` | v1 模式 |
| `backend/app/ops/data_health.py` | **独占** |
| `tests/test_ops_data_health.py` · `test_staged_pilot.py` · `test_raw_store.py` | 测试基线 |
| `specs/model_inputs/**` | whitelist 对照 |

### 3.8 B01-LIN — Lineage & Layer3 Hygiene

**无 forward 卡**；权威 = 路线图 Batch 3D.3 + `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` + `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md`

| ID / 路径 | 用途 |
| --------- | ---- |
| `ADV-R3X-LINEAGE-001` | L3/L4 snapshot lineage |
| `R3Y-LINEAGE-VR-001` | VR/fetch_log binding |
| `R3-B6-021-O-01` / `O-02` | Layer3 manifest/bar |
| `R3Y-TEST-DEPTH-001` | test depth |
| `docs/quality/adversarial_audit_report.md` | AUD-05/07 来源 |
| `backend/app/layer3_chains/**` · `layer4_markets/**` · `layer2_sensors/**`（若 VR 绑定触及） | 实现邻接 |

### 3.9 Plan 质检 checklist（复杂任务 Agent-2）

- [ ] §3.1 + 分支 §3.x **每一行** 已入 `MASTER`/`implement.jsonl` 或标明无损摘要
- [ ] `authority_graph.yaml` 模块已核对
- [ ] `GLOBAL_TASK_TEMPLATE.md` 15 节与任务卡 Red Flags 已覆盖
- [ ] Batch hardening §3–§7、§2.5/§2.6 边界已写入
- [ ] 任务卡 §必读 与 PROMPT §5（若有）**无缺口**
- [ ] `/to-issues` 切片表已冻结
- [ ] 遗漏项已写回 MASTER 并修复，**复检零遗留**

### 3.10 Plan 质检输出格式（Agent-2 必填）

| 路径 | 已入 MASTER/implement | 摘要一句 | 遗漏风险 |
| ---- | --------------------- | -------- | -------- |

---

## 4. 轨道 A — 四条正式线（complex）

**适用：** B01-023、B01-FRED、B01-SP3、B01-DH2。

### 4.1 Agent 流水线

```
Plan → Plan质检 → Execute → Audit(A1–A8) → Repair → 对抗性审计 → 主会话提交
```

| 步骤 | Agent | 产出与门禁 |
| ---- | ----- | ---------- |
| 1 Plan | `composer-2.5` | `MASTER.plan.md`、`implement.jsonl`、`validate-plan-freeze` exit 0 |
| 2 Plan质检 | `composer-2.5` | §3.9/§3.10 零遗留 |
| 3 Execute | `composer-2.5` | TDD §8.x；RED/GREEN 证据；`validate-execute-handoff` |
| 4 Audit ×8 | `composer-2.5` | §4.2 模板；`audit_matrix.json` |
| 5 Repair | `composer-2.5` | 阻塞+非阻塞全修 |
| 6 对抗性 | `composer-2.5` | `agents/audit-adversarial-authority.md` |
| 7 主会话 | — | §6 + §8.x PASS + commit |

**Plan 必含：** §2.2–§2.3、§2.5–§2.7、hardening 摘要；建议将 §8.x 抄入 `MASTER.plan.md` §2 子 AC。

### 4.2 Audit 派发（一维一 agent）

| 维 | 模板 |
| --- | --- |
| A1 | `agents/audit-a1-spec.md` |
| A2 | `agents/audit-a2-ponytail.md` |
| A3 | `agents/security-auditor.md` + `sql-pro.md` |
| A4 | `agents/code-reviewer.md` |
| A5 | `agents/audit-a5-completion.md` + `quant-analyst.md` + `risk-manager.md` |
| A6 | `agents/performance-engineer.md`（SKIP 须记录） |
| A7 | `agents/database-administrator.md` + `sre-engineer.md` + `devops-incident-responder.md` |
| A8 | `agents/qa-expert.md` + `test-automator.md` |

路由：`.trellis/spec/guides/audit-skill-paths.yaml`。

### 4.3 正式线 Audit 单队列

- Execute 可并行；**Audit→Repair→对抗性→提交** 同一时刻 **仅一条正式线**。
- 轨道 B **不占** 此队列。
- 建议 Audit 顺序（Execute 完成先后）：**FRED → SP3 → DH2 → 023**（023 属 Wave D，可与 Batch 01 完成先后解耦）。

### 4.4 正式线派发清单

| # | 角色 | Prompt 要点 |
| --- | ---- | ------------- |
| 1 | Plan | 任务卡 + `trellis-plan` + §3 + hardening + `/to-issues` |
| 2 | Plan质检 | §3.9–§3.10 + §2.5/§2.6 + 零遗留 |
| 3 | Execute | `implement.jsonl` 逐行 + TDD + impact |
| 4a–h | A1–A8 | `agents/` 全文 + diff + AC |
| 5 | Repair | 全 findings 修复 + pytest |
| 6 | 对抗性 | `audit-adversarial-authority.md` |
| 7 | 主会话 | §6 + §8 + commit |

---

## 5. 轨道 B — 三条精简线 + 文档线

### 5.1 B01-WL

```
轻量Plan → Plan质检 → 编写 → 对抗性审计 → 主会话
```

| 步骤 | 要求 |
| ---- | ---- |
| 轻量 Plan | `DEBT.plan.md`；allowed §2.6 |
| **Plan质检** | §3.3 全文索引；manifest C01；hardening §5–§8；零遗留 |
| 编写 | YAML + matrix；无 fetch |
| 对抗性 | `audit-adversarial-authority.md` + `BATCH_01_ADVERSARIAL_AUDIT.md` |
| 主会话 | §6 + §8.1 |

### 5.2 B01-TDX

```
轻量Plan → Plan质检 → 修复/探针 → 对抗性 → 主会话
```

| 步骤 | 要求 |
| ---- | ---- |
| Plan质检 | 018C + addendum；**较小 cap**（B01-AUD-02） |
| 修复 | TDD；raw-only；`enabled_by_default=false` |
| 主会话 | 无授权 → 仅 mocked |

### 5.3 B01-LIN

```
轻量Plan → Plan质检 → 修复 → 对抗性 → 主会话
```

| 步骤 | 要求 |
| ---- | ---- |
| Plan | 映射 `R3D-LIN-*`/`R3D-L3-*`/`R3D-TEST-01` |
| 修复 | malformed fail-closed；lineage pytest |
| 禁止 | `layer5_evidence/**` |

### 5.4 精简线派发表

| 分支 | 1 | 2 | 3 | 4 | 5 |
| ---- | - | - | - | - | - |
| WL | 轻量Plan | **Plan质检** | 编写 | 对抗性 | 主会话 |
| TDX | 轻量Plan | **Plan质检** | 修复 | 对抗性 | 主会话 |
| LIN | 轻量Plan | **Plan质检** | 修复 | 对抗性 | 主会话 |

---

## 6. 单分支 Done — 主会话验收

- [ ] 任务卡 §11 + §8.x 验收命令全绿
- [ ] `uv run pytest -q` 全绿
- [ ] `loop_maintain.py`（需时 `--fix`）
- [ ] `detect_changes()`；符合 §2.5/§2.6
- [ ] 测试五字段 + 测试 ponytail
- [ ] §3 已索引；`composer-2.5` 记录
- [ ] Trellis 证据（complex：`validate-execute-handoff`；debt：merge gate）
- [ ] no-mutation / 授权证据（适用时）
- [ ] 分支 worktree commit
- [ ] **Closure report 九项**（父包 `ROUND_3_DATA_PRODUCTION_READINESS/README.md` §5）：
  1. Branch / worktree / task ID
  2. What changed
  3. What did not change
  4. Test commands and results
  5. ResourceGuard status
  6. Source authorization status
  7. Production DB mutation proof or no-touch statement
  8. Registry updates（resolved / re-defer / none）
  9. Remaining risks and next gate

---

## 7. 全部 Done — 合并

### 7.1 推荐：integration 预合并（可选但建议）

```bash
git checkout master && git pull
git checkout -b integration/round3-batch01
# 按 Track A 顺序 merge 各 feature 分支
uv run pytest -q
uv run python scripts/loop_maintain.py --fix
# FF merge integration/round3-batch01 → master
```

**Track B（023）** 合入 `integration/round3-wave-d` 或直 `master`，**不与 Batch 01 integration 包混 PR**。

### 7.2 Track A — Batch 01 协调包合并顺序

| 序 | ID | 分支 | 前提 |
| --- | --- | --- | --- |
| 1 | B01-WL | `chore/round3-model-input-whitelist` | — |
| 2 | B01-LIN | `fix/round3-batch6-lineage-and-layer3-hygiene` | 可与 1 交换；避让未合并 023 的 layer5 冲突 |
| 3 | B01-FRED | `feature/round3-fred-authorized-sandbox-pilot` | **WL 已合并** |
| 4 | B01-TDX | `debt/round3-tdx-manual-probe` | 可与 3 交换 |
| 5 | B01-SP3 | `feature/round3-real-data-staged-pilot-v3` | **WL 已合并** |
| 6 | B01-DH2 | `feature/round3-readonly-data-health-v2` | WL + FRED/TDX/SP3 evidence 可读 |

### 7.3 Track B — Wave D（023）

| 序 | 分支 | 前提 |
| --- | ---- | ---- |
| 1 | `feature/round3-023b-evidence-chain-full` | 022 + Layer3/4 集成稳定（任务卡 §16）；全量 pytest 绿 |

### 7.4 合并后主会话（一次协调提交）

1. **Registry 三件套** — manifest §5 全表：

   | Registry 行 | 闭合 owner | 备注 |
   | ----------- | ---------- | ---- |
   | `B2.5-O-05` | B01-C02 | FRED-only evidence |
   | `R3-PROMPT14-AKSHARE-VAL-01` | B01-C04 或 re-defer | validation-only |
   | `R3-B2.75-REQ2-EM` | **不可** TDX 单独关闭 | Eastmoney 政策 |
   | TDX disabled-candidate | B01-C03 | raw probe 或 re-defer |
   | Data health v2 readiness | B01-C05 | 只读报告，非 production ready |

2. 更新 **`docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`**（B01-C0x ↔ 分支 ↔ 证据路径）
3. 确认 WL 已产出 `model_input_readiness_matrix.md`（DH2/SP3 仅引用，不重复改除非 AC 要求）
4. 全量 pytest + `loop_maintain --fix`
5. GitNexus `analyze`（勿覆盖 `AGENTS.md` 定制段）
6. 更新 `PROJECT_IMPLEMENTATION_ROADMAP.md`、`ROUND3_HANDOFF.md`、`ROUND3_BATCH_IMPLEMENTATION_MAP.md` checkpoint

---

## 8. 各分支 PASS 条件与 §11 验收命令

> §6 + 本节**同时满足**方可 Done。复杂任务建议将下表抄入 `MASTER.plan.md` §2。

### 8.1 B01-WL

| 维度 | PASS |
| ---- | ---- |
| 产出 | `specs/model_inputs/layer1`..`layer5` + matrix 字段齐全 |
| 角色 | 无 AkShare Primary / TDX production / FRED production 升级 |
| 审计 | 对抗性零 OPEN |

```bash
uv sync --locked
uv run pytest tests/test_round3_verification_command_matrix.py -q
uv run pytest tests/test_unresolved_item_task_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
uv run pytest tests/test_model_input_whitelist.py -q   # 若新增
uv run pytest -q && uv run ruff check .
```

### 8.2 B01-TDX

| 维度 | PASS |
| ---- | ---- |
| 授权 | 授权 YAML 或 `BLOCKED_AUTH` + mocked 绿 |
| 角色 | validation-only；非 Layer2 production primary |
| 审计 | 未关 `R3-B2.75-REQ2-EM` |

```bash
uv sync --locked
uv run pytest tests/test_tdx_manual_probe.py -q
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_layer2_cross_asset_sensor.py -q
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

### 8.3 B01-LIN

| 维度 | PASS |
| ---- | ---- |
| 范围 | 未改 `layer5_evidence/**` |
| 行为 | malformed fail-closed；lineage 测试绿 |
| TEST-DEPTH | runtime 测试或 wont-fix ADR |

（验收命令以 `DEBT.plan.md` Verification 列为准 + 全量 `uv run pytest -q`）

### 8.4 B01-023

| 维度 | PASS |
| ---- | ---- |
| Plan | `validate-plan-freeze` exit 0；`R3D-023-01`..`05` |
| 实现 | evidence chain；Agent 文本非事实源 |
| Audit | A1–A8 + 对抗性零遗留 |

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

### 8.5 B01-FRED

| 维度 | PASS |
| ---- | ---- |
| Registry | fred sandbox/disabled-by-default |
| B2.5-O-05 | FRED-only 关闭或 re-defer |
| 边界 | **未改 `data_health.py` 主体** |

```bash
uv sync --locked
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py -q
# 下列仅跑既有绿测，不得为 FRED 改 data_health 主体：
uv run pytest tests/test_ops_data_health.py -q
uv run ruff check backend/app/datasources backend/app/ops tests/test_fred_*.py
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

### 8.6 B01-SP3

| 维度 | PASS |
| ---- | ---- |
| 白名单 | 每 symbol 可追溯 `specs/model_inputs/**` |
| 冲突 | dry-run summary；无 clean 覆盖 |

```bash
uv sync --locked
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q
uv run pytest tests/test_real_data_staged_pilot_v3.py -q
uv run ruff check backend/app/ops backend/app/storage backend/app/validators tests/test_staged_pilot.py tests/test_raw_store.py tests/test_real_data_staged_pilot_v3.py
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

### 8.7 B01-DH2

| 维度 | PASS |
| ---- | ---- |
| 只读 | 无 fetch/DB 写/`source_health_snapshot` |
| profile | whitelist/FRED/TDX/v3/rollup |

```bash
uv sync --locked
uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q   # 若触及 evidence helper
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

### 8.8 口诀

| 类型 | Done 当且仅当 |
| ---- | ------------- |
| 正式线 | §6 + §8.4–§8.7 每行 + 已提交 |
| 精简线 | §6 + §8.1–§8.3 + 对抗性闭环 + 已提交 |

---

## 9. 开波检查清单

- [ ] 本 playbook + `BATCH_01_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` 已提交
- [ ] 已读 manifest · hardening · adversarial audit · **父 README** · **`agent-toolchain.md`**
- [ ] 七分支 owner、worktree、§2.5 锁已登记
- [ ] FRED/TDX/SP3 **live 授权**已向用户确认
- [ ] `composer-2.5 only`；registry **仅主会话批处理**
- [ ] integration 分支策略已选（§7.1）

### 9.1 Worktree 创建模板

**前置：** 每分支 `DEBT.plan`/`MASTER` 含 allowed、forbidden、verification、merge gate（`round3-repair-debt-worktree-plan.md` §8）。

```bash
cd C:/Users/Guang/Desktop/quant-monitor-desk
git fetch origin
git worktree add -b chore/round3-model-input-whitelist ../quant-monitor-desk-wt-b01-wl master
# 重复：wt-b01-fred, wt-b01-tdx, wt-b01-sp3, wt-b01-dh2, wt-b01-lin
git worktree add -b feature/round3-023b-evidence-chain-full ../quant-monitor-desk-wt-023-layer5 master
```

每 worktree 内首次验证：

```bash
uv sync --locked
uv run pytest -q --tb=no -x   # 基线绿
```

---

## 10. 快速对照

| 原意 | 章节 |
| ---- | ---- |
| 正式复杂流程 | §4 |
| debt-lite | §5 |
| 七路文件锁 | §2.5 |
| allowed/forbidden | §2.6 |
| `/to-issues` | §2.7 |
| 双轨合并 | §0、§7 |
| closure 九项 | §6 |

---

## 11. Playbook 对抗性审计修复闭环

| 处置 | 章节 |
| ---- | ---- |
| 范围边界 023 vs Batch 01 | §0、§7 Track A/B |
| ID 映射 C01–C05 | §1.1、§3.0 |
| LIN 入 manifest | manifest §1.1 |
| closure report 路径 | §6 九项内联 |
| allowed/forbidden SSOT | §2.6 |
| registry 锁 SP3/TDX | §2.5 |
| `/to-issues` | §2.7 |
| Plan 质检 debt-lite | §5.1–§5.3 |
| §3 索引补全 | §3.2–§3.8 |
| §11 验收命令 | §8.1–§8.7 |
| integration 分支 | §7.1 |
| worktree 命令 | §9.1 |
| COVERAGE 更新 | §7.4 |
| 对抗性审计原文 | `BATCH_01_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` |

---

_文档版本：2026-06-24 rev.2 · 对抗性审计 hardened · Batch 01 + Wave D 023 双轨_
