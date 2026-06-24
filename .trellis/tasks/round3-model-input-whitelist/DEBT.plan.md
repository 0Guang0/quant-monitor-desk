# Repair/Debt Lite Plan — round3-model-input-whitelist

> **Playbook ID:** B01-WL (`B01-C01`)  
> **轨道:** debt-lite（§5.1）  
> **模型:** `composer-2.5`  
> **Trellis task-dir:** `.trellis/tasks/round3-model-input-whitelist`  
> **本阶段:** 轻量 Plan only — **禁止**业务实现代码、**禁止** registry 三件套 commit

---

## Source of truth

| 项 | 值 |
| --- | --- |
| 任务卡 | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md` |
| Manifest | `BATCH_01_TASK_CARD_MANIFEST.md` → `B01-C01` |
| 协调手册 | `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §2.5/§2.6/§2.7 + §5.1 |
| Hardening | `BATCH_01_HARDENING_RULES.md` §3–§9（Plan 摘要 §3–§7 + §9 escalate；编写阶段逐条引用） |
| base branch | `master` |
| target branch | `chore/round3-model-input-whitelist` |
| worktree | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b01-wl` |
| owner agent | B01-WL Plan → 编写 agent（同分支） |

## 决策与目标

建立五层模型**第一批真实数据输入白名单**（docs/spec/config），供 B01-FRED、B01-SP3、B01-DH2 只读引用。**WL 为 Batch 01 Track A 合并序 #1**；Layer1 P0 macro 白名单须最先冻结，解除 FRED/SP3 前置阻塞。

**允许表述：** model input whitelist established · sandbox/staged candidate · validation-only · deferred  
**禁止表述：** production-live ready · production clean write · full-market/full-history default

## Boundary（§2.5 / §2.6 SSOT）

| 维度 | 内容 |
| --- | --- |
| **§2.5 文件锁** | `specs/model_inputs/**`、`docs/quality/model_input_readiness_matrix.md`、whitelist 测试 **B01-WL 独占写**；FRED/SP3/DH2 仅只读已合并版；registry 三件套 **主会话**独占 |
| **Owns（可写）** | 同上 + whitelist 语义验证测试（如 `tests/test_model_input_whitelist.py`） |
| **Must not own** | runtime fetch、DB migration、adapter 默认启用、`source_registry.yaml` / `source_capabilities.yaml` 直接修改、registry 三件套、`backend/app/**` 运行时逻辑 |
| **production/data** | 无网络 fetch、无 DB 写、无 clean write、无 live probe |
| **non-goals** | 不关闭 `B2.5-O-05`；不升级 FRED/TDX/AkShare 生产角色；不扩 registry 行 |

## 基线注意（非本分支引入）

`master` 上 `tests/test_ops_data_health.py::test_dataHealthIntegration_v2Evidence_bundle` **当前为红**；归属 B01-DH2 / v2 evidence 对齐，**WL Plan 仅记录**。编写阶段全量 pytest 若因此红，须在 evidence 中注明「已知 master 基线债」，不得为绿而改 `data_health.py`。

---

## Vertical slices（`/to-issues` 冻结表）

> 垂直切片；编写阶段一次一片 RED→GREEN。不得单块水平扫五层 YAML。

| Slice | Source ID | AC（完成标准） | Allowed files | Forbidden files | Verification | Evidence path |
| --- | --- | --- | --- | --- | --- | --- |
| **WL-01** | `R3D-WL-L1` | `layer1_source_whitelist.yaml` 含 P0 macro：`DGS10`、`T10Y3M`、`VIXCLS`、`SP500`、`DFII10`；其余 Layer1 指标标 `deferred`/`P2`；每行含任务卡 §6 必填字段；`fred` 行 `readiness=sandbox_candidate`，`macro_supplementary` 不得作 FRED primary | `specs/model_inputs/layer1_source_whitelist.yaml` | registry、backend、fetch | `pytest tests/test_model_input_whitelist.py -k layer1 -q`（编写后） | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-01-green.txt` |
| **WL-02** | `R3D-WL-L2` | `layer2_source_whitelist.yaml` 对照 `layer2_cross_asset_registry_fixture.yaml`：VIX/HYG 等 axis display-only → `fixture_only`；Copper/HG 等 → `staged_fixture` 或 `sandbox_candidate`；无 live FRED 默认 | `specs/model_inputs/layer2_source_whitelist.yaml` | Layer2 runtime、registry | `pytest tests/test_model_input_whitelist.py -k layer2 -q` | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-02-green.txt` |
| **WL-03** | `R3D-WL-L3` | `layer3_anchor_source_plan.yaml` 映射 anchor/node → `source_id`/`operation`；staged bundle 项标 `staged_only`；缺源标 `deferred` + `closure_test` | `specs/model_inputs/layer3_anchor_source_plan.yaml` | `layer3_chains/**` 实现 | `pytest tests/test_model_input_whitelist.py -k layer3 -q` | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-03-green.txt` |
| **WL-04** | `R3D-WL-L4` | `layer4_market_source_plan.yaml`：`CN_A` calendar/breadth 为首批 `sandbox_candidate`；US/HK/FUT/options 默认 `deferred`；对照 `layer4_staged_market/manifest.yaml` | `specs/model_inputs/layer4_market_source_plan.yaml` | `layer4_markets/**` 实现 | `pytest tests/test_model_input_whitelist.py -k layer4 -q` | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-04-green.txt` |
| **WL-05** | `R3D-WL-L5` | `layer5_instrument_source_plan.yaml`：baostock 日 K、cninfo 元数据、FRED macro daily、`tdx_pytdx` validation-only；无 production_candidate | `specs/model_inputs/layer5_instrument_source_plan.yaml` | `layer5_evidence/**` | `pytest tests/test_model_input_whitelist.py -k layer5 -q` | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-05-green.txt` |
| **WL-06** | `R3D-WL-MATRIX` | `model_input_readiness_matrix.md` 人类可读汇总；`specs/model_inputs/README.md`；语义测试覆盖 forbidden role 转移（akshare≠primary、tdx≠production、fred≠production、macro_supplementary≠FRED primary） | `docs/quality/model_input_readiness_matrix.md`、`specs/model_inputs/README.md`、`tests/test_model_input_whitelist.py` | 仅存在性断言 | §11 验收命令全集 + `loop_maintain.py --fix`（docs 索引） | `.trellis/tasks/round3-model-input-whitelist/execute-evidence/wl-06-green.txt` |

### WL-01 P0 macro 种子（来自 Layer1 specs，编写时展开为完整行）

| input_id（建议） | series | source_id | role | readiness | notes |
| --- | --- | --- | --- | --- | --- |
| `L1-ENV-DGS10` | `DGS10` | `fred` | `primary_candidate` | `sandbox_candidate` | `ENV-E1-DGS10`；须用户授权后 live |
| `L1-ENV-T10Y3M` | `T10Y3M` | `fred` | `primary_candidate` | `sandbox_candidate` | 收益率曲线利差 |
| `L1-RA-VIXCLS` | `VIXCLS` | `fred` | `primary_candidate` | `sandbox_candidate` | Layer2 fixture 仍为 staged_fixture |
| `L1-RA-SP500` | `SP500` | `fred` | `primary_candidate` | `sandbox_candidate` | 风险轴交叉验证 |
| `L1-ENV-DFII10` | `DFII10` | `fred` | `primary_candidate` | `sandbox_candidate` | 实际利率；非 macro_supplementary |

**显式禁止：** `macro_supplementary`（akshare）不得标记为上述 FRED 序列的 `primary_candidate` 或 `production_candidate`（hardening §4、§8）。

---

## §3.1 共用底座索引（已入 Plan）

| 类别 | 路径 | Plan 落点 | 摘要一句 |
| --- | --- | --- | --- |
| 协调 | playbook · BATCH_01_MODEL_SOURCE_READINESS/** · ROUND_3 README | 本文 Source of truth | Batch 01 协调包与 WL 流水线 §5.1 |
| 协调 | ROUND3_BATCH_IMPLEMENTATION_MAP §2.3/§2.6 · round3-repair-debt-worktree-plan §6 | Vertical slices + Merge gate | 历史追踪；WL 为 C01 首卡 |
| 协调 | complex-task-planning-protocol Phase 8D · agent-toolchain.md | 本文结构 | debt-lite 轻量计划模板 |
| 审计 | BATCH_01_ADVERSARIAL_AUDIT · HARDENING · FIRST_BATCH_SELF_CHECK | § Hardening 摘要 | 对抗性约束写入测试 AC |
| Registry | AUDIT_DEFERRED / UNRESOLVED / RESOLVED · COVERAGE | Boundary non-goals | **WL 不闭合** registry 行；主会话 §7.4 |
| Handoff | ROUND3_HANDOFF · PROJECT_IMPLEMENTATION_ROADMAP | 决策与目标 | Round 3D.2 P0 |
| 质量门 | staged_acceptance_policy · production_live_pilot_policy · BATCH3_STAGED_DOWNSTREAM_GATE | Boundary + WL-06 | docs/spec 阶段验收 |
| 质量门 | ROUND3_TEST_DOCSTRING_HYGIENE · verification_commands | Merge gate | 五字段 docstring；Round 3 gate |
| 全局 | GLOBAL_EXECUTION_RULES · TESTING_POLICY · RESOURCE_LIMITS · TASK_TEMPLATE | Vertical slices Verification | 无 fetch、小 caps |
| 契约 | runtime_versions · write_contract · resource_limits · snapshot_lineage | WL-06 row fields | lineage 字段要求记入每行 |
| 架构 | module_boundary_matrix · MIGRATION_MAP · authority_graph.yaml | Boundary | `model_inputs` 为 docs/spec 新簇；合并后 `loop_maintain` 补图 |

---

## §3.3 B01-WL 分支索引（playbook 逐行）

| 路径 | 用途 | 已入 Plan | 摘要一句 | 遗漏风险 |
| --- | --- | --- | --- | --- |
| `specs/datasource_registry/source_registry.yaml` | 只读对照 | WL-01/05 + Boundary | baostock/cninfo/akshare/tdx 角色与 domain 对齐；**不改文件** | 低 — 编写时逐行核对 `macro_supplementary` |
| `specs/datasource_registry/source_capabilities.yaml` | 只读对照 | WL-05 | capability 与 operation 映射 | 低 |
| `specs/contracts/source_route_contract.yaml` | 路由契约 | WL-05 | `source_id`+`operation` 不得绕过 RoutePlanner | 中 — L5 operation 命名须与契约一致 |
| `specs/contracts/source_capability_contract.yaml` | 能力契约 | WL-05 | validation_only 语义 | 低 |
| `specs/contracts/datasource_service_contract.yaml` | 服务契约 | Boundary | 白名单不改 service | 低 |
| `specs/contracts/layer2_sensor_contract.yaml` | L2 契约 | WL-02 | staged_fixture vs sandbox_candidate | 低 |
| `specs/contracts/layer3_loader_contract.yaml` | L3 契约 | WL-03 | anchor/source_keys 映射 | 中 — anchor registry JSON 字段对齐 |
| `specs/contracts/layer4_market_contract.yaml` | L4 契约 | WL-04 | CN_A market_id 与 breadth/calendar | 低 |
| `specs/contracts/layer5_evidence_contract.yaml` | L5 契约 | WL-05 | instrument/bar/event 证据候选 | 中 — 与 023 并行只读 |
| `specs/layer1_axes/restructured_axes_v1_1/**` | Layer1 指标 SSOT | WL-01 P0 表 | 五轴 indicator_spec 提取 FRED 序列 | 低 — P1 可第二批 |
| `tests/fixtures/layer2_cross_asset_registry_fixture.yaml` | staged L2 现状 | WL-02 | VIX/HYG display_only；Copper staged | 低 |
| `tests/fixtures/layer3_staged_bundle/bundle_manifest.yaml` | staged L3 现状 | WL-03 | `staged_fixture_only` 标记 | 低 |
| `tests/fixtures/layer4_staged_market/manifest.yaml` | staged L4 现状 | WL-04 | `CN_A` + source_fetch_ids | 低 |
| `017`–`022` 历史建模任务卡 | 输入对照 | WL-01..05 AC | 各层实现边界只读 | 低 — 不重复实现层逻辑 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | 历史追踪 | Source of truth | checkpoint 由主会话更新 | 低 — WL 不改 MAP |

---

## Hardening 摘要（编写阶段强制 §3–§7）

| 规则 | WL 落地 |
| --- | --- |
| §3 Authorization | 本任务 docs/spec only — **无 live fetch**；每行 `requires_user_authorization` 须如实标注；下游 FRED/TDX/SP3 live 须 §3 授权 YAML，否则 `FAIL_AUTH`/`BLOCKED_AUTH` |
| §4 Registry closure | **不闭合** deferred 行；`macro_supplementary` 不足以关 `B2.5-O-05`；proposed delta 仅写 task evidence |
| §5 Source role | baostock→sandbox A 股日线；cninfo→metadata；akshare→validation_only；fred→sandbox；tdx→validation-only disabled-default |
| §6 Data scope | 有界 symbol/series/row/window；禁止全市场/全历史默认 |
| §7 Evidence | 每行预留 `source_fetch_id`/`content_hash`/`as_of`/`rule_version` 需求；本任务不采集 |
| §8 Testing | 负向：akshare≠Primary；tdx≠production primary；fred≠production；macro_supplementary≠FRED primary；缺授权须阻断 live |
| §9 Escalate | 扩 cap / live / registry 闭合 → STOP，交主会话 |

## GLOBAL_TASK_TEMPLATE §15 / 任务卡 §15（→ Boundary + Hardening）

| 强制项 | WL Plan 落点 |
| --- | --- |
| 版本与锁文件 | §3.1 `runtime_versions.md`；**不改** lockfile |
| 阶段化验收 | docs/spec 分层；Merge gate 不含 frontend/build（§11 + Merge gate） |
| 回滚与恢复 | git revert；无 DB/文件写入回滚 |
| 幂等与重试 | 行字段 + Hardening §7 记录下游 `source_fetch_id` 幂等约定 |
| 安全与隐私 | Boundary 禁止凭证/endpoint；YAML 仅公开 `source_id`/series |
| lineage / as-of | 行 schema + WL-06；`snapshot_lineage_contract.yaml` 字段对齐 |
| 测试质量 | WL-06 语义负向测试；禁止仅存在性断言（任务卡 §13 Red Flags） |

---

## 预期产出文件（编写阶段）

```
specs/model_inputs/
  README.md
  layer1_source_whitelist.yaml
  layer2_source_whitelist.yaml
  layer3_anchor_source_plan.yaml
  layer4_market_source_plan.yaml
  layer5_instrument_source_plan.yaml
docs/quality/model_input_readiness_matrix.md
tests/test_model_input_whitelist.py   # 若项目尚无同类语义测试
```

**行 schema：** 任务卡 §6 必填字段（`input_id`、`layer`、`business_purpose`、`data_domain`、`source_id`、`operation`、`role`、`readiness`、`symbol_or_series`、`window_cap`、`row_cap`、`requires_user_authorization`、`allowed_next_gate`、`forbidden_claims`、`closure_test`、`notes`）。

---

## Merge gate（playbook §8.1）

```bash
uv sync --locked
uv run pytest tests/test_round3_verification_command_matrix.py -q
uv run pytest tests/test_unresolved_item_task_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
uv run pytest tests/test_model_input_whitelist.py -q
uv run pytest -q
uv run ruff check .
uv run python scripts/loop_maintain.py --fix   # 新 docs/specs 路径索引
```

**已知基线：** 全量 `pytest -q` 可能因 `test_dataHealthIntegration_v2Evidence_bundle` 失败；记录于 closure report，不属 WL AC。

**Registry：** proposed delta 可写 task evidence；**禁止**本分支 commit `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` 三件套。

---

## Plan 质检清单（Agent-2，§3.9 / §5.1）

- [x] §3.1 每一行已入本文「§3.1 共用底座索引」或标明摘要
- [x] §3.3 每一行已入「§3.3 B01-WL 分支索引」；零口头遗漏
- [x] `authority_graph.yaml`：`specs/model_inputs/**` 合并后须 `loop_maintain` 补映射（已记入 WL-06）
- [x] `GLOBAL_TASK_TEMPLATE.md` 15 节 + 任务卡 §13 Red Flags → 「GLOBAL_TASK_TEMPLATE §15」+ Hardening + Boundary
- [x] BATCH hardening §3–§7、§2.5/§2.6 边界已写入
- [x] 任务卡 §3 必读 + §9 `/to-issues` 六切片已冻结
- [x] `/to-issues` 垂直切片表完整（Source ID、AC、allowed、verification）
- [x] manifest C01 前置关系（FRED/SP3 依赖 WL）已注明
- [x] 基线红测 `test_dataHealthIntegration_v2Evidence_bundle` 已记录
- [x] 无 registry 三件套 commit 计划
- [x] 复检：遗漏项修回 DEBT.plan 后 **零遗留**

> Plan 质检 Agent-2 · 2026-06-25 · **PASS**

---

## 阻塞项

| 项 | 状态 | 说明 |
| --- | --- | --- |
| WL Plan 本身 | **无阻塞** | 可进入 Plan 质检 |
| FRED / SP3 Execute | **下游等待** | 须 WL 合并后引用 `specs/model_inputs/**` |
| master DH2 集成测红 | **记录项** | 不阻塞 WL docs/spec 编写 |
| registry 三件套 | **主会话队列** | WL agent 不得并发闭合 |

---

## 下游 handoff（主会话）

1. Plan 质检 PASS → 编写 agent 按 WL-01→WL-06 顺序 TDD  
2. 对抗性审计：`audit-adversarial-authority.md` + `BATCH_01_ADVERSARIAL_AUDIT.md`  
3. Track A merge #1 → 解锁 B01-FRED / B01-SP3  
4. Closure report 九项（playbook §6）

---

_Plan 版本：2026-06-25 · B01-WL debt-lite · composer-2.5 · 仅 Plan 阶段_
