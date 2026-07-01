# MASTER 计划 — Round 3 Batch 5 `023b` full Layer5 evidence chain (B01-023)

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **Batch 01 Playbook：** `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §0 + §3.2 + §8.4  
> **合并轨：** Wave D **Track B**（不得与 Batch 01 六卡混 PR）

---

## 0. 元信息

| 字段                      | 值                                                                                         |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| 任务 slug                 | `round3-023b-evidence-chain-full`                                                          |
| Playbook ID               | `B01-023`                                                                                  |
| 分支                      | `feature/round3-023b-evidence-chain-full` @ worktree `../quant-monitor-desk-wt-023-layer5` |
| 前置                      | `023A` + `021` + `022`；任务卡 §16 gate                                                    |
| manifest_protocol_version | `3`                                                                                        |
| analysis_waiver           | `false`                                                                                    |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md`                             |

### Wave D / Batch 01 边界（§0 强制）

1. **Track B 单独合并** — playbook §7.3；不与 Batch 01 integration 包混 PR
2. **文件锁** — `layer5_evidence/**` 本分支独占；B01-LIN 不得改
3. `BATCH_01_HARDENING_RULES.md` §1–§10 — 冲突取更严
4. staged-only；无 live fetch；无 production clean write
5. D-09 — Layer 2–5 不复制 Layer1 全套标准化字段
6. registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md` — **主会话批处理**；本分支仅 proposed delta

### §16 前提检查（Execute 硬 gate）

| 前提              | Plan 时状态              | Execute Boot 复检                        |
| ----------------- | ------------------------ | ---------------------------------------- |
| `023A` foundation | ✅ 代码在 worktree       | `test_layer5_evidence_foundation.py` 绿  |
| `021` Layer3 集成 | ✅ `snapshot_builder.py` | `test_layer3_snapshot_builder.py` 绿     |
| `022` Layer4 集成 | ✅ `market_structure.py` | `test_layer4_market_structure.py` 绿     |
| 全量 pytest       | ⏳ Plan 未执行           | **`uv run pytest -q` 必须全绿方可 §8.1** |

### 0.1 门控速查

| 项        | 值                                                     |
| --------- | ------------------------------------------------------ |
| 怎么测    | §8 RED→GREEN；`tests/test_layer5_evidence_chain.py`    |
| 怎么验收  | §10 Tier A + playbook §8.4                             |
| 什么叫过  | §2 AC-023-1..6 + `R3D-023-01`..`05` 映射完成           |
| prod-path | Tier B：`uv run pytest -q` 全库回归                    |
| 6.pre     | `research/gitnexus-execute-summary.md`（Execute 产出） |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；每 §8.x 步前对照 ladder
2. 复用 023A `EvidenceFoundationValidator` / `Layer5LineageBuilder`；禁止平行第二套 identity 逻辑
3. 禁止新依赖、未请求 helper；`ponytail:` 标已知天花板
4. TDD：RED → karpathy-guidelines → testing-guidelines → ponytail → GREEN

### 0.3b Execute 工程纪律 — 测试

1. 五字段 docstring（playbook §2.2.1）
2. 只 mock 外部 I/O；lineage/as_of 用真实 fixture 值
3. 每步 GREEN 后 Read `incremental-implementation`；Tier B 全库仅 §8.6 一次
4. 模型 **`composer-2.5`**（playbook §2.3）

### 0.4 上下文打包（v3）

Execute 以 MASTER + `implement.jsonl` + `context_pack.json` 为准。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute + ponytail。Phase 0 → §8.x → §10 → Audit。勿 finish-work。Track B 分轨。
```

---

## 1. 目标与目的

### 1.1 目标

在 023A foundation 上交付：`instrument_registry`、bar/event/financial/valuation staged 模型、`evidence_chain.py` builder、冲突复核 ADR、条件 storage port。

### 1.2 目的

让 Layer3/4 snapshot 可关联 evidence refs，支撑审计化「为什么这么判断」；闭合 Plan 级 `R3D-023-01`..`05`；**不**声称 production-live。

### 1.3 前置

- 归档：`06-22-round3-023a-evidence-foundation`
- `06-24-round3-021-layer3-snapshot`、`06-24-round3-022-layer4-market` 代码在 worktree
- Batch 3 staged gate CLOSED

### 1.4 约束

- allowed：见 `research/worktree-slices.md`
- forbidden：live source、production 写入、registry trio commit、改 L3/L4 实现

### 1.4a Playbook §2.5 / §2.6 边界（B01-023）

| Owns（可写）                                                                                                                                            | Must not own                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `backend/app/layer5_evidence/**`、`specs/contracts/layer5_evidence_contract.yaml`、L5 测试与 fixture、`docs/adr/ADR-023-layer5-conflict-review-path.md` | live fetch、production 写入、registry 三件套直接 commit、`layer3_chains/**` / `layer4_markets/**` 写 |

> 完整路径表：`research/worktree-slices.md` · hardening §3–§7 摘要见 §0 边界 #4–#5

### 1.5 停止条件

| #   | 事件                                                | 处理                               |
| --- | --------------------------------------------------- | ---------------------------------- |
| 1   | Plan 未 freeze / 用户未批准                         | 禁止 `task.py start`               |
| 2   | 触发 forbidden 路径（ops/staged/registry/L3/L4 写） | 立即停止；revert                   |
| 3   | RED 非预期全库红                                    | 停当前 §8 步                       |
| 4   | 声称 production-live / Batch 01 包 readiness        | 中止；修正 MASTER                  |
| 5   | live fetch 或全市场 DuckDB 扫描                     | **自定义停损** — 违反 hardening §3 |
| 6   | 并发 commit 闭合 registry 三件套 / COVERAGE         | 停止；交主会话                     |
| 7   | §16 复检失败（foundation/L3/L4 pytest 红）          | 禁止 §8.1；交协调者                |
| 8   | 重复实现 023A foundation 逻辑于新模块               | 停止；合并到 foundation 复用       |

### 1.6 原计划归并

| 来源                                           | 内容                        |
| ---------------------------------------------- | --------------------------- |
| `023_implement_layer5_evidence_chain.md`       | full chain + §16/§17        |
| `023A_layer5_evidence_foundation.md`           | 最小 foundation 边界        |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` Batch 3D.1 | `R3D-023-01`..`05`          |
| `layer5_security_evidence.md`                  | evidence_chain 表语义       |
| `layer5_evidence_contract.yaml`                | models + `deferred_to_023b` |
| playbook §3.2 + §8.4                           | B01-023 索引与 PASS         |
| `UNRESOLVED_ITEM_TASK_COVERAGE.md`             | `R3-PARTIAL-4`、`R2-RISK-2` |

---

## 2. 预期结果（AC）

| ID       | Roadmap      | 预期结果                                                                             | 验证链                                                             |
| -------- | ------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| AC-023-1 | `R3D-023-01` | `instrument_registry` 行校验；`instrument_id` 唯一；延续 023A ref                    | §8#1 / §9.1; `test_instrumentRegistry_uniqueIds`                   |
| AC-023-2 | `R3D-023-02` | bar/event/financial/valuation staged 行符合 contract；no-future-data                 | §8#2 / §9.2; `test_securityBar_rejectsFutureTradeDate` 等          |
| AC-023-3 | `R3D-023-03` | `EvidenceChainBuilder` 含 layer context 槽 + `upstream_snapshot_ids`；Agent 非事实源 | §8#3 / §9.3; `test_evidenceChain_traceUpstreamSnapshots`           |
| AC-023-4 | `R3D-023-04` | ADR-023：severe reconcile failed → `manual_review_state=queued`                      | §8#4 / §9.4; `test_evidenceChain_severeConflictQueuesManualReview` |
| AC-023-5 | `R3D-023-05` | `EvidenceReadPort` fake 测边界 **或** ADR re-defer `R2-RISK-2`                       | §8#5 / §9.5; `test_evidenceReadPort_boundary`                      |
| AC-023-6 | —            | playbook §8.4 + 任务卡 §11 验收                                                      | §10                                                                |

### 2.1 Playbook §8.4 子 AC

| 维度  | PASS 条件                                         | MASTER 映射   |
| ----- | ------------------------------------------------- | ------------- |
| Plan  | `validate-plan-freeze` exit 0；`R3D-023-01`..`05` | §SCI + §2     |
| 实现  | evidence chain；Agent 文本非事实源                | AC-023-3      |
| Audit | A1–A8 + 对抗性零遗留                              | AUDIT.plan.md |
| 边界  | 未 live / 未 production 写 / 未混 Batch 01 PR     | §0、§3.3      |

---

## 3. 需求与场景矩阵

| 场景# | Given                            | When                  | Then                              | AC       | 测试                         | Tier |
| ----- | -------------------------------- | --------------------- | --------------------------------- | -------- | ---------------------------- | ---- |
| S1    | staged instrument 行             | validate registry     | 唯一 instrument_id                | AC-023-1 | `test_instrumentRegistry_*`  | A    |
| S2    | staged bar 行 as_of 边界内       | validate bar          | 通过；未来 trade_date 拒绝        | AC-023-2 | `test_securityBar_*`         | A    |
| S3    | L3/L4 snapshot ids + L5 事实证据 | build chain           | context 槽非空；upstream ids 保留 | AC-023-3 | `test_evidenceChain_*`       | A    |
| S4    | severe conflict 标记             | apply conflict policy | queued manual review              | AC-023-4 | `test_evidenceChain_severe*` | A    |
| S5    | builder 需读 staged bundle       | inject port           | 不 import 具体 storage 类         | AC-023-5 | `test_evidenceReadPort_*`    | B    |

**3.1 需求说明：** 完整 Layer5 chain staged 可测；023A 行为回归不退化。  
**3.2 范围：** in §3.1 · out：live ingestion、全量回填、审核 UI、registry 闭合

### 3.3 禁止修改

- `backend/app/layer3_chains/**`、`backend/app/layer4_markets/**`（只读）
- `backend/app/ops/staged_pilot.py`、`storage/staged_evidence.py`
- `specs/contracts/snapshot_lineage_contract.yaml`（019/023A owner 历史；本任务只读）
- registry 三件套直接写
- production DB

### 3.2 Out of scope · defer

| 项                                   | 边界                       | 偿还                   |
| ------------------------------------ | -------------------------- | ---------------------- |
| `ADV-R3X-LINEAGE-001` 全量 DB 持久化 | chain 测试 + envelope only | Batch 6 / LIN          |
| FastAPI `/api/layer5/*`              | API 层                     | Round 4+               |
| WriteManager clean table 写          | optional sandbox           | defer                  |
| instant severe queue UI              | Round4                     | `R3-PARTIAL-4` partial |

---

## 4. 代码地图

| 路径                                                 | 操作                                                          |
| ---------------------------------------------------- | ------------------------------------------------------------- |
| `backend/app/layer5_evidence/instrument_registry.py` | 创建 — registry 校验                                          |
| `backend/app/layer5_evidence/evidence_models.py`     | 创建 — bar/event/financial/valuation 行（或扩展 `models.py`） |
| `backend/app/layer5_evidence/evidence_chain.py`      | 创建 — `EvidenceChainBuilder`                                 |
| `backend/app/layer5_evidence/ports.py`               | 条件创建 — `EvidenceReadPort`                                 |
| `specs/contracts/layer5_evidence_contract.yaml`      | 更新 — 移除/兑现 `deferred_to_023b` 项                        |
| `docs/adr/ADR-023-layer5-conflict-review-path.md`    | 创建 — `R3-PARTIAL-4` 决策                                    |
| `tests/fixtures/layer5_staged_evidence/`             | 创建 — 最小 staged bundle                                     |
| `tests/test_layer5_evidence_chain.py`                | 创建 — §5.3 用例                                              |

**已有（023A · 只扩展不推翻）：** `foundation.py`、`models.py`、`lineage.py`、`test_layer5_evidence_foundation.py`

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring（playbook §2.2.1）
2. 只 mock 外部 I/O
3. 每测 ≥1 业务语义断言
4. `tests/` ponytail（§2.2.2）

### 5.1 测试文件路径

| 路径                                       | 目标                                            | 测试目的          | §8 步   |
| ------------------------------------------ | ----------------------------------------------- | ----------------- | ------- |
| `tests/test_layer5_evidence_chain.py`      | `backend/app/layer5_evidence/evidence_chain.py` | full chain staged | 8.1–8.6 |
| `tests/test_layer5_evidence_foundation.py` | `foundation.py`                                 | 023A 回归         | 8.6     |

### 5.2 成功/失败语义

| 能力      | 成功怎么测                 | 失败怎么测                         | 场景 |
| --------- | -------------------------- | ---------------------------------- | ---- |
| registry  | 合法 instrument 行         | 重复 id → 拒绝                     | S1   |
| bar/event | contract 字段齐全          | 未来 trade_date → 拒绝             | S2   |
| chain     | upstream ids + context     | Agent 摘要作事实 → 拒绝            | S3   |
| conflict  | severe → queued            | queued 无 flag → 拒绝              | S4   |
| port      | fake port 返回 staged dict | 直接 import storage → 禁止（审查） | S5   |

### 5.3 用例设计

| 测试文件                              | `test_*` 名称                                         | 断言语义                   | 场景 | RED 命令                                                           |
| ------------------------------------- | ----------------------------------------------------- | -------------------------- | ---- | ------------------------------------------------------------------ |
| `tests/test_layer5_evidence_chain.py` | `test_instrumentRegistry_uniqueIds`                   | instrument_id 唯一         | S1   | `pytest …::test_instrumentRegistry_uniqueIds -q`                   |
| 同上                                  | `test_securityBar_rejectsFutureTradeDate`             | 未来 bar 日期拒绝          | S2   | `pytest …::test_securityBar_rejectsFutureTradeDate -q`             |
| 同上                                  | `test_evidenceChain_traceUpstreamSnapshots`           | chain 含 L3/L4 snapshot id | S3   | `pytest …::test_evidenceChain_traceUpstreamSnapshots -q`           |
| 同上                                  | `test_evidenceChain_rejectsAgentTextAsFact`           | Agent 文本不能进事实链     | S3   | `pytest …::test_evidenceChain_rejectsAgentTextAsFact -q`           |
| 同上                                  | `test_evidenceChain_severeConflictQueuesManualReview` | severe → queued            | S4   | `pytest …::test_evidenceChain_severeConflictQueuesManualReview -q` |
| 同上                                  | `test_evidenceReadPort_boundary`                      | port injection 边界        | S5   | `pytest …::test_evidenceReadPort_boundary -q`                      |

### 5.4 四层测试

| 层      | 范围               | 命令                                                                                            | 通过                     |
| ------- | ------------------ | ----------------------------------------------------------------------------------------------- | ------------------------ |
| L1 单元 | chain + foundation | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` | exit 0                   |
| L2 集成 | L3/L4 回归         | `uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer4_market_structure.py -q`  | exit 0                   |
| L3 管道 | batch3 gate        | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q`                                  | exit 0                   |
| L4 E2E  | 全库               | `uv run pytest -q`                                                                              | exit 0；**仅 §8.6 一次** |

---

## 6. 验证（Tier）

| Tier | 环境      | 命令                                                                                            | 场景  | 通过         |
| ---- | --------- | ----------------------------------------------------------------------------------------------- | ----- | ------------ |
| A    | local/ci  | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` | S1–S4 | exit 0       |
| A    | local/ci  | `uv sync --locked`                                                                              | —     | exit 0       |
| B    | prod-path | `uv run pytest -q`                                                                              | S1–S5 | exit 0       |
| B    | prod-path | `uv run ruff check .`                                                                           | —     | 无新增 error |

**6.1 交接门槛：** §8 证据齐 · §5.1 已建 · AC-023-1..6 有用例 · §5.4 L4 已跑 · §1.5 未触发

---

## 7. Red Flags

| 风险                      | 预防                               |
| ------------------------- | ---------------------------------- |
| 与 023A 重复实现 identity | 复用 `EvidenceFoundationValidator` |
| Agent 文本作事实源        | AC-023-3 + foundation 回归         |
| 混 Batch 01 PR            | Track B 显式                       |
| registry 并发闭合         | 停止条件 #6                        |
| 全量 bar 回填             | AC-023-2 staged only               |
| 改 L3/L4 代码             | §3.3 forbidden                     |

---

## 8. 实现顺序（垂直切片）

| 序  | ID             | Roadmap      | 交付物（完标准）                             | 依赖           | AC       | §9 步 |
| --- | -------------- | ------------ | -------------------------------------------- | -------------- | -------- | ----- |
| 0   | SLICE-BOOT     | —            | 测试骨架 + Boot 证据                         | §16 gate       | —        | 9.0   |
| 1   | SLICE-REGISTRY | `R3D-023-01` | `instrument_registry.py` + 唯一性测试绿      | SLICE-BOOT     | AC-023-1 | 9.1   |
| 2   | SLICE-MODELS   | `R3D-023-02` | evidence 行类型 + validator + no-future-data | SLICE-REGISTRY | AC-023-2 | 9.2   |
| 3   | SLICE-CHAIN    | `R3D-023-03` | `evidence_chain.py` + trace 测试             | SLICE-MODELS   | AC-023-3 | 9.3   |
| 4   | SLICE-CONFLICT | `R3D-023-04` | ADR-023 + severe→queued 测试                 | SLICE-CHAIN    | AC-023-4 | 9.4   |
| 5   | SLICE-PORT     | `R3D-023-05` | port **或** re-defer ADR                     | SLICE-CHAIN    | AC-023-5 | 9.5   |
| 6   | SLICE-GATES    | —            | contract 更新 + Tier B + handoff             | 4+5            | AC-023-6 | 9.6   |

---

## 9. 实现步骤（RED/GREEN · Execute only）

### 9.0 Boot

| 字段               | 内容                                                                                                             |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 做什么             | 按 **§0.3** Read `implement.jsonl` 每一条 + `research/integration-ledger.md`；§16 复检 pytest；充实 chain 测试体 |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py -q`                                                           |
| GREEN 命令         | `uv sync --locked` + boot reads 证据                                                                             |
| RED 证据           | `research/execute-evidence/9.0-red.txt`                                                                          |
| GREEN 证据         | `research/execute-evidence/9.0-green.txt`                                                                        |
| 绑定 Execute Skill | trellis-execute · test-driven-development                                                                        |
| 已执行             | [ ]                                                                                                              |

### 9.1 SLICE-REGISTRY (`R3D-023-01`)

| 字段               | 内容                                                                                      |
| ------------------ | ----------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py::test_instrumentRegistry_uniqueIds -q` |
| GREEN 命令         | 同上 exit 0                                                                               |
| RED 证据           | `research/execute-evidence/9.1-red.txt`                                                   |
| GREEN 证据         | `research/execute-evidence/9.1-green.txt`                                                 |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines                        |
| 已执行             | [ ]                                                                                       |

### 9.2 SLICE-MODELS (`R3D-023-02`)

| 字段               | 内容                                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py::test_securityBar_rejectsFutureTradeDate -q` |
| GREEN 命令         | 同上 exit 0                                                                                     |
| RED/GREEN 证据     | `9.2-red.txt` / `9.2-green.txt`                                                                 |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                                            |
| 已执行             | [ ]                                                                                             |

### 9.3 SLICE-CHAIN (`R3D-023-03`)

| 字段               | 内容                                                                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py::test_evidenceChain_traceUpstreamSnapshots tests/test_layer5_evidence_chain.py::test_evidenceChain_rejectsAgentTextAsFact -q` |
| GREEN 命令         | 同上 exit 0                                                                                                                                                                      |
| RED/GREEN 证据     | `9.3-red.txt` / `9.3-green.txt`                                                                                                                                                  |
| 绑定 Execute Skill | test-driven-development · gitnexus-impact                                                                                                                                        |
| 已执行             | [ ]                                                                                                                                                                              |

### 9.4 SLICE-CONFLICT (`R3D-023-04`)

| 字段               | 内容                                                                                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py::test_evidenceChain_severeConflictQueuesManualReview -q` |
| GREEN 命令         | 同上 exit 0                                                                                                 |
| RED/GREEN 证据     | `9.4-red.txt` / `9.4-green.txt`                                                                             |
| 绑定 Execute Skill | test-driven-development                                                                                     |
| 已执行             | [ ]                                                                                                         |

### 9.5 SLICE-PORT (`R3D-023-05`)

| 字段               | 内容                                                                                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_chain.py::test_evidenceReadPort_boundary -q` **或** 记录 re-defer ADR |
| GREEN 命令         | 同上 exit 0                                                                                                     |
| RED/GREEN 证据     | `9.5-red.txt` / `9.5-green.txt`                                                                                 |
| 绑定 Execute Skill | test-driven-development                                                                                         |
| 已执行             | [ ]                                                                                                             |

### 9.6 SLICE-GATES

| 字段               | 内容                                                                |
| ------------------ | ------------------------------------------------------------------- |
| RED 命令           | `uv run pytest tests/test_layer5_evidence_foundation.py -q`（回归） |
| GREEN 命令         | §10 Tier A + B                                                      |
| RED/GREEN 证据     | `9.6-red.txt` / `9.6-green.txt`                                     |
| 绑定 Execute Skill | incremental-implementation                                          |
| 已执行             | [ ]                                                                 |

---

## 10. Tier 验收

| Tier | 命令                                                                                            | 通过         |
| ---- | ----------------------------------------------------------------------------------------------- | ------------ |
| A    | `uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q` | exit 0       |
| A    | `uv sync --locked`                                                                              | exit 0       |
| B    | `uv run pytest -q`                                                                              | exit 0       |
| B    | `uv run ruff check .`                                                                           | 无新增 error |
| B    | `uv run python -m compileall backend scripts tests`                                             | exit 0       |

**10.1 交接门槛：** `validate-execute-handoff` exit 0 · 未 finish-work

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 绑定       | 已读 | 已执行 |
| -------------------------- | -------- | ---------- | ---- | ------ |
| trellis-execute            | 必做     | Boot       | [ ]  | [ ]    |
| test-driven-development    | 必做     | §9 RED     | [ ]  | [ ]    |
| incremental-implementation | 必做     | §9 SLICE   | [ ]  | [ ]    |
| karpathy-guidelines        | 必做     | GREEN      | [ ]  | [ ]    |
| testing-guidelines         | 必做     | 写测       | [ ]  | [ ]    |
| gitnexus-impact            | 必做     | 改 symbol  | [ ]  | [ ]    |
| systematic-debugging       | 条件     | DEBUG      | [ ]  | [ ]    |
| trellis-check              | **不用** | → Audit A1 | —    | —      |

---

## 12. Source Context Index（SCI）

### SCI-A — playbook §3.1 共用底座（摘要）

| 路径                                            | 摘要                        |
| ----------------------------------------------- | --------------------------- |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | §0 双轨；§2.5 锁；§8.4 PASS |
| `BATCH_01_HARDENING_RULES.md`                   | §1–§10 硬停                 |
| `BATCH_01_TASK_CARD_MANIFEST.md`                | Wave D 行；manifest §4      |
| `GLOBAL_*.md`                                   | 执行/测试/资源上限          |
| `UNRESOLVED_ITEM_TASK_COVERAGE.md`              | R3-PARTIAL-4 / R2-RISK-2    |
| `MIGRATION_MAP.md`                              | layer5_evidence 目录        |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`            | §2.3 Serial 023             |

### SCI-B — playbook §3.2 B01-023 专读

| 路径                                     | 摘要                    |
| ---------------------------------------- | ----------------------- |
| `023_implement_layer5_evidence_chain.md` | 任务卡 + §16/§17        |
| `023A_layer5_evidence_foundation.md`     | 归档边界                |
| `layer5_security_evidence.md`            | evidence_chain DDL 语义 |
| `layer5_evidence_contract.yaml`          | models + deferred       |
| `data_validation_and_conflict.md`        | manual review queue     |
| `write_manager.md`                       | clean 写 defer          |
| `snapshot_lineage_contract.yaml`         | lineage 字段（只读）    |
| `backend/app/layer5_evidence/**`         | 023A 基线               |
| `test_layer5_evidence_foundation.py`     | 回归                    |

### SCI-C — Plan 质检（§3.9/§3.10）

| 路径                                            | 已入 MASTER/implement           | 摘要一句                               | 遗漏风险           |
| ----------------------------------------------- | ------------------------------- | -------------------------------------- | ------------------ |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | ✅                              | §0 Track B + §3.2 + playbook §8.4 PASS | 低                 |
| `BATCH_01_HARDENING_RULES.md`                   | ✅                              | §1–§10 硬停；§3 live 须授权 YAML       | 低                 |
| `BATCH_01_TASK_CARD_MANIFEST.md`                | ✅                              | Wave D B01-023 行                      | 低                 |
| `BATCH_01_MODEL_SOURCE_READINESS/README.md`     | ✅                              | Batch 01 入口                          | 低                 |
| `ROUND_3_DATA_PRODUCTION_READINESS/README.md`   | ✅                              | Round 3 父入口                         | 低                 |
| `BATCH_01_ADVERSARIAL_AUDIT.md`                 | ✅                              | 对抗性审计来源                         | 低                 |
| `BATCH_01_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` | N/A                             | 主仓已有；worktree 待 rebase           | 低（Plan 不阻塞）  |
| `FIRST_BATCH_SELF_CHECK.md`                     | ✅                              | 首包自检                               | 低                 |
| `agent-toolchain.md`                            | ✅                              | Boot 工具路由                          | 低                 |
| `complex-task-planning-protocol.md`             | ✅                              | Plan/Execute 门控                      | 低                 |
| `authority_graph.yaml`                          | ✅                              | layer5_evidence 模块路由               | 低                 |
| `ROUND3_HANDOFF.md`                             | ✅                              | Round 交接                             | 低                 |
| `docs/ops/verification_commands.md`             | ✅                              | Round 3 gate hygiene                   | 低                 |
| `RESOLVED_ISSUES_REGISTRY.md`                   | ✅                              | 已闭合项只读                           | 低                 |
| playbook §3.2 全表                              | ✅ SCI-B                        | L5 专读零遗留                          | 低                 |
| hardening §3–§7                                 | ✅ §0 / §1.4a                   | live 授权 + registry 主会话            | 低                 |
| §2.5/§2.6                                       | ✅ §0 / §1.4a / worktree-slices | `layer5_evidence/**` 独占              | 低                 |
| `/to-issues` vertical-slices                    | ✅ §8 + research                | 六切片 ↔ §9.0–9.6 1:1                  | 低                 |
| `R3D-023-01`..`05` + SLICE-GATES                | ✅ §2 / §8 / §9                 | roadmap 映射                           | 低                 |
| `PROMPT_023b`                                   | N/A                             | 不存在                                 | 已用 §16+023A 替代 |
| §16 Execute Boot                                | ✅ §0                           | 全量 pytest 须绿（master 基线债已知）  | 中                 |

**must read original task card** — `023_implement_layer5_evidence_chain.md` 为 AC 原文权威。
