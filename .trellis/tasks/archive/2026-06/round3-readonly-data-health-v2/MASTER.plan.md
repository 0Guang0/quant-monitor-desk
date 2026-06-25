# MASTER 计划 — B01-DH2 Read-only Data Health v2

> **Execute 入口** — staged/sandbox only；**不得**声称 production-live。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **必须读原文：** 任务卡 `R3E_readonly_data_health_v2.md` 及四张兄弟 forward 卡（摘要见 Source Context Index）

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `round3-readonly-data-health-v2`                               |
| Playbook ID               | B01-DH2 · Manifest B01-C05                                     |
| 分支                      | `feature/round3-readonly-data-health-v2`                       |
| Worktree                  | `../quant-monitor-desk-wt-b01-dh2`                             |
| 模型                      | `composer-2.5`                                                 |
| 前置                      | v1 `data_health.py` on master；兄弟卡 evidence 可先 fixture    |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md` |

### Batch 01 边界（Playbook §2.5 / §2.6）

| Owns                                                      | Must not                                               |
| --------------------------------------------------------- | ------------------------------------------------------ |
| `data_health.py` / `data_health_cli.py`                   | fetch、live pilot、`source_health_snapshot`、migration |
| `tests/test_data_health_v2.py`、readiness report evidence | `staged_pilot.py` 主体、registry 三件套、WL YAML       |

### Failure modes / 回滚

| 场景                    | 处理                                          |
| ----------------------- | --------------------------------------------- |
| 触发 fetch 或 DB 写     | 中止；revert                                  |
| 修改 forbidden 文件组   | 立即停止                                      |
| 缺 WL 却 PASS whitelist | 停止；修正 BLOCKED 逻辑                       |
| 回滚                    | revert `data_health*` + v2 测试；无 migration |

### 0.1 门控速查

| 项        | 值                                                                 |
| --------- | ------------------------------------------------------------------ |
| 怎么测    | §9 RED→GREEN；`test_ops_data_health.py` + `test_data_health_v2.py` |
| 怎么验收  | §10 + Playbook §8.7                                                |
| 什么叫过  | §2 AC-DH2-\* 全部                                                  |
| prod-path | Tier B：`uv run pytest -q`                                         |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；复用 v1 loader/rules；最小 diff 扩展 profile router。

### 0.3b 测试纪律

五字段 docstring；RED 必须先 FAIL；禁止削弱测试目的（尤其 DH2-BASE）。

### Source Context Index（Playbook §3.1 + §3.7）

#### §3.1 共用底座

| 路径                                                 | 摘要                    | implement |
| ---------------------------------------------------- | ----------------------- | --------- |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`      | §2.5 锁、§8.7 PASS      | [x]       |
| `BATCH_01_TASK_CARD_MANIFEST.md`                     | C01–C05 依赖图          | [x]       |
| `BATCH_01_HARDENING_RULES.md`                        | 禁 production-live 措辞 | [x]       |
| `BATCH_01_MODEL_SOURCE_READINESS/README.md`          | Batch 01 入口与目标     | [x]       |
| `BATCH_01_ADVERSARIAL_AUDIT.md`                      | Batch 对抗性审计结论    | [x]       |
| `ROUND_3_DATA_PRODUCTION_READINESS/README.md`        | Round 3E 入口           | [x]       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                  | Round 3E.4 血缘         | [x]       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3                    | 全局纪律                | [x]       |
| `staged_acceptance_policy.md`                        | 分层验收                | [x]       |
| `production_live_pilot_policy.md`                    | no-mutation             | [x]       |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md` | **只读**                | [x]       |

#### §3.7 B01-DH2 + 兄弟卡

| 路径                                                     | 摘要                    | implement |
| -------------------------------------------------------- | ----------------------- | --------- |
| `R3E_readonly_data_health_v2.md`                         | forward 权威 AC         | [x]       |
| `R3Y_readonly_data_health_v1.md`                         | v1 模式；禁 snapshot    | [x]       |
| `PROMPT_20_feature_round3_readonly_data_health_v1.md`    | legacy 启动             | [x]       |
| `R3D_model_input_whitelist.md`                           | whitelist schema        | [x]       |
| `R3E_fred_authorized_sandbox_pilot.md`                   | FRED evidence 字段      | [x]       |
| `R3E_tdx_manual_probe_addendum.md`                       | TDX 授权边界            | [x]       |
| `R3E_real_data_staged_pilot_v3.md`                       | v3 caps/role            | [x]       |
| `backend/app/ops/data_health.py`                         | **独占扩展**            | [x]       |
| `tests/test_ops_data_health.py`                          | v1 回归 + BASE          | [x]       |
| `specs/contracts/data_quality_rules.yaml`                | rule_id                 | [x]       |
| `specs/contracts/source_conflict_rules.yaml`             | conflict dry-run        | [x]       |
| `specs/contracts/runtime_versions.md`                    | runtime 锁对照          | [x]       |
| `specs/model_inputs/**`                                  | WL 对照；缺失 → BLOCKED | [x]       |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                       | 已闭合项只读            | [x]       |
| `tests/test_staged_pilot.py` · `tests/test_raw_store.py` | staged/raw 回归基线     | [x]       |

---

## 1. 目标

扩展 read-only data health：新增 whitelist / FRED / TDX / staged pilot v3 / rollup profile，输出 PASS/WARN/FAIL/**BLOCKED**，陈述 sandbox clean-write rehearsal 资格；修复 master 基线 integration 红测。

### 1.3 约束

- 只读文件；确定性报告；无 registry commit
- 兄弟 evidence 开发期用 fixture；合并前对齐真实 task evidence 路径

### 1.3a WL 未合并 → BLOCKED + fixture

| 场景                           | Execute 行为                                                          |
| ------------------------------ | --------------------------------------------------------------------- |
| `specs/model_inputs/**` 不存在 | whitelist profile **仅** 返回 `BLOCKED`（禁止猜 scope / 静默 PASS）   |
| DH2-01 测试                    | 用 `tests/fixtures/data_health/whitelist/` 驱动 GREEN；不编写 WL YAML |
| 兄弟卡 evidence 未落地         | 各 profile 用对应 fixture；rollup/gate 用合成 bundle                  |

### 1.3b 兄弟 evidence 路径对齐表（合并前 SSOT）

| 兄弟卡   | 开发期 fixture                                | 合并前 SSOT                                                             |
| -------- | --------------------------------------------- | ----------------------------------------------------------------------- |
| B01-WL   | `tests/fixtures/data_health/whitelist/`       | `specs/model_inputs/**`                                                 |
| B01-FRED | `tests/fixtures/data_health/fred_sandbox/`    | `.trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/` |
| B01-TDX  | `tests/fixtures/data_health/tdx_probe/`       | `.trellis/tasks/round3-tdx-manual-probe/execute-evidence/`              |
| B01-SP3  | `tests/fixtures/data_health/staged_pilot_v3/` | `.trellis/tasks/round3-real-data-staged-pilot-v3/execute-evidence/`     |

> DH2-BASE：`test_dataHealthIntegration_v2Evidence_bundle` 改指向 `tests/fixtures/data_health/v2_integration_bundle/`（自包含 manifest+payload），**保留**日 K 规则断言与 PASS/WARN 语义，禁止删断言换绿。

### 1.5 停止条件

| #   | 事件                  | 处理                        |
| --- | --------------------- | --------------------------- |
| 1   | Plan 未 freeze        | 禁止 start                  |
| 2   | 执行 fetch / DB 写    | 中止                        |
| 3   | 改 forbidden 文件     | revert                      |
| 4   | RED 非本步全库红      | 停当前 §9 步                |
| 5   | 声称 production-live  | 停止                        |
| 6   | 缺 whitelist 却 PASS  | 停止；BLOCKED only          |
| 7   | 为绿而删日 K 规则断言 | 停止；恢复 DH2-BASE purpose |

### 1.6 原计划归并

| 来源                             | 内容                          |
| -------------------------------- | ----------------------------- |
| `R3E_readonly_data_health_v2.md` | 六切片 + 测试 + profile 名    |
| `R3Y` + `PROMPT_20`              | v1 只读基线                   |
| Playbook §8.7                    | PASS 子 AC                    |
| manifest §5                      | Data health v2 readiness 报告 |

---

## 2. 预期结果（AC）

| ID              | 维度     | PASS 条件                                                            | 验证链   |
| --------------- | -------- | -------------------------------------------------------------------- | -------- |
| AC-DH2-PLAN     | Plan     | `validate-plan-freeze` exit 0；切片 DH2-BASE..07                     | freeze   |
| AC-DH2-BASELINE | 基线     | `test_dataHealthIntegration_v2Evidence_bundle` PASS/WARN + 日 K 规则 | §9.0     |
| AC-DH2-PROFILE  | Profile  | 五 profile + rollup 可调用                                           | §9.1–9.5 |
| AC-DH2-BLOCKED  | BLOCKED  | 缺 whitelist → BLOCKED                                               | §9.1     |
| AC-DH2-FRED     | FRED     | 缺 hash/as_of FAIL；macro_supplementary 不关 primary                 | §9.2     |
| AC-DH2-TDX      | TDX      | 无授权 FAIL；production primary FAIL                                 | §9.3     |
| AC-DH2-SP3      | v3       | cap/role 违规 FAIL；cninfo PDF bulk FAIL metadata-only               | §9.4     |
| AC-DH2-ROLLUP   | Rollup   | staged-only → WARN 汇总                                              | §9.5     |
| AC-DH2-GATE     | Gate     | rehearsal 仅全 safety 证据时 true                                    | §9.6     |
| AC-DH2-CLI      | CLI      | `--profile` 路由 v2；未知 profile exit 2；默认 v1 bundle             | §9.7     |
| AC-DH2-BOUND    | 边界     | 无 fetch/DB/migration/registry                                       | Audit    |
| AC-DH2-TEST     | 测试     | 两测试文件语义断言 + 五字段                                          | §10      |
| AC-DH2-PLAYBOOK | Playbook | §8.7 命令绿                                                          | §10      |

---

## 3. 范围

### 3.1 In scope

- `backend/app/ops/data_health.py` — profile router + v2 checkers
- `backend/app/ops/data_health_cli.py` — 可选 `--profile`
- `tests/test_ops_data_health.py` — v1 回归 + DH2-BASE
- `tests/test_data_health_v2.py` — v2 profile 语义测（新建）
- `tests/fixtures/data_health/**` — 各 profile + v2_integration_bundle
- `.trellis/tasks/round3-readonly-data-health-v2/execute-evidence/`

### 3.2 Out / defer

| 项                           | 处理             |
| ---------------------------- | ---------------- |
| registry 三件套              | 主会话 §7.4      |
| `specs/model_inputs/**` 编写 | B01-WL           |
| 兄弟 fetch 实现              | B01-FRED/TDX/SP3 |

### 3.3 禁止修改

- `staged_pilot.py` 主体、`staged_pilot_fetch_ports.py`
- registry 三件套、`specs/model_inputs/**`（只读至 WL 合并）
- `layer5_evidence/**`、migration、frontend

---

## 4. 代码地图

| 路径                                                | 操作               |
| --------------------------------------------------- | ------------------ |
| `backend/app/ops/data_health.py`                    | 扩展 — profile API |
| `backend/app/ops/data_health_cli.py`                | 薄改 — `--profile` |
| `tests/test_data_health_v2.py`                      | 创建               |
| `tests/fixtures/data_health/v2_integration_bundle/` | 创建 — BASE        |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring（playbook §2.2.1）
2. 断言 gate 语义与 forbidden promotion，非仅解析成功

### 5.1 测试文件路径

| 路径                            | 目标             | 测试目的                   | §9      |
| ------------------------------- | ---------------- | -------------------------- | ------- |
| `tests/test_ops_data_health.py` | `data_health.py` | v1 回归 + integration BASE | 9.0     |
| `tests/test_data_health_v2.py`  | `data_health.py` | v2 profile 语义            | 9.1–9.6 |

### 5.2 成功/失败语义

| 能力             | 成功怎么测                   | 失败怎么测           | 场景 |
| ---------------- | ---------------------------- | -------------------- | ---- |
| BASE integration | PASS/WARN + 日 K rule 曾运行 | overall FAIL         | S0   |
| whitelist        | 合法 YAML PASS               | 缺失 BLOCKED         | S1   |
| FRED             | 全字段 PASS                  | 缺 as_of FAIL        | S2   |
| TDX              | validation-only PASS         | 无授权 FAIL          | S3   |
| v3               | 合规 manifest PASS/WARN      | AkShare primary FAIL | S4   |
| rollup           | 多源 WARN 文案               | 混合 FAIL 汇总       | S5   |
| gate             | 全证据 gate true             | 缺 proof false       | S6   |

### 5.3 用例设计

| 测试文件                  | test\_\*                                                   | 断言语义                        | §9  |
| ------------------------- | ---------------------------------------------------------- | ------------------------------- | --- |
| `test_ops_data_health.py` | `test_dataHealthIntegration_v2Evidence_bundle`             | PASS/WARN；日 K 规则；无假 FAIL | 9.0 |
| `test_data_health_v2.py`  | `test_dataHealthV2_whitelist_missing_blocked`              | overall BLOCKED                 | 9.1 |
| 同上                      | `test_dataHealthV2_fred_missingAsOf_fails`                 | FAIL rule                       | 9.2 |
| 同上                      | `test_dataHealthV2_fred_macroSupplementary_noPrimaryClose` | 不关 FRED primary               | 9.2 |
| 同上                      | `test_dataHealthV2_tdx_missingAuth_fails`                  | FAIL/BLOCKED                    | 9.3 |
| 同上                      | `test_dataHealthV2_tdx_productionPrimary_fails`            | FAIL                            | 9.3 |
| 同上                      | `test_dataHealthV2_aksharePrimary_fails`                   | FAIL                            | 9.4 |
| 同上                      | `test_dataHealthV2_cninfoPdfBulk_failsMetadataOnly`        | FAIL                            | 9.4 |
| 同上                      | `test_dataHealthV2_v3CapBreach_fails`                      | FAIL                            | 9.4 |
| 同上                      | `test_dataHealthV2_rollup_stagedOnly_warns`                | WARN                            | 9.5 |
| 同上                      | `test_dataHealthV2_gate_requiresFullSafetyEvidence`        | gate false until complete       | 9.6 |

### 5.4 四层测试

| 层   | 命令                                             | 通过   |
| ---- | ------------------------------------------------ | ------ |
| 单元 | `uv run pytest tests/test_data_health_v2.py -q`  | exit 0 |
| 集成 | `uv run pytest tests/test_ops_data_health.py -q` | exit 0 |
| 管道 | `uv run pytest -q`                               | exit 0 |
| E2E  | N/A — 无 frontend                                | SKIP   |

---

## 6. 验证

| Tier | 命令                                                                                           | 通过   |
| ---- | ---------------------------------------------------------------------------------------------- | ------ |
| A    | `uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q`                  | exit 0 |
| B    | `uv run pytest -q`                                                                             | exit 0 |
| C    | `uv run ruff check backend/app/ops tests/test_ops_data_health.py tests/test_data_health_v2.py` | exit 0 |

---

## 7. Red Flags

| 风险           | 预防                            |
| -------------- | ------------------------------- |
| 网络 fetch     | grep `requests`/`httpx` in diff |
| 写 snapshot 表 | 无 DB import                    |
| 缺证据 PASS    | BLOCKED 路径                    |
| 削弱 BASE 测   | purpose 冻结                    |

---

## 8. 实现顺序（垂直切片）

| 序  | ID       | 交付物（完标准）                             | 依赖       | AC              |
| --- | -------- | -------------------------------------------- | ---------- | --------------- |
| 0   | DH2-BASE | 自包含 v2_integration_bundle；integration 绿 | Boot       | AC-DH2-BASELINE |
| 1   | DH2-01   | whitelist profile + BLOCKED                  | BASE       | AC-DH2-BLOCKED  |
| 2   | DH2-02   | FRED profile                                 | BASE       | AC-DH2-FRED     |
| 3   | DH2-03   | TDX profile                                  | BASE       | AC-DH2-TDX      |
| 4   | DH2-04   | staged pilot v3 profile                      | DH2-01     | AC-DH2-SP3      |
| 5   | DH2-05   | source_readiness_rollup                      | DH2-01..04 | AC-DH2-ROLLUP   |
| 6   | DH2-06   | rehearsal gate 文案强化                      | DH2-05     | AC-DH2-GATE     |
| 7   | DH2-07   | CLI `--profile`（可选）                      | DH2-05     | AC-DH2-CLI      |

---

## 9. 实现步骤（RED/GREEN）

### 9.0 Boot + DH2-BASE — v1 integration 修复

| 字段               | 内容                                                                                                                                                             |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Boot               | Phase 0 逐条 Read `implement.jsonl`（§0.3）；再 Read `research/integration-ledger.md`                                                                            |
| 切片               | DH2-BASE                                                                                                                                                         |
| RED 命令           | `uv run pytest tests/test_ops_data_health.py::test_dataHealthIntegration_v2Evidence_bundle -q`                                                                   |
| GREEN 命令         | 同上                                                                                                                                                             |
| 绑定 Execute Skill | trellis-execute · test-driven-development · gitnexus-impact · karpathy-guidelines · testing-guidelines                                                           |
| 实现要点           | 新增 `tests/fixtures/data_health/v2_integration_bundle/`（manifest + raw JSON）；测试改指向 fixture 或 resolver 支持 evidence-local payload；**不**削弱日 K 断言 |
| 证据               | `execute-evidence/9.0-red.txt` / `9.0-green.txt`                                                                                                                 |
| 已执行             | [x]                                                                                                                                                              |

### 9.1 DH2-01 — Whitelist profile

| 字段               | 内容                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_data_health_v2.py::test_dataHealthV2_whitelist_missing_blocked -q` |
| GREEN 命令         | 同上                                                                                         |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                                         |
| 已执行             | [x]                                                                                          |

### 9.2 DH2-02 — FRED profile

| RED 命令 | `uv run pytest tests/test_data_health_v2.py::test_dataHealthV2_fred_missingAsOf_fails tests/test_data_health_v2.py::test_dataHealthV2_fred_macroSupplementary_noPrimaryClose -q` |
| GREEN 命令 | 同上 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 已执行 | [x] |

### 9.3 DH2-03 — TDX profile

| RED 命令 | `uv run pytest tests/test_data_health_v2.py::test_dataHealthV2_tdx_missingAuth_fails tests/test_data_health_v2.py::test_dataHealthV2_tdx_productionPrimary_fails -q` |
| GREEN 命令 | 同上 |
| 已执行 | [x] |

### 9.4 DH2-04 — Staged pilot v3

| RED 命令 | `uv run pytest tests/test_data_health_v2.py -k "aksharePrimary or cninfoPdfBulk or v3CapBreach" -q` |
| GREEN 命令 | 同上 |
| 已执行 | [x] |

### 9.5 DH2-05 — Rollup

| RED 命令 | `uv run pytest tests/test_data_health_v2.py::test_dataHealthV2_rollup_stagedOnly_warns -q` |
| GREEN 命令 | 同上 |
| 已执行 | [x] |

### 9.6 DH2-06 — Gate statement

| RED 命令 | `uv run pytest tests/test_data_health_v2.py::test_dataHealthV2_gate_requiresFullSafetyEvidence -q` |
| GREEN 命令 | 同上 |
| 已执行 | [x] |

### 9.7 DH2-07 — CLI profile（可选）

| RED 命令 | `uv run pytest tests/test_ops_data_health.py -k "CliProfile" -q` |
| GREEN 命令 | 同上 |
| 已执行 | [x] |

---

## 10. 验收命令（Playbook §8.7）

```bash
uv sync --locked
uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q
uv run pytest -q
uv run ruff check backend/app/ops tests/test_ops_data_health.py tests/test_data_health_v2.py
uv run python -m compileall backend scripts tests
```

---

## 11. Execute Skill 冻结

| Skill                      | 绑定                | 已读 |
| -------------------------- | ------------------- | ---- |
| trellis-execute            | Boot                | [x]  |
| test-driven-development    | §9 RED              | [x]  |
| incremental-implementation | §9 SLICE            | [x]  |
| karpathy-guidelines        | GREEN               | [x]  |
| testing-guidelines         | 写测                | [x]  |
| gitnexus-impact            | 改 symbol           | [x]  |
| trellis-check              | **不用** → Audit A1 | —    |

---

## 12. Plan 质检 §3.10（Agent-2）

| 路径                        | 已入 MASTER/implement  | 摘要                         | 遗漏风险          |
| --------------------------- | ---------------------- | ---------------------------- | ----------------- |
| Playbook §3.1               | [x]                    | 共用底座                     | 低                |
| Playbook §3.7               | [x]                    | DH2+兄弟卡+model_inputs      | 低                |
| R3E 任务卡 §3 必读          | [x]                    | v2 AC + registry×3 + runtime | 低                |
| BATCH_01 README/ADVERSARIAL | [x]                    | Batch 纪律                   | 低                |
| BATCH_01_HARDENING          | [x]                    | 禁 production 措辞           | 低                |
| `specs/model_inputs/**`     | [x] §1.3a BLOCKED      | WL 未合并                    | 低 — fixture 驱动 |
| 兄弟 evidence 路径          | [x] §1.3b 对齐表       | 合并前 SSOT                  | 低                |
| master 红测 DH2-BASE        | [x] §9.0 自包含 bundle | archive 路径断裂             | 低 — Execute 首步 |
| AC-DH2-CLI                  | [x] §2 + §9.7          | 可选 CLI 切片                | 低                |
| `validate-plan-freeze`      | [x] exit 0             | 2026-06-25 复检              | 低                |

**Agent-2 复检：零遗留**

---

## 13. 阻塞项（Plan 冻结时）

| 阻塞                          | 影响                           | 缓解                |
| ----------------------------- | ------------------------------ | ------------------- |
| B01-WL 未合并                 | whitelist 只能 BLOCKED/fixture | 不猜 scope          |
| 兄弟 evidence 未落地          | rollup 用合成 bundle           | 合并前路径对齐表    |
| archive `.audit-sandbox` 缺失 | BASE 红                        | fixture bundle §9.0 |
