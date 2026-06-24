# Repair/Debt Lite Plan — round3-tdx-manual-probe

> **Agent:** B01-TDX (B01-C03) · **Model:** `composer-2.5`  
> **Track:** Phase 8D debt-lite · **Pipeline:** 轻量 Plan → Plan 质检 → 修复/探针 → 对抗性 → 主会话  
> **Plan 阶段约束：** 禁止实现业务代码、禁止 commit registry 三件套。

---

## Source of truth

| Field | Value |
| ----- | ----- |
| Playbook ID | `B01-TDX` |
| Manifest ID | `B01-C03` |
| Legacy card | `B01-L01` → `018C_tdx_pytdx_low_cost_probe.md` |
| Forward card | `R3E_tdx_manual_probe_addendum.md` |
| Audit / registry IDs | `R3-B2.75-REQ2-EM`（**不可本分支关闭**）、`R3-PROMPT14-AKSHARE-VAL-01`（**不可本分支关闭**）、`R2.6-IMPL-8`（只读参照）、TDX disabled-candidate（`B01-C03` owner） |
| Prior 018C closeout | `PROBE_ACCEPT_DISABLED_CANDIDATE`（`tdx_pytdx` registry draft）；`tdx_pytdx_live_probe: PROBE_REDEFERRED` |
| Prior gate slice | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/`（`tdx_live_manual_probe_gate.py` + auth tests） |
| Base branch | `master` |
| Target branch | `debt/round3-tdx-manual-probe` |
| Worktree | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b01-tdx` |
| Trellis task-dir | `.trellis/tasks/round3-tdx-manual-probe/` |
| Evidence path | `.trellis/tasks/round3-tdx-manual-probe/execute-evidence/` |
| Merge coordinator | 主会话（Track A 序 4，可与 FRED 交换） |
| Hardening | `BATCH_01_HARDENING_RULES.md` §1–§10；cap 取 **较小值**（`B01-AUD-02` CLOSED → 018C 赢 addendum） |

---

## Decision（Plan 阶段）

在既有 018C disabled-candidate + live-manual-probe gate 基础上，补齐 **Batch 01 forward addendum** 要求的：

1. `run_tdx_live_manual_probe()` / `tdx_manual_probe.py` 侧车探针（mocked CI 路径 + opt-in live 路径）；
2. `tests/test_tdx_manual_probe.py` 六切片 TDD 覆盖；
3. raw-only 证据与 comparison summary；
4. registry **proposed delta**（主会话批处理，本分支不直接 commit 闭合）。

**不声称：** production-live ready、production primary、Layer2 production source、Eastmoney/AkShare registry 闭合。

---

## Boundary（§2.5 / §2.6 SSOT）

### Owns（可写）

| 组 | 路径 |
| -- | ---- |
| Registry 行（proposed） | `specs/datasource_registry/source_registry.yaml` 中 **`tdx_pytdx` 行** |
| Registry 行（proposed） | `specs/datasource_registry/source_capabilities.yaml` 中 **`tdx_pytdx` 块** |
| Adapter | `backend/app/datasources/adapters/tdx_pytdx.py` |
| Ops 窄改 | `backend/app/ops/tdx_manual_probe.py`（新建）、`tdx_live_manual_probe_gate.py`（已有，可窄改）、`interface_probe_fetch_ports.py` 中 **`TdxPytdxProbeFetchPort` 窄改**、`live_pilot_fetch_ports.py` 仅 TDX 相关窄改 |
| 测试 | `tests/test_tdx_manual_probe.py`（新建）、`tests/test_tdx_live_manual_probe_authorization.py`（已有，可窄改）、`tests/test_interface_probe_018c.py`（窄改若探针契约变化） |
| 任务证据 | `.trellis/tasks/round3-tdx-manual-probe/**` |
| 授权证据（Execute） | `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md`（live 前创建） |

### Must not own

- production primary / automatic fallback / `enabled_by_default: true`
- Layer2 production source 启用（`observation.assert_staged_source` 守卫不得削弱）
- production DB / clean table 写入
- 关闭 `R3-B2.75-REQ2-EM`、`R3-PROMPT14-AKSHARE-VAL-01`
- FRED/baostock/cninfo/akshare registry 行、`staged_pilot.py` 主体、`data_health.py`、`layer5_evidence/**`
- registry 三件套 **直接 commit 闭合**（主会话排队）
- `uv.lock` 变更（pytdx 保持 optional，除非用户另批）

### Production / data boundary

- `write_target`: sandbox / raw / staging only（`.audit-sandbox/` 或 task-local `execute-evidence/`）
- `allow_production_clean_write: false`
- `data/duckdb/quant_monitor.duckdb`: 只读 inspect 或 no-touch 证明

---

## Live 授权（§3 · BATCH_01_HARDENING_RULES §3）

用户已于 **2026-06-24** 口头/会话授权 Batch 01 live 探针。Execute 前须落盘 TDX 专用授权文件并通过 `validate_tdx_live_manual_probe_authorization()`。

**生效 cap：取 018C 较小值（B01-AUD-02），不得使用 addendum §7 的 30 日 / 100 行默认值。**

```yaml
authorization_present: true
authorized_by: user
authorized_at: "2026-06-24"
authorized_session_id: "b01-tdx-live-2026-06-24"  # Execute 时写入授权 MD，须与 gate 校验一致
source_id: tdx_pytdx
write_target: sandbox
allow_production_clean_write: false
raw_only: true
max_network_calls: 5
max_total_rows: 40  # 对齐 tdx_live_manual_probe_gate.MAX_TOTAL_ROWS
authorization_evidence_path: docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md
approved_requests:
  - domain: cn_equity_daily_bar
    operation: fetch_daily_bar
    symbols: ["sh.600519"]
    window: "recent 5 trading days"
    max_rows: 10
  - domain: cn_index_daily_bar
    operation: fetch_index_daily_bar
    symbols: ["000001.SH"]
    window: "recent 5 trading days"
    max_rows: 10
  - domain: security_list
    operation: fetch_security_list
    symbols: ["sh"]
    window: "max_rows=20 per market"
    max_rows: 20
tdx_host: "<user-provided in authorization MD table>"
tdx_port: "<user-provided in authorization MD table>"
forbidden_live_entrypoints:
  - backend.app.ops.interface_probe.run_interface_probe
  - TdxPytdxProbeFetchPort without authorization_verified=true
registry_rows_must_remain_open:
  - R3-B2.75-REQ2-EM
  - R3-PROMPT14-AKSHARE-VAL-01
```

**Plan 阶段缺口：** 授权 MD 文件尚不存在；`tdx_host`/`tdx_port` 待用户填入授权表。无文件时 CI 仅跑 mocked 路径，live 记录 `TDX_PROBE_FAIL_AUTH_MISSING` 或 `TDX_PROBE_REDEFERRED`。

---

## 探针状态枚举（addendum §6）

```text
TDX_PROBE_PASS_RAW_ONLY
TDX_PROBE_FAIL_AUTH_MISSING
TDX_PROBE_FAIL_DEPENDENCY
TDX_PROBE_FAIL_NETWORK
TDX_PROBE_FAIL_SCHEMA
TDX_PROBE_FAIL_VALIDATION
TDX_PROBE_REJECTED
TDX_PROBE_REDEFERRED
```

---

## 权威必读索引（§3.1 共用 + §3.5 TDX）

> Plan 质检须逐行核对；下表为 DEBT.plan 无损摘要。Execute 前须 Read 原文件。

### §3.1 共用底座

| 路径 | Plan 摘要 | 对本分支含义 |
| ---- | --------- | ------------ |
| `docs/quality/coordination/BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | Batch 01 七路协调、§2.5 文件锁、§5.2 TDX 精简线 | 本分支独占 `tdx_pytdx` registry 行 + adapter + `ops/*tdx*` |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/**` | Batch 入口 + manifest + hardening + adversarial | 任务边界 SSOT |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_TASK_CARD_MANIFEST.md` | manifest C03 + §5 registry ownership | TDX 仅 disabled-candidate；不可关 EM/AkShare |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/README.md` | Round 3D/3E 父包；closure 九项 | 合并后主会话更新 handoff |
| `docs/quality/ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.3/§2.6 | 批次地图与串行语义 | TDX 与 023 分轨 |
| `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6/§8 | Phase 8D worktree 切片 | debt-lite 模板来源 |
| `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D | 轻量计划最小产物 | 本 DEBT.plan 结构 |
| `agent-toolchain.md` | GitNexus impact/detect_changes；Plan→to-issues | Execute 改符号前 impact |
| `docs/quality/coordination/BATCH_01_ADVERSARIAL_AUDIT.md` | B01-AUD-02 cap 冲突已 CLOSED | **018C cap 优先** |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md` | §3 授权 YAML、§4 registry 闭合、§5 角色上限 | TDX 最高角色：validation-only candidate |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/FIRST_BATCH_SELF_CHECK.md` | 批次自检 | TDX optional dep + no live CI |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | `R3-B2.75-REQ2-EM` 等 OPEN | 不可误关 EM/AkShare 行 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | 同上 pair | 闭合须 exact evidence |
| `docs/RESOLVED_ISSUES_REGISTRY.md` | 已闭合项对照 | 避免误将 TDX 探针当作 EM/AkShare 闭合证据 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | ID→分支映射 | 主会话 §7.4 更新 |
| `docs/quality/ROUND3_HANDOFF.md` | 交接 | 合并后 checkpoint |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` | Round 3E.2 | 路线图锚点 |
| `docs/quality/staged_acceptance_policy.md` | staged 验收 | raw-only 首过 |
| `docs/quality/production_live_pilot_policy.md` | live pilot 阶段门 | 授权字段对齐 §3 YAML |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` | 018C 不打开 production-live | 探针 PASS ≠ live ready |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md` | 五字段 docstring | 新测必备 |
| `docs/ops/verification_commands.md` | Round 3 gate 命令 | §11 验收子集 |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | 全局执行 | no production write |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | 全局测试 | mocked CI 默认 |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | 资源上限 | ResourceGuard 对齐 |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` | 15 节模板 | Red Flags 对照 |
| `specs/contracts/runtime_versions.md` | 运行时版本 | pytdx optional |
| `specs/contracts/write_contract.yaml` | 写契约 | no clean write |
| `specs/contracts/resource_limits.yaml` | eco/normal/batch caps | 探针行数上限 |
| `specs/contracts/snapshot_lineage_contract.yaml` | lineage | evidence 含 fetch_id/hash/as_of |
| `docs/architecture/module_boundary_matrix.md` | 模块边界 | adapter/ops 窄改 |
| `docs/architecture/MIGRATION_MAP.md` | 迁移地图 | 向下追溯邻接 |
| `specs/context/authority_graph.yaml` | 权威图 | Plan 质检核对模块 |

### §3.5 B01-TDX 专用

| 路径 | Plan 摘要 | 对本分支含义 |
| ---- | --------- | ------------ |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_tdx_manual_probe_addendum.md` | Forward 执行 addendum；六切片；§11 验收 | **主 AC 来源**（cap 被 018C 收紧） |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md` | Legacy sidecar probe；三 operation；external ref 边界 | cap SSOT；不可关 Request 2 |
| `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md` | 018C landing | henrylin99/tdx_quant 形状参考 |
| `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md` | Live probe 规划卡 | 与 PROMPT_10 对齐 |
| `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_10_debt_r3b275_018c_live_manual_probe_plan.md` | PROMPT_10 约束 | gate 已落地，runner 待实现 |
| `backend/app/datasources/adapters/tdx_pytdx.py` | Skeleton adapter；三 domain | 窄扩展 parser，非 factory Primary |
| `backend/app/ops/staged_pilot.py` | Staged pilot | **只读**；不扩 TDX production 路径 |
| `backend/app/ops/live_pilot_fetch_ports.py` | Live fetch ports | TDX 窄改仅限探针接线 |
| `backend/app/ops/tdx_live_manual_probe_gate.py` | Fail-closed 授权门；`APPROVED_PROBE_ENVELOPES` | 已有；与 §3 YAML 一致 |
| `backend/app/ops/interface_probe_fetch_ports.py` | `TdxPytdxProbeFetchPort` | live 须经 gate；默认 blocked |
| `backend/app/ops/interface_probe.py` | 018C sidecar runner | **禁止**用于 TDX live（gate 明示） |
| `backend/app/layer2_sensors/observation.py` | `assert_staged_source` 拒 `tdx_pytdx` | 测试须保持守卫 |
| `backend/app/datasources/route_planner.py` | 路由预览 | TDX fail-closed 回归 |
| `specs/datasource_registry/source_registry.yaml` | `tdx_pytdx` disabled/validation | proposed delta only |
| `specs/datasource_registry/source_capabilities.yaml` | `proposed_disabled_source` | proposed delta only |
| `specs/contracts/source_route_contract.yaml` | DISABLED_SOURCE 等状态 | 路由矩阵测试 |
| `specs/contracts/source_capability_contract.yaml` | 能力断言 | OperationDisabledError |
| `specs/contracts/datasource_service_contract.yaml` | 服务门面 | route-before-fetch |
| `specs/contracts/data_adapter_contract.md` | adapter 契约 | skeleton 边界 |
| `tests/test_tdx_live_manual_probe_authorization.py` | 授权门控（无网络） | 已有 5 测；可扩展 |
| `tests/test_interface_probe_018c.py` | disabled-by-default / no Primary | 基线回归 |
| `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md` | 未来 Execute 计划 SSOT | `run_tdx_live_manual_probe` 规格 |
| `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/authorization_checklist.md` | 018C 授权清单 §4 envelope | 与 gate `APPROVED_PROBE_ENVELOPES` 一致 |
| `tests/test_source_capabilities.py` | capability 断言基线 | addendum §11 验收子集 |
| `tests/test_source_route_planner.py` | 路由矩阵基线 | TDX fail-closed 回归 |
| `tests/test_layer2_sensor_loader.py` | Layer2 守卫 | builder 拒 `tdx_pytdx` staged 路径 |
| `.trellis/tasks/06-22-round3-018c-low-cost-probe/execute-evidence/interface_probe_decision.md` | 018C 决策 | `PROBE_ACCEPT_DISABLED_CANDIDATE` |
| Registry OPEN 行：`R3-B2.75-REQ2-EM` | Eastmoney hist 仍 OPEN | 测试断言不可自动闭合 |
| Registry OPEN 行：`R3-PROMPT14-AKSHARE-VAL-01` | AkShare validation OPEN | 同上 |
| Registry OPEN 行：`R2.6-IMPL-8` | QMT/Yahoo/xqshare E2E | 只读；本任务不触及 |

---

## Plan 质检 checklist（§3.9 · Agent-2 复检 2026-06-25）

- [x] §3.1 + §3.5 **每一行** 已入 DEBT.plan 或标明无损摘要（含 manifest、RESOLVED、验收测、authorization_checklist）
- [x] `authority_graph.yaml` 已索引（§3.1）
- [x] `GLOBAL_TASK_TEMPLATE.md` 15 节 → addendum §1–§15 + DEBT Red flags / Closure report 已覆盖
- [x] hardening §3–§7 + §8 负向测试要点已写入 Boundary / §3 YAML / slices
- [x] 任务卡 addendum §3 必读 + legacy 018C + PROMPT_10 无缺口
- [x] `/to-issues` vertical slices TDX-01..06 已冻结
- [x] 遗漏项已写回 DEBT.plan；**复检零 Plan 遗留**

## Plan 质检索引（§3.10 · Agent-2 必填）

| 路径 / 检查项 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
| ------------- | -------------- | -------- | -------- |
| Playbook §3.1（协调/审计/Registry/Handoff/质量门/全局/契约/架构） | 是 | 27 行 + manifest + RESOLVED | 低 |
| Playbook §3.5（addendum/018C/R3D/PROMPT_10/adapter/observation/OPEN 行） | 是 |  playbook 7 组 + 扩展 gate/测/契约共 32 行 | 低 |
| Playbook §2.5 文件锁 | 是 | 独占 `tdx_pytdx` 行 + adapter + `ops/*tdx*` | 中：registry commit 须主会话排队 |
| Playbook §2.6 B01-TDX | 是 | Boundary Owns/Must-not | 低 |
| `BATCH_01_TASK_CARD_MANIFEST.md` C03 + §5 | 是 | Source of truth + Registry proposed delta | 低 |
| `BATCH_01_HARDENING_RULES.md` §3 授权 YAML | 是 | §3 YAML；`authorization_present: true` @ 2026-06-24 | 低（MD 为 Execute 产出） |
| `BATCH_01_ADVERSARIAL_AUDIT.md` B01-AUD-02 | 是 | 较小 cap；018C 赢 addendum | 低 |
| Cap：018C vs addendum §7 | 是 | **5 trading days / max_rows 10 / security list 20 / max_calls 5 / total 40** | 低 |
| Live gate `APPROVED_PROBE_ENVELOPES` | 是 | 与 §3 YAML、`authorization_checklist.md` §4 一致 | 低 |
| `authorization_checklist.md` | 是 | §3.5 索引；BLK-TDX-01 落盘指引 | 低 |
| 授权 MD `…_2026-06-24.md` | Execute 产出 | Plan 非阻塞；mocked CI 路径完整 | 低（live opt-in 前须落盘） |
| addendum §9 六切片 + §11 验收 | 是 | Vertical slices + Merge gate | 低 |
| addendum §13 Red Flags | 是 | Red flags 节 | 低 |
| addendum §14–§15 输出/审计项 | 是 | Closure report 九项 + `uv.lock` 禁改 | 低 |
| `run_tdx_live_manual_probe` / `tdx_manual_probe.py` | Execute | Slice TDX-01..05；基线盘点已标缺失 | **Execute 工作项，非 Plan 缺口** |
| `tests/test_tdx_manual_probe.py` | Execute | Slice TDX-01..06 RED 起点 | **Execute 工作项，非 Plan 缺口** |

---

## 基线盘点（worktree @ `debt/round3-tdx-manual-probe`）

| 资产 | 状态 |
| ---- | ---- |
| `tdx_pytdx` registry/capability draft | 已存在；disabled + validation_only |
| `TdxPytdxAdapter` skeleton | 已存在；未 factory 注册为 Primary |
| `tdx_live_manual_probe_gate.py` | 已存在；018C envelope + host/port 绑定 |
| `test_tdx_live_manual_probe_authorization.py` | 已存在；5 测绿 |
| `TdxPytdxProbeFetchPort` | 已存在；无授权则 `USER_AUTH_REQUIRED` |
| `test_interface_probe_018c.py` | 已存在；disabled/no Primary 回归 |
| `observation.assert_staged_source` | 已拒 `tdx_pytdx` Layer2 |
| `tdx_manual_probe.py` / `run_tdx_live_manual_probe()` | **缺失** |
| `tests/test_tdx_manual_probe.py` | **缺失** |
| `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md` | **缺失** |
| registry commit | **禁止本阶段** |

---

## Vertical slices（/to-issues · debt-lite）

| Slice | Source ID / AC | Allowed files | Forbidden | Verification（RED→GREEN） | Evidence |
| ----- | -------------- | ------------- | --------- | --------------------------- | -------- |
| **TDX-01** Authorization gate | addendum §9.1；hardening §3 | `tdx_live_manual_probe_gate.py`、`tdx_manual_probe.py`、`test_tdx_manual_probe.py`、`test_tdx_live_manual_probe_authorization.py` | `live_pilot.validate_authorization` 复用；无授权 live 网络 | RED: live runner 无 payload 拒绝；GREEN: gate 集成 + 状态 `TDX_PROBE_FAIL_AUTH_MISSING` | `execute-evidence/tdx-01-auth-red.txt` / `-green.txt` |
| **TDX-02** Mocked equity daily | addendum §9.2；018C §4.2 | `tdx_manual_probe.py`、`tdx_pytdx.py`（窄）、`interface_probe_fetch_ports.py`（mock 注入）、`test_tdx_manual_probe.py` | production write；enable default | RED: mocked equity 写出 raw JSON 含 source_id/symbol/dates/hash；GREEN: parser + manifest | `execute-evidence/tdx-02-equity-*` |
| **TDX-03** Mocked index daily | addendum §9.3 | 同上 + `parse_index_instrument` | Layer2 production 路径 | RED: index `000001.SH` raw evidence；GREEN: validation-only 保持 | `execute-evidence/tdx-03-index-*` |
| **TDX-04** Security list cap | addendum §9.4；cap **20**（018C） | `tdx_manual_probe.py`、`test_tdx_manual_probe.py` | >20 行静默截断无状态 | RED: 超 cap 显式 fail/truncate 状态；GREEN: capped list probe | `execute-evidence/tdx-04-list-*` |
| **TDX-05** Comparison report | addendum §9.5 | `tdx_manual_probe.py`、task evidence only | 自动覆盖 baostock/akshare；clean write | RED: 报告区分 comparable / missing / conflict；GREEN: summary MD/JSON | `execute-evidence/tdx-05-compare-*` |
| **TDX-06** Registry closeout | addendum §9.6；manifest §5 | `research/registry_proposed_delta.yaml`（**proposed**）、`test_tdx_manual_probe.py`（负向断言） | **commit** registry；关 `R3-B2.75-REQ2-EM` | RED: TDX success 不闭合 EM/AkShare；GREEN: decision `PROBE_*` + rationale | `execute-evidence/tdx-06-registry-*`、`interface_probe_decision.md`（Batch 01 版） |

**Live opt-in（跨 TDX-02..04，非默认 CI）：** 授权 MD 落盘 + `run_tdx_live_manual_probe --live`（或等价 flag）→ bounded fetch → `TDX_PROBE_PASS_RAW_ONLY` 或 failure taxonomy；须 `no_mutation_proof.md`。

---

## Explicit non-goals

- Production primary / Layer2 production source / automatic fallback
- 关闭 Eastmoney hist 或 AkShare validation registry 行
- QMT / xqshare / Yahoo 集成
- 全市场 / 全历史 / 分钟线
- registry 三件套直接 merge commit（主会话 §7.4）
- Plan 阶段写实现代码或改 registry 已提交状态

---

## Merge gate（§8.2 · addendum §11）

### Targeted

```bash
uv sync --locked
uv run pytest tests/test_tdx_manual_probe.py -q
uv run pytest tests/test_tdx_live_manual_probe_authorization.py -q
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_layer2_sensor_loader.py::test_stagedSource_rejectsTdxPytdx_viaBuilder -q
uv run pytest tests/test_interface_probe_018c.py -q
uv run ruff check backend/app/datasources backend/app/ops tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py
```

### Full（主会话 Done）

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
uv run python scripts/loop_maintain.py   # 若触达 docs/specs
```

### Closure report（父 README §5 九项）

Execute/主会话须填：branch、changed/not-changed、测试结果、ResourceGuard、授权状态、DB no-mutation、registry proposed/resolved、残余风险。

---

## Registry proposed delta（Plan 仅记录 · 禁止本阶段 commit）

| 行 / 家族 | 本分支动作 | 证据要求 |
| --------- | ---------- | -------- |
| TDX disabled-candidate | `PROBE_PASS_RAW_ONLY` → 保持 disabled/validation；或 `PROBE_REDEFERRED` + owner/phase | `interface_probe_decision.md` |
| `R3-B2.75-REQ2-EM` | **保持 OPEN**；decision 明示「TDX 不闭合 EM hist」 | 负向测试 |
| `R3-PROMPT14-AKSHARE-VAL-01` | **保持 OPEN** | 负向测试 |
| `R2.6-IMPL-8` | 不触及 | — |

---

## 阻塞项（Plan → Execute 交接）

| ID | 阻塞 | Owner | 解除条件 |
| -- | ---- | ----- | -------- |
| **BLK-TDX-01** | `docs/quality/tdx_pytdx_live_manual_probe_authorization_2026-06-24.md` 不存在 | 用户/协调者 | 按 `authorization_checklist.md` 落盘；含 host/port/session_id。**Plan 非阻塞**；mocked + `TDX_PROBE_REDEFERRED` 可先行 |
| **BLK-TDX-02** | `run_tdx_live_manual_probe()` / `tdx_manual_probe.py` 未实现 | B01-TDX Execute | Slice TDX-01..05 GREEN |
| **BLK-TDX-03** | `tests/test_tdx_manual_probe.py` 不存在 | B01-TDX Execute | 六切片 RED 文件齐全 |
| **BLK-TDX-04** | TDX `host:port` 未知 | 用户 | 写入授权 MD 表格 |
| **BLK-TDX-05** | `pytdx` 可选依赖可能未安装 | 环境 | live 时 `TDX_PROBE_FAIL_DEPENDENCY`；CI mocked 不受影响 |
| **BLK-TDX-06** | Registry 须主会话批处理 | 主会话 | 本分支仅交 `registry_proposed_delta.yaml` |

**非阻塞：** 无 TDX 授权时仍可完成 mocked 路径 + `TDX_PROBE_REDEFERRED` closeout（playbook §5.2 · addendum §11）。

---

## Red flags（addendum §13 · 立即停止）

- TDX `enabled_by_default: true` 或 Primary 晋升
- 无授权 live 网络调用
- 全市场 security list / 超 cap 拉取
- TDX 成功用于闭合 EM/AkShare 行
- production DB / clean table 写入
- 默认 CI 依赖 live TDX server

---

## 下一步（Plan 完成后）

1. **Plan 质检** agent：§3.9/§3.10 零遗留复检  
2. **Execute** agent：按 Vertical slices TDX-01→06 严格 TDD  
3. **对抗性审计**：`audit-adversarial-authority.md` + `BATCH_01_ADVERSARIAL_AUDIT.md`  
4. **主会话**：§7.2 序 4 合并 + registry 批处理

---

_Plan 版本：2026-06-25 · B01-TDX debt-lite · composer-2.5 · Plan 质检 Agent-2 PASS（零 Plan 遗留）_
