# MASTER 计划 — B01-C04 Round 3 staged real-data pilot v3

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **WL 依赖：** Execute 前 `specs/model_inputs/**` 必须存在（B01-WL 合并或只读 rebase）。

---

## 0. 元信息

| 字段 | 值 |
| ---- | -- |
| 任务 slug | `06-25-round3-real-data-staged-pilot-v3` |
| Playbook ID | `B01-SP3` / Manifest `B01-C04` |
| 分支 | `feature/round3-real-data-staged-pilot-v3` |
| Worktree | `../quant-monitor-desk-wt-b01-sp3` |
| 前置 | **B01-WL** `chore/round3-model-input-whitelist` → `specs/model_inputs/**` |
| manifest_protocol_version | `3` |
| `EVIDENCE_ROOT` | `.trellis/tasks/06-25-round3-real-data-staged-pilot-v3/execute-evidence/` |
| analysis_waiver | `false` |
| 原计划 | `research/source-index.md` · `research/original-plan-trace.md` |
| model | `composer-2.5` |

### Batch 01 边界摘要（Playbook §2.5 / §2.6）

| Owns（可写） | Must not own |
| ------------ | ------------ |
| `staged_pilot.py` 主体 v3 路径、`staged_pilot_fetch_ports.py`（非 FRED 独占端口） | FRED/TDX/QMT/Yahoo production |
| baostock/cninfo/akshare registry **proposed delta**（非 fred/tdx 行） | production clean write |
| `storage/staged_evidence.py` 窄改 | `specs/model_inputs/**` 写入（B01-WL） |
| `tests/test_real_data_staged_pilot_v3.py` + v3 evidence | `data_health.py` 主体 |
| | registry 三件套 **直接 commit**（主会话排队） |

### Hardening 摘要（BATCH_01_HARDENING_RULES §1–§7）

1. 输出语言仅允许 raw/staging/sandbox evidence、source readiness assessed
2. Live fetch 须 hardening §3 授权 YAML（用户 2026-06-24 已批；caps 见 §0 caps）
3. `akshare` 最高角色 validation-only；`baostock` A 股日线 sandbox primary 候选；`cninfo` metadata-only
4. `R3-PROMPT14-AKSHARE-VAL-01` 须 exact evidence 或 re-defer
5. `R3-B2.75-REQ2-EM` 不得侧路关闭

### 默认 v3 caps（可 §9.1 冻结到 JSON；WL 更严则取更严）

| 项 | 默认 |
| --- | ---- |
| `pilot_id` | `r3e-staged-pilot-v3-20260625` |
| baostock symbols | 5–20（来自 WL） |
| cninfo symbols/issuers | 5–20（metadata only） |
| akshare comparison symbols | 2–10（validation-only） |
| trade/calendar window | 30–120 days |
| max_rows_total | baostock 2000 / cninfo 500 / akshare 1000 |
| `max_network_calls_per_run` | 50 |
| `sandbox_root` | `.audit-sandbox/r3e-staged-pilot-v3/` |
| `production_clean_write` | `false` |

### 0.1 门控速查

| 项 | 值 |
| --- | --- |
| 怎么测 | §9 RED→GREEN；`tests/test_staged_pilot.py` 回归 + `tests/test_real_data_staged_pilot_v3.py` |
| 怎么验收 | playbook §8.6 + §6 Tier A/B |
| 什么叫过 | §2 全部 AC + WL trace + 无 production-live 声称 |
| prod-path | Tier B：`uv run pytest -q` 全库（§9.7） |
| 6.pre | `research/gitnexus-execute-summary.md` |
| WL 门禁 | Boot：`test -d specs/model_inputs` 或等价；失败 → §1.5 #5 |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §9.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；每 §9.x 步开始前对照 ladder
2. 写业务代码前：YAGNI → 复用 v2 `staged_pilot.py` 路径 → 最小 diff
3. TDD：RED → karpathy-guidelines → testing-guidelines → GREEN
4. 禁止新依赖；有意简化用 `ponytail:` 注释

### 0.3b Execute 工程纪律 — 测试

1. 五字段 docstring（覆盖范围/测试对象/目的/验证点/失败含义）
2. 每步 GREEN 后 Read `incremental-implementation`；全量 pytest 仅 §9.7
3. **禁止弱化测试目的**

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + `research/integration-ledger.md` 为准。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute + ponytail。Phase 0：确认 specs/model_inputs/** 存在，否则 STOP §1.5#5。逐行 implement.jsonl → §9.x → Audit。勿 finish-work。
```

---

## 1. 目标

在 v2 staged pilot 基础上，按 **model input whitelist** 扩展 baostock / cninfo / akshare 小样本试跑，产出 v3 证据链与 source readiness 矩阵。

### 1.1 目的

证明系统是 **model-driven ingestion**（非全市场）；为 B01-DH2 data health v2 与后续 sandbox clean-write rehearsal 提供可读证据输入。

### 1.2 前置

| 前置 | 要求 |
| ---- | ---- |
| B01-WL | `specs/model_inputs/**` + `docs/quality/model_input_readiness_matrix.md` 已合并到集成分支 |
| v2 pilot | `06-24-round3-real-data-staged-pilot-v2` archive 证据 |
| PROMPT_14 授权 | `prompt14_user_authorization_2026-06-22.md` |
| Live 授权 | 2026-06-24 用户批；Execute live 前须 `execute-evidence/live_authorization_2026-06-24.yaml`（hardening §3 字段）；缺则 `skip_live_fetch=True` |

### 1.3 约束

- staged-only；raw/staging/sandbox 路径 only
- `R3-B2.75-REQ2-EM` 保持 DEFERRED
- registry 闭合仅 **proposed delta** + 主会话 merge

### 1.4 约束（持续）

- 无 hard-coded 全市场 universe
- 每个 symbol/issuer 须可追溯 WL 条目
- validation-only 输出不得自动升为 primary raw fact

### 1.5 停止条件

| # | 事件 | 处理 |
| --- | ---- | ---- |
| 1 | Plan 未 freeze / 用户未批准 Execute | 禁止 `task.py start` |
| 2 | production clean table 行数/hash 变化 | 中止；MUTATION_DETECTED 证据 |
| 3 | 触发 §3.3 forbidden 路径 | 立即停止；revert |
| 4 | RED 非预期全库红 | 停当前 §9 步 |
| 5 | **`specs/model_inputs/**` 不存在或 WL hash 无法解析** | **Execute 硬停**；协调者合并 B01-WL 或 rebase WL 分支后重开 Boot |
| 6 | pilot scope 无 WL trace（hand-picked symbols） | 中止；回 Plan/Repair |
| 7 | akshare 被选为 Primary 或 cninfo PDF bulk | 中止；违反 hardening §5/§6 |
| 8 | 未经批准的 caps / network 扩样 | `StagedPilotAuthorizationError` |
| 9 | agent 直接 commit registry 三件套闭合 | 停止；改为主会话 proposed delta |

### 1.6 原计划归并

| 来源 | 内容 |
| ---- | ---- |
| `R3E_real_data_staged_pilot_v3.md` | 分支、切片、验收、Red Flags |
| `R3D_model_input_whitelist.md` | WL 输出路径与 gate |
| `R3X_real_data_staged_pilot.md` | v1 staged 证据格式基线（只读） |
| `R3Y_real_data_staged_pilot_v2.md` + addendum | v2 模式；TDD；不得绕过 WL |
| `018B_production_live_pilot_gate.md` | sandbox / no clean write |
| `AUDIT_DEFERRED_REGISTRY.md` | `R3-PROMPT14-AKSHARE-VAL-01`、`R3-B2.75-REQ2-EM` 不得侧路关闭 |
| `BATCH_01_*` manifest/playbook/hardening | 文件锁与合并序 |
| v2 archive | 证据格式基线 |
| 纠偏 | `source-index.md` §A |

---

## 2. 预期结果（AC）

| ID | 预期结果 | 验证链 | 切片 |
| --- | -------- | ------ | ---- |
| AC-SP3-01 | WL loader 拒绝缺失/超 cap；caps JSON 含 whitelist_ref/hash | §9.1 | R3E-SP3-01 |
| AC-SP3-02 | baostock WL symbols raw/staging manifest v3 | §9.2 | R3E-SP3-02 |
| AC-SP3-03 | cninfo metadata-only；拒绝 PDF/full-text | §9.3 | R3E-SP3-03 |
| AC-SP3-04 | akshare validation-only + taxonomy；非 Primary | §9.4 | R3E-SP3-04 |
| AC-SP3-05 | conflict dry-run summary；无 clean 覆盖 | §9.5 | R3E-SP3-05 |
| AC-SP3-06 | closeout + source_readiness_matrix + no-mutation proof | §9.6 | R3E-SP3-06 |

### Playbook §8.6 PASS 子 AC（抄录）

- 每 symbol 可追溯 `specs/model_inputs/**`
- conflict dry-run summary；无 clean 覆盖
- §8.6 pytest + ruff 命令绿

---

## 3. 范围

### 3.1 In scope

- `backend/app/ops/staged_pilot.py` — v3 orchestration（平行 v2，不破坏 v2 API）
- `backend/app/ops/staged_pilot_fetch_ports.py` — 窄修
- `backend/app/storage/staged_evidence.py` — 仅 evidence 注册需要时
- `backend/app/validators/data_quality.py` — 仅现有规则不够时
- `tests/test_staged_pilot.py` — v2 回归
- `tests/test_real_data_staged_pilot_v3.py` — **Execute 新建**
- `tests/test_raw_store.py` — 回归
- `.trellis/tasks/06-25-round3-real-data-staged-pilot-v3/execute-evidence/*`
- `execute-evidence/registry_proposed_delta_v3.yaml` — **非 commit 闭合**

### 3.2 Out of scope · defer

| 项 | 偿还 |
| --- | ---- |
| `specs/model_inputs/**` 编写 | B01-WL |
| FRED/TDX/QMT/Yahoo live production | 各兄弟卡 |
| production clean write | sandbox rehearsal 另判 |
| `data_health.py` v2 | B01-DH2 |
| full market / full history / minute data | 禁止 |

### 3.3 禁止修改

- production migration / 直接写 `data/duckdb/quant_monitor.duckdb` clean 表
- `layer2_sensors/`、`layer3_chains/`、`layer4_markets/`（非 pilot 必需）
- `specs/model_inputs/**`（B01-WL 独占）
- fred/tdx registry 行（B01-FRED/TDX）
- registry 三件套 **直接闭合 commit**

---

## 4. 代码地图

| 路径 | 操作 |
| ---- | ---- |
| `staged_pilot.py` | 新增 v3：WL loader、caps v3、run/closeout/conflict |
| `staged_pilot_fetch_ports.py` | 窄修 fetch（若 RED 暴露） |
| `staged_evidence.py` | 窄改注册字段（若需要 pilot_id v3） |
| `validators/data_quality.py` / `validators/source_conflict.py` | 仅复用现有；不扩大 scope |
| `ops/live_pilot_fetch_ports.py` | 只读邻接；SP3 不改（FRED 独占 live port 扩展） |
| `source_registry.yaml` | **proposed delta 文件**，非 agent 直接改主文件 |

---

## 5. 测试契约（Execute 写代码 · Plan 写契约）

> purpose **冻结**；改 purpose 须回 Plan。

### 5.0 规范

1. 五字段 docstring（ROUND3_TEST_DOCSTRING_HYGIENE + playbook §2.2.1）
2. mocked/dry-run 默认；live 须 §0 授权 + evidence YAML
3. **测试文件路径**、**测试目的**、**成功怎么测**、**失败怎么测** 见 §5.1–§5.2

### 5.1 测试文件（路径写死）

| 测试文件路径 | 目标文件 | 测试目的（冻结） | §9 步 |
| ------------ | -------- | ---------------- | ----- |
| `tests/test_real_data_staged_pilot_v3.py` | `backend/app/ops/staged_pilot.py` | v3 WL 驱动与安全边界 | 9.1–9.6 |
| `tests/test_staged_pilot.py` | `backend/app/ops/staged_pilot.py` | v2 回归不被 v3 破坏 | 9.0, 9.7 |
| `tests/test_raw_store.py` | `backend/app/storage/raw_store.py` | raw store 回归 | 9.7 |

### 5.2 成功/失败语义

| 能力 | 成功怎么测 | 失败怎么测 | 场景 |
| ---- | ---------- | ---------- | ---- |
| WL gate | 合法 WL fixture 加载 caps 通过 | 缺 WL / 超 cap 抛错或 FAIL 状态 | S1 |
| baostock v3 | mock fetch 产出 manifest 必填字段 | 超 symbol/row 拒绝 | S2 |
| cninfo metadata | metadata manifest 无 PDF 字段扩张 | PDF/full-text op 拒绝 | S3 |
| akshare validation | 仅 validation op；taxonomy 记录 | primary 选择失败 | S4 |
| conflict dry-run | summary JSON；无 clean write | 尝试写 clean 表失败 | S5 |
| closeout | readiness matrix + no-mutation | 缺字段 / production-live 声称失败 | S6 |

### 5.3 用例设计（Plan 冻结）

| 测试文件 | `test_*` 名称 | 断言语义 | 场景 | RED 命令 | GREEN 命令 |
| -------- | ------------- | -------- | ---- | -------- | ---------- |
| `tests/test_real_data_staged_pilot_v3.py` | `test_v3_refuses_missing_whitelist` | 无 `specs/model_inputs` 时 fail-closed | S1 | `pytest tests/test_real_data_staged_pilot_v3.py::test_v3_refuses_missing_whitelist -v` | 同上 exit 0 |
| 同上 | `test_v3_whitelist_caps_enforced` | 超 cap 拒绝 | S1 | `pytest …::test_v3_whitelist_caps_enforced -v` | 同上 |
| 同上 | `test_v3_baostock_manifest_fields` | manifest 含 fetch_id/hash | S2 | `pytest …::test_v3_baostock_manifest_fields -v` | 同上 |
| 同上 | `test_v3_cninfo_rejects_pdf_expansion` | PDF 路径拒绝 | S3 | `pytest …::test_v3_cninfo_rejects_pdf_expansion -v` | 同上 |
| 同上 | `test_v3_akshare_validation_only_not_primary` | akshare 非 Primary | S4 | `pytest …::test_v3_akshare_validation_only_not_primary -v` | 同上 |
| 同上 | `test_v3_conflict_dry_run_no_clean_write` | conflict summary 无 clean 写 | S5 | `pytest …::test_v3_conflict_dry_run_no_clean_write -v` | 同上 |
| 同上 | `test_v3_closeout_readiness_matrix` | closeout 字段完整 | S6 | `pytest …::test_v3_closeout_readiness_matrix -v` | 同上 |

### 5.4 四层测试

| 层 | 环境 | 命令 | 通过 | 证据 |
| --- | ----- | ---- | ---- | ---- |
| 单元 | local/ci | `uv run pytest tests/test_real_data_staged_pilot_v3.py tests/test_staged_pilot.py -q` | exit 0 | §9.x-green.txt |
| 集成 | local/ci | `uv run pytest tests/test_raw_store.py -q` | exit 0 | 9.7-green.txt |
| 管道 | prod-path | playbook §8.6 ruff + compileall | exit 0 | 9.7-green.txt |
| E2E | prod-path | `uv run pytest -q` | exit 0 | 9.7-green.txt |

---

## 6. 验证

| Tier | 环境 | 命令 | 场景 | 通过条件 | 勾 |
| ---- | ----- | ---- | ---- | -------- | --- |
| A | local/ci | `uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py tests/test_real_data_staged_pilot_v3.py -q` | S1–S6 | exit 0 | [ ] |
| B | prod-path | `uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests` | 全回归 | exit 0 | [ ] |
| C | prod-path | `uv run ruff check backend/app/ops backend/app/storage backend/app/validators tests/test_staged_pilot.py tests/test_raw_store.py tests/test_real_data_staged_pilot_v3.py` | SP3 文件集 | exit 0 | [ ] |

**6.1 交接门槛：** §9 证据齐 · WL 已合并 · §5.4+§6 B/C 已跑 · §1.5 未触发

---

## 7. Red Flags

| 风险 | 预防 |
| ---- | ---- |
| WL 未合仍实现 symbol 列表 | §1.5 #5 Boot 检查 |
| v2 envelope 冒充 v3 | SP3-01 独立测试 |
| akshare 关 EM 债 | explicit re-defer |
| registry agent commit | proposed delta only |
| 横向单脚本六切片 | §8 垂直切片 + 独立 evidence |

---

## 8. 实现顺序（垂直切片）

| 序 | ID | 交付物（完标准） | 依赖 | AC |
| --- | --- | ---------------- | ---- | --- |
| 1 | R3E-SP3-01 | `pilot_v3_caps.json` + WL loader + `whitelist_ref.json` | **WL merged** | AC-SP3-01 |
| 2 | R3E-SP3-02 | baostock raw/staging manifest v3 | SP3-01 | AC-SP3-02 |
| 3 | R3E-SP3-03 | cninfo metadata evidence + schema notes | SP3-01 | AC-SP3-03 |
| 4 | R3E-SP3-04 | akshare taxonomy v3 | SP3-01 | AC-SP3-04 |
| 5 | R3E-SP3-05 | `conflict_check_summary_v3.json` | SP3-02,04 | AC-SP3-05 |
| 6 | R3E-SP3-06 | closeout + readiness matrix + no-mutation + registry proposed delta | SP3-01..05 | AC-SP3-06 |
| 7 | R3E-SP3-07 | Tier B 全量回归 + playbook §8.6 | SP3-01..06 | 全 AC |

---

## 9. 实现步骤（RED/GREEN · 仅 Execute）

### 9.0 Boot

> **Boot 路由：** 见 §0.3 Execute 强制必读清单 + `research/integration-ledger.md`（禁止在此枚举全路径）。

| RED 命令 | GREEN 命令 | 证据 | 绑定 Execute Skill | 已执行 |
| -------- | ---------- | ---- | ------------------ | ------ |
| `uv run pytest tests/test_staged_pilot.py -q`（基线） | 同上 exit 0 | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [ ] |
| **WL 存在检查**（见 §0.1） | 目录存在 | `9.0-wl-gate.txt` | Boot gate | [ ] |

### 9.1 R3E-SP3-01 — WL loader / caps

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-01（§8 序 1） |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_refuses_missing_whitelist tests/test_real_data_staged_pilot_v3.py::test_v3_whitelist_caps_enforced -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.1-red.txt` / `9.1-green.txt` |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines |
| 通过 | RED FAIL；GREEN 0；§5.2 S1 |

### 9.2 R3E-SP3-02 — baostock expansion

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-02 |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_baostock_manifest_fields -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.2-red.txt` / `9.2-green.txt` + `raw_evidence_manifest_v3_baostock.json` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S2 |

### 9.3 R3E-SP3-03 — cninfo metadata

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-03 |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_cninfo_rejects_pdf_expansion -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.3-red.txt` / `9.3-green.txt` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S3 |

### 9.4 R3E-SP3-04 — akshare validation-only

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-04 |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_akshare_validation_only_not_primary -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.4-red.txt` / `9.4-green.txt` + `akshare_validation_taxonomy_v3.json` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S4 |

### 9.5 R3E-SP3-05 — conflict dry-run

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-05 |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_conflict_dry_run_no_clean_write -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.5-red.txt` / `9.5-green.txt` + `conflict_check_summary_v3.json` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S5 |

### 9.6 R3E-SP3-06 — closeout / readiness

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-06 |
| RED 命令 | `uv run pytest tests/test_real_data_staged_pilot_v3.py::test_v3_closeout_readiness_matrix -v` |
| GREEN 命令 | 同上 exit 0 |
| 证据 | `9.6-red.txt` / `9.6-green.txt` + `pilot_v3_closeout.json` + `source_readiness_matrix_v3.md` + `no_mutation_proof_v3.md` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation |
| 通过 | §5.2 S6 |

### 9.7 R3E-SP3-07 — merge gate regression

| 字段 | 内容 |
| ---- | ---- |
| 切片 | R3E-SP3-07 |
| RED 命令 | `uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py tests/test_real_data_staged_pilot_v3.py -q` |
| GREEN 命令 | `uv sync --locked` → Tier A pytest → Tier C ruff → Tier B 全库（playbook §8.6 顺序） |
| 证据 | `9.7-green.txt` |
| 绑定 Execute Skill | incremental-implementation |
| 通过 | §6 Tier A/B/C；§8.6 五命令全 exit 0 |

---

## 10. Execute 交接 DoD

- [ ] §9 证据齐 · WL 已合并 · §5.4+§6 · `validate-execute-handoff` 0 · 未 finish-work
- [ ] closure report 九项（父 README §5）
- [ ] registry **proposed delta** 移交主会话

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 绑定 | 已读 | 已执行 |
| ----- | ------ | ---- | ---- | ------ |
| trellis-execute | 必做 | Boot | [ ] | [ ] |
| test-driven-development | 必做 | §9 RED | [ ] | [ ] |
| incremental-implementation | 必做 | §9 SLICE | [ ] | [ ] |
| karpathy-guidelines | 必做 | GREEN | [ ] | [ ] |
| testing-guidelines | 必做 | 写测 | [ ] | [ ] |
| gitnexus-impact | 必做 | 改 symbol | [ ] | [ ] |
| systematic-debugging | 条件 | DEBUG | [ ] | [ ] |
| trellis-check | **不用** | → Audit A1 | — | — |

---

## 12. WL 依赖策略（Execute 协调）

| 策略 | 说明 |
| ---- | ---- |
| **硬停** | `specs/model_inputs/**` 不存在 → 禁止 §9.1+（§1.5 #5） |
| **合并优先** | Track A：先 merge `chore/round3-model-input-whitelist`，再 rebase SP3 |
| **只读引用** | Execute Boot 允许 `git merge --no-commit` WL 或 read-tree 只读检出 WL 文件到 worktree（**不**手写 symbol 列表） |
| **测试** | 使用合并后的真实 WL；禁止长期用临时 fixture 冒充生产 WL |
| **证据** | 所有 manifest 含 `whitelist_ref`（路径 + sha256） |
| **Plan 阶段** | 本 MASTER 已冻结；WL 缺失 **不阻塞 Plan freeze**，阻塞 Execute start |

---

## 13. Plan 质检表（Agent-2 · §3.10）

| 路径 | 已入 MASTER/implement | 摘要一句 | 遗漏风险 |
| ---- | --------------------- | -------- | -------- |
| Playbook §2.5/§2.6/§8.6 | §0/§6/§9.7 inline | 无损摘要（worktree 尚无 playbook 文件） | 低 |
| Playbook §3.6 `R3X_real_data_staged_pilot.md` | §1.6 + implement | v1 证据格式只读 | 低 |
| Playbook §3.6 `R3Y_*` v2 + addendum | §1.6/§8 + implement | 不得绕过 WL | 低 |
| Playbook §3.6 `prompt14_user_authorization` | §1.2 + implement | 授权链 | 低 |
| Playbook §3.6 `source_conflict_rules.yaml` | §6 + implement | conflict dry-run | 低 |
| Playbook §3.6 `staged_pilot*.py` | §4/§8 + implement | v2→v3 主实现 | 低 |
| Playbook §3.6 `staged_evidence.py` | §4 + implement | 窄改评估 | 低 |
| Playbook §3.6 `validators/data_quality.py` | §4 + implement | 复用现有规则 | 低 |
| Playbook §3.6 v2 archive | §1.2 + implement | closeout 对照 | 低 |
| R3E v3 卡 §3–§14 | §2/§5/§8/§9 + implement | 六实现切片 + SP3-07 回归门 | 低 |
| R3D WL 卡 | §12 + implement | WL 输出路径；Execute 前阻塞 | **Execute 阻塞** |
| `live_pilot_fetch_ports.py` | §4 + implement | 只读邻接；不改 | 低 |
| `validators/source_conflict.py` | §4 + implement | conflict dry-run 复用 | 低 |
| `AUDIT_DEFERRED_REGISTRY.md` | §1.6 + implement | AKSHARE-VAL / EM 债 re-defer | 低 |
| 018B | §0 + implement | sandbox 边界 | 低 |
| hardening §1–§7 | §0 + implement | live YAML；禁止 AkShare Primary | 低 |
| manifest C04 §4/§5 | §3/§12 + implement | 依赖 C01；registry proposed delta | 低 |
| GLOBAL×4 | §1.6/§5 + implement | TDD + caps + WriteManager | 低 |
| `/to-issues` vertical-slices | §8 + `vertical-slices.md` | R3E-SP3-01..07 冻结 | 低 |
| Live 授权 2026-06-24 | §1.2/§0 | 用户已批；Execute 写 YAML 证据 | 低 |
| `specs/model_inputs/**` | §1.5 #5/§12 | Plan 时不存在；Boot 硬停 | **Execute 阻塞** |
| registry 三件套 | §3.3/§10 | proposed delta only；禁止 agent commit | 低 |
| source-index §C | 全文 | 六类索引完整 | 低 |

### 13.1 Agent-2 结论（2026-06-25）

| 项 | 结果 |
| --- | ---- |
| `validate-plan-freeze` | exit 0 |
| §3.9 checklist | 零遗留 |
| Verdict | **PASS** |
| Execute 门禁 | **须等 B01-WL 合并**（`specs/model_inputs/**` 缺失 → Boot STOP §1.5 #5） |
| registry | Execute 禁止直接 commit；仅 `registry_proposed_delta_v3.yaml` |
