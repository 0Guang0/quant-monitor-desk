# 执行索引 — R3FR-03 TDX Provider Refactor

> P0i：**索引完整**（v4 输入清单门禁 · 对抗性 Plan 审计 2026-06-26 已闭合）  
> **读者：Execute + Audit**  
> **冻结任务卡：** `frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md`  
> **审计矩阵：** `AUDIT.plan.md`  
> **对抗性审计：** `research/adversarial-plan-audit.report.md`

---

## 0. 冻结元数据

| 字段         | 值                                                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-26-round3fr-tdx-provider`                                                                                                          |
| source_card  | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_03_TDX_PROVIDER_REFACTOR.md` |
| frozen_card  | `frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md`                                                                                              |
| batch / item | `ROUND_3_REFERENCE_ADOPTION_REFACTOR` / `R3FR-03`                                                                                      |
| 分支         | `refactor/round3fr-tdx-provider`（**禁止 master / R3FR-05 分支 Execute**）                                                             |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3F-R · `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`                                          |

### 0.1 血缘（活任务卡 AC ↔ Step ↔ 测试函数）

| AC                         | Step | 测试 / 命令（函数名须 TDD RED 首跑）                                                                                   | 验证链 |
| -------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------- | ------ |
| AC-TDX-01 缺 pytdx         | 9.1  | `tests/test_tdx_pytdx_port.py::test_tdxPytdxPort_missingPytdx_returnsDisabledSource`                                   | §2     |
| AC-TDX-02 live 授权        | 9.4  | `test_tdx_live_manual_probe_authorization.py` + `test_tdxPytdxPort_withoutAuth_raisesUserAuthRequired`                 | §2     |
| AC-TDX-02 mocked 默认      | 9.5  | `test_tdx_manual_probe.py`（mocked 路径全绿）                                                                          | §2     |
| AC-TDX-03 拒绝 minute/scan | 9.3  | `test_tdxPytdxPort_rejectsMinuteBars` · `test_tdxPytdxPort_rejectsFullMarketScan` · `test_tdxPytdxPort_rejectsOverCap` | §2     |
| AC-TDX-04 raw hash         | 9.2  | `test_tdxNormalizer_equityManifest_hasRequiredFieldsAndHash`                                                           | §2     |
| AC-TDX-04 编排 evidence    | 9.5  | `test_tdx_manual_probe.py`（comparison/hash 子集）                                                                     | §2     |
| AC-TDX-05 guardrails       | 9.7  | `test_reference_adoption_guardrails.py`                                                                                | §2     |
| AC-TDX-06 registry caps    | 9.6  | `test_tdxPytdx_capsMatchTaskCard` · `test_tdxRoute_tdxPytdx_disabledByDefault`                                         | §2     |
| Done 完整形态              | 9.7  | §2.1 Tier B + `loop_maintain.py`                                                                                       | §2.1   |

### 0.2 Caps 权威（闭合 ADV-01）

| 项                                 | 值                                                                                                                                                                                 |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SSOT**                           | 活任务卡 / frozen §5 `Default caps`                                                                                                                                                |
| **supersedes**                     | 018C 授权 MD 与 gate 中 equity/index `max_rows=10` → **3**（R3FR-03 provider port）                                                                                                |
| **同步点（9.4 + 9.6 同一 GREEN）** | `tdx_live_manual_probe_gate.py` · `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md` · `tdx_manual_probe.py` 常量 · `source_capabilities.yaml` `resource_caps` |
| **不闭合**                         | `UNRESOLVED` B01-C03 live `PROBE_REDEFERRED`（host 占位）；本任务仅强化 port                                                                                                       |

---

## 1. 步骤与证据（Execute）

| Step | 切片                  | RED 命令                                                                                                                                                                                                | GREEN 命令                                      | 证据                                   |
| ---- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------- |
| 9.0  | Boot 基线             | `uv run pytest tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q`（基线捕获；**非** TDD 新测）                                                                        | 同左                                            | `execute-evidence/9.0-{red,green}.txt` |
| 9.1  | port + PortError      | `uv run pytest tests/test_tdx_pytdx_port.py::test_tdxPytdxPort_missingPytdx_returnsDisabledSource -q`（须先 RED）                                                                                       | 同左                                            | `9.1-{red,green}.txt`                  |
| 9.2  | normalizer            | `uv run pytest tests/test_tdx_pytdx_port.py::test_tdxNormalizer_equityManifest_hasRequiredFieldsAndHash -q`                                                                                             | 同左                                            | `9.2-{red,green}.txt`                  |
| 9.3  | caps 拒绝             | `uv run pytest tests/test_tdx_pytdx_port.py -k "rejectsMinute or rejectsFullMarket or rejectsOverCap" -q`                                                                                               | 同左                                            | `9.3-{red,green}.txt`                  |
| 9.4  | 授权 + forbidden live | `uv run pytest tests/test_tdx_pytdx_port.py::test_tdxPytdxPort_withoutAuth_raisesUserAuthRequired tests/test_tdx_live_manual_probe_authorization.py::test_tdxLiveGate_forbiddenDirectPortInvocation -q` | 同左全绿                                        | `9.4-{red,green}.txt`                  |
| 9.5  | 编排瘦身              | `uv run pytest tests/test_tdx_manual_probe.py -q`                                                                                                                                                       | 同左                                            | `9.5-{red,green}.txt`                  |
| 9.6  | registry + route      | `uv run pytest tests/test_tdx_pytdx_port.py::test_tdxPytdx_capsMatchTaskCard tests/test_source_capabilities.py -k tdx -q`                                                                               | 同左                                            | `9.6-{red,green}.txt`                  |
| 9.7  | guardrails 收尾       | `uv run pytest tests/test_reference_adoption_guardrails.py tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py tests/test_tdx_pytdx_port.py -q`                            | 同左 + `uv run python scripts/loop_maintain.py` | `9.7-{red,green}.txt`                  |

> 每步 GREEN：`incremental-implementation` → `uv run pytest -q`。新测模块登记：`uv run python scripts/loop_maintain.py --fix`。

---

## 2. AC ↔ 测试 / 验收

| AC        | 测试                                                                             | 通过条件                                    |
| --------- | -------------------------------------------------------------------------------- | ------------------------------------------- |
| AC-TDX-01 | `test_tdx_pytdx_port.py::test_tdxPytdxPort_missingPytdx_returnsDisabledSource`   | `PortError` status `DISABLED_SOURCE`        |
| AC-TDX-02 | live auth + `test_tdxPytdxPort_withoutAuth_raisesUserAuthRequired` + mocked 全绿 | 无授权不联网                                |
| AC-TDX-03 | `rejectsMinute` / `rejectsFullMarket` / `rejectsOverCap`                         | 显式拒绝                                    |
| AC-TDX-04 | normalizer hash 测试 + probe evidence 子集                                       | manifest + content/schema hash              |
| AC-TDX-05 | `test_reference_adoption_guardrails.py`                                          | 无 `参考项目/**` import                     |
| AC-TDX-06 | `test_tdxPytdx_capsMatchTaskCard` + route disabled                               | YAML caps = §5；`enabled_by_default: false` |

### 2.1 Tier

| 层  | 命令                                                            |
| --- | --------------------------------------------------------------- |
| A   | 任务卡 §11 两档 targeted pytest                                 |
| B   | `uv run pytest -q`                                              |
| C   | `uv run python scripts/loop_maintain.py`（touch `backend/` 后） |

---

## 3. 必须读原文（manifest · 自动生成 jsonl）

| path                                                                                                                                    | manifest   | audience | for             |
| --------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | --------------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                                   | must-read  | execute  | 9.0             |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                    | must-read  | execute  | 9.0             |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                                   | must-read  | execute  | 9.3 caps        |
| `specs/contracts/runtime_versions.md`                                                                                                   | must-read  | execute  | Boot            |
| `docs/quality/staged_acceptance_policy.md`                                                                                              | must-read  | execute  | Tier            |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                    | must-read  | both     | 9.7             |
| `specs/datasource_registry/source_registry.yaml`                                                                                        | must-read  | execute  | 9.6             |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                    | must-read  | execute  | 9.6             |
| `backend/app/datasources/adapters/fetch_port.py`                                                                                        | must-read  | execute  | 9.1 PortError   |
| `backend/app/datasources/adapters/tdx_pytdx.py`                                                                                         | must-read  | execute  | 9.2             |
| `backend/app/ops/tdx_live_manual_probe_gate.py`                                                                                         | must-read  | execute  | 9.4             |
| `backend/app/ops/tdx_manual_probe.py`                                                                                                   | must-read  | execute  | 9.5             |
| `backend/app/ops/interface_probe_fetch_ports.py`                                                                                        | must-read  | execute  | 9.5             |
| `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md`                                                                  | must-read  | execute  | 9.4 caps        |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                            | audit-only | audit    | B01-C03         |
| `MIGRATION_MAP.md`                                                                                                                      | audit-only | audit    | 路径导航        |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                                 | audit-only | audit    | 追溯            |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md` | must-read  | both     | 文件锁/rollback |
| `.trellis/tasks/06-26-round3fr-tdx-provider/research/integration-ledger.md`                                                             | must-read  | execute  | 打包            |

---

## 4. 已并入冻结任务卡

| 来源                     | 章节                       |
| ------------------------ | -------------------------- |
| `R3FR_03` + §5 caps 权威 | frozen §1–§2、§5.1、§7–§14 |
| `vertical-slices.md`     | frozen §9                  |
| rollback / registry 归属 | frozen §8、§15             |

---

## 5. Audit 追溯集

| 类别         | 文件                                                                      |
| ------------ | ------------------------------------------------------------------------- |
| 活任务卡     | `R3FR_03_TDX_PROVIDER_REFACTOR.md`                                        |
| frozen       | `frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md`                                 |
| playbook     | `BATCH_3FR_COORDINATOR_PLAYBOOK.md`                                       |
| roadmap      | `PROJECT_IMPLEMENTATION_ROADMAP.md`                                       |
| unresolved   | `UNRESOLVED_ITEM_TASK_COVERAGE.md`                                        |
| 对抗性审计   | `research/adversarial-plan-audit.report.md`                               |
| R3FR-05 并行 | **R3FR-03 独占 `tdx_pytdx` registry 行**；R3FR-05 不得改 caps；合并序 3→4 |

---

## 6. 机器路由

`context_pack.json` — `uv run python scripts/context_router.py --task .trellis/tasks/06-26-round3fr-tdx-provider`（Boot 前复跑；空 `modules` 时以 §3 manifest 为准）。

Execute Boot：`frozen` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条。
