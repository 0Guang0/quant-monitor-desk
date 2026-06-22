# Loop Engineering Task Flow Refactor Plan

> 目的：把当前复杂任务流程从“用户频繁提醒、agent 手动翻 docs/specs、测试意图不清、evidence 散落、项目地图 stale”改造成“agent 自动读取权威上下文、测试语义可追溯、功能验收可证明、证据集中索引、项目地图自动生成”的可落地机制。  
> 读者：本地执行 agent、Trellis 维护者、任务流程改造执行者。  
> 范围：任务流程、复杂任务协议、上下文路由、测试语义、功能验证、证据索引、项目地图。  
> 非目标：不重写业务功能；不废弃现有 Plan/Execute/Audit/Repair/Finish；不删除现有 docs/specs，而是在其上增加机器可读路由与验证层。

---

## 0. 必须解决的五个问题

本轮流程迭代必须至少解决以下 P0–P4。任一未落地，视为任务流程改造未完成。

| 优先级 | 必解问题                      | 目标                                                                     |
| ------ | ----------------------------- | ------------------------------------------------------------------------ |
| **P0** | agent 不读 `docs/` / `specs/` | 建立机器可读上下文路由，强制 agent 自动读取相关设计、规则、契约、任务卡  |
| **P1** | 测试不知道测什么              | 建立测试语义目录，明确每个测试的 purpose、验证对象、失败含义             |
| **P2** | 功能如何验证不清楚            | 建立功能验证矩阵，把 AC / 功能 / 规则 / 契约映射到 tests 或 audit checks |
| **P3** | evidence 散落                 | 每个复杂任务生成统一 evidence index / loop manifest / audit matrix       |
| **P4** | 项目地图 stale                | 从机器可读配置自动生成 project map，并在 CI 中检查是否过期               |

---

## 1. 当前问题诊断

当前项目已经具备较强的复杂任务协议能力：

- `MASTER.plan.md` 定义复杂任务主计划。
- `AUDIT.plan.md` 定义 A1–A8 维度审计。
- `implement.jsonl` / `audit.jsonl` 用于 agent 上下文注入。
- `execute-evidence/`、`repair-evidence/`、`audit.report.md` 用于保存执行、审计、修复证据。
- `docs/INDEX.md`、`MIGRATION_MAP.md`、`docs/ops/verification_commands.md` 已经具备人工导航能力。

但核心缺口是：

1. **人工索引不是 agent 路由**  
   `docs/INDEX.md` 和 `MIGRATION_MAP.md` 是给人看的导航，不是机器可执行的上下文路由。agent 不会稳定地根据任务自动选择应读的 `docs/modules/*`、`specs/contracts/*`、`docs/quality/*`、`docs/implementation_tasks/*`。

2. **测试只有命令，不足以表达验证语义**  
   `docs/ops/verification_commands.md` 已有命令矩阵，但没有统一回答：每个测试为什么存在、验证哪个设计/规则/契约、失败说明哪个业务假设失效。

3. **功能验收与测试之间缺少强绑定**  
   `MASTER.plan.md` 可以列 AC，测试文件可以存在，但缺少全局矩阵证明：每个 AC 被哪个测试或 audit check 覆盖。

4. **证据没有统一入口**  
   evidence 分散在 task 目录多个位置，后续 agent 需要人工判断哪些证据是最终可信入口。

5. **项目地图靠人工维护，容易 stale**  
   `MIGRATION_MAP.md` 过大，不适合作为每次 agent 任务的主入口；也缺少自动生成和 CI stale 检查。

---

## 2. 目标架构

目标不是再增加一层长文档，而是增加四类机器可读文件和一组校验脚本。

```text
现有 docs/specs/tasks/tests
        ↓
authority_graph.yaml          # P0：上下文权威图
        ↓
context_router.py             # 自动生成 context_pack
        ↓
context_pack.json             # 每个任务的唯一上下文入口
        ↓
Plan / Execute / Audit / Repair
        ↓
test_catalog.yaml             # P1：测试语义
feature_verification_matrix   # P2：功能如何验证
contract_coverage.yaml        # P2：契约如何验证
        ↓
loop_manifest.json            # P3：AC→测试→证据→审计→修复链
_evidence_index.json          # P3：统一证据入口
audit_matrix.json             # P3：审计结论机器可读
        ↓
generated project map         # P4：自动生成项目地图
```

执行原则：

```text
用户不再负责告诉 agent 去哪里找文档；
用户不再负责解释每个测试为什么存在；
用户不再负责从散落 evidence 中判断任务状态；
用户只负责业务授权、目标变更、风险接受、真实生产/外部资源授权。
```

---

## 3. P0 — 解决 agent 不读 docs/specs

### 3.1 概念

建立 **Authority Graph**。它是机器可读的上下文权威图，负责回答：

```text
当任务触及某模块、某目录、某测试、某功能时，agent 必须读取哪些 docs/specs/rules/contracts？
```

不能再依赖 agent 自己从 `docs/INDEX.md` 或 `MIGRATION_MAP.md` 中人工推断。

### 3.2 新增文件

```text
specs/context/authority_graph.yaml
```

示例：

```yaml
modules:
  layer2_sensors:
    implementation:
      - backend/app/layer2_sensors/**
    docs:
      - docs/modules/layer2_cross_asset_sensor.md
      - docs/architecture/module_boundary_matrix.md
    contracts:
      - specs/contracts/layer2_sensor_contract.yaml
      - specs/contracts/snapshot_lineage_contract.yaml
      - specs/contracts/resource_limits.yaml
    rules:
      - docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md
      - docs/implementation_tasks/GLOBAL_TESTING_POLICY.md
      - docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md
    implementation_tasks:
      - docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md
    tests:
      - tests/test_layer2_sensor_loader.py
      - tests/test_batch3_staged_downstream_gate.py
      - tests/test_batch25_production_data_gate.py
    forbidden_claims:
      - production-live ready
      - live production ingestion
    required_evidence:
      - context_pack.json
      - loop_manifest.json
      - evidence_index.json
      - audit_matrix.json
```

### 3.3 新增脚本

```text
scripts/context_router.py
```

支持命令：

```bash
uv run python scripts/context_router.py --module layer2_sensors
uv run python scripts/context_router.py --files backend/app/layer2_sensors/snapshot_builder.py
uv run python scripts/context_router.py --task .trellis/tasks/06-22-round3-019-layer2-sensor
uv run python scripts/context_router.py --task .trellis/tasks/06-22-round3-019-layer2-sensor --check
```

输出：

```text
.trellis/tasks/<task>/context_pack.json
.trellis/tasks/<task>/research/context-router-output.md
```

### 3.4 `context_pack.json` 格式

```json
{
  "task": "06-22-round3-019-layer2-sensor",
  "modules": ["layer2_sensors"],
  "source_authorities": [
    {
      "type": "design",
      "path": "docs/modules/layer2_cross_asset_sensor.md",
      "reason": "Layer2 behavior and boundaries"
    },
    {
      "type": "contract",
      "path": "specs/contracts/layer2_sensor_contract.yaml",
      "reason": "Layer2 machine-readable contract"
    },
    {
      "type": "policy",
      "path": "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md",
      "reason": "staged-only limitation"
    }
  ],
  "tests": [
    {
      "path": "tests/test_layer2_sensor_loader.py",
      "purpose": "Layer2 registry/snapshot/observation behavior"
    }
  ],
  "forbidden_claims": ["production-live ready", "live production ingestion"],
  "required_evidence": [
    "loop_manifest.json",
    "evidence_index.json",
    "audit_matrix.json"
  ]
}
```

### 3.5 协议接入点

修改复杂任务协议：

```text
Plan P0：必须运行 context_router.py。
Plan freeze：必须检查 context_pack.json 存在且路径有效。
Execute：必须先读 context_pack.json，不得自行猜 docs/specs。
Audit A1/A5/A8：必须验证 context_pack 是否覆盖任务 touched modules / AC / tests。
```

`implement.jsonl` 规则：

```text
第 1 条：MASTER.plan.md
第 2 条：context_pack.json
后续：context_pack 中无法摘要、必须原文读取的 authority 文件
```

`audit.jsonl` 规则：

```text
第 1 条：AUDIT.plan.md
第 2 条：context_pack.json
后续：audit 必须原文读取的 source authority
```

### 3.6 P0 验收标准

P0 完成必须满足：

```text
[ ] specs/context/authority_graph.yaml 存在
[ ] scripts/context_router.py 存在
[ ] 至少覆盖当前 Round 3 相关模块：layer1_axes、layer2_sensors、layer5_evidence、datasources、validators、ops
[ ] context_router 能根据 task 生成 context_pack.json
[ ] context_pack.json 中 docs/specs/rules/tests 路径全部存在
[ ] validate-plan-freeze 或新增 validator 会检查 context_pack.json
[ ] AGENTS.md / complex-task-planning-protocol.md 明确：agent 不得向用户询问 docs/specs 路径
```

---

## 4. P1 — 解决测试不知道测什么

### 4.1 概念

建立 **Test Catalog**。每个测试必须回答：

```text
这个测试为什么存在？
验证哪个设计文档？
验证哪个规则？
验证哪个契约？
失败代表什么业务风险？
```

### 4.2 新增文件

```text
tests/test_catalog.yaml
```

示例：

```yaml
tests/test_batch3_staged_downstream_gate.py:
  purpose: "确保 Batch 3 只能 staged-only，不得被误读为 production-live readiness"
  type: policy-contract
  verifies:
    docs:
      - docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md
      - docs/quality/production_live_pilot_policy.md
      - docs/ROUND3_HANDOFF.md
    specs: []
    rules:
      - docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md
  protected_claims:
    forbidden:
      - production-live ready
      - live production ingestion
    required:
      - staged-only
      - does not open production-live
  command: "uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q"
  failure_meaning: "Batch 3 gate language or references drifted; downstream agent may wrongly assume live production readiness."
  evidence_required: "pytest output + doc link check"

tests/test_layer2_sensor_loader.py:
  purpose: "验证 Layer2 sensor loader、snapshot、observation、lineage、ResourceGuard 行为"
  type: runtime-contract
  verifies:
    docs:
      - docs/modules/layer2_cross_asset_sensor.md
    specs:
      - specs/contracts/layer2_sensor_contract.yaml
      - specs/contracts/snapshot_lineage_contract.yaml
      - specs/contracts/resource_limits.yaml
  command: "uv run python -m pytest tests/test_layer2_sensor_loader.py -q"
  failure_meaning: "Layer2 runtime behavior no longer符合设计/契约。"
  evidence_required: "pytest output"
```

### 4.3 新增脚本

```text
scripts/check_test_catalog.py
```

检查规则：

```text
- 每个 tests/test_*.py 必须登记在 tests/test_catalog.yaml。
- 每个 entry 必须有 purpose/type/verifies/command/failure_meaning。
- verifies.docs / verifies.specs / verifies.rules 路径必须存在。
- docs/ops/verification_commands.md 中列出的测试必须登记。
- MASTER.plan.md §9/§10 引用的测试必须登记。
```

推荐命令：

```bash
uv run python scripts/check_test_catalog.py
```

### 4.4 协议接入点

修改复杂任务协议：

```text
Plan P2/P4：为任务新增或引用测试时，必须更新 tests/test_catalog.yaml。
Execute：新增测试前先检查 test_catalog 是否已有同类测试语义。
Audit A8：测试缺口审计必须读取 test_catalog，而不是只看测试文件存在。
Finish：如果有新增测试但未登记 test_catalog，不得 finish-work。
```

### 4.5 P1 验收标准

```text
[ ] tests/test_catalog.yaml 存在
[ ] Round 3 gate hygiene 相关测试全部登记
[ ] 至少覆盖当前活跃模块测试：layer1、layer2、production gate、source routing、write manager、ResourceGuard
[ ] scripts/check_test_catalog.py 存在并可运行
[ ] 新增测试未登记时 check_test_catalog fail
[ ] docs/ops/verification_commands.md 中的测试与 test_catalog 一致
```

---

## 5. P2 — 解决功能如何验证

### 5.1 概念

建立 **Feature Verification Matrix** 和 **Contract Coverage Matrix**。它们回答：

```text
每个功能 / AC 如何验证？
每个设计/规则/契约如何被测试或审计覆盖？
哪些必须有负向测试？
哪些只能通过 audit check 验证？
```

### 5.2 新增文件：功能验证矩阵

```text
specs/verification/feature_verification_matrix.yaml
```

示例：

```yaml
features:
  R3-B3-STAGED-DOWNSTREAM-GATE:
    description: "Batch 3 下游只能 staged-only"
    authorities:
      - docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md
      - docs/quality/production_live_pilot_policy.md
      - docs/ROUND3_HANDOFF.md
    acceptance:
      - id: AC-STAGED-001
        statement: "Batch 3 不得声明 production-live readiness"
        tests:
          - tests/test_batch3_staged_downstream_gate.py::test_batch3_staged_gate_records_fail_closed_decisions
          - tests/test_batch25_production_data_gate.py::test_batch25_evidence_is_staged_not_production_live
        verification_type: policy-negative
        evidence: pytest-output
      - id: AC-STAGED-002
        statement: "018C probe PASS 不得关闭 R3-B2.75-REQ2-EM"
        tests:
          - tests/test_fred_staged_semantics.py
        verification_type: registry-contract
        evidence: pytest-output

  layer2_sensor:
    authorities:
      - docs/modules/layer2_cross_asset_sensor.md
      - specs/contracts/layer2_sensor_contract.yaml
    acceptance:
      - id: AC-L2-001
        statement: "Layer2 snapshot 必须 deterministic hash"
        tests:
          - tests/test_layer2_sensor_loader.py::test_snapshot_hash_is_deterministic
        verification_type: runtime-contract
      - id: AC-L2-002
        statement: "ResourceGuard HARD_STOP 必须中止批处理"
        tests:
          - tests/test_layer2_sensor_loader.py::test_resource_guard_hard_stop_aborts_snapshot
        verification_type: negative-runtime
```

### 5.3 新增文件：契约覆盖矩阵

```text
specs/verification/contract_coverage.yaml
```

示例：

```yaml
specs/contracts/source_route_contract.yaml:
  requirements:
    SOURCE_ROUTE_READY_REQUIRED:
      text: "Route must be READY before live fetch"
      tests:
        - tests/test_batch275_live_pilot_gate.py::test_route_not_ready_blocks_fetch
        - tests/test_source_route_planner.py
      negative_required: true

specs/contracts/write_contract.yaml:
  requirements:
    WRITE_MANAGER_ONLY:
      text: "Clean table writes must go through DuckDBWriteManager"
      tests:
        - tests/test_write_manager.py
        - tests/test_db_validation_gate.py
      negative_required: true
```

### 5.4 新增脚本

```text
scripts/check_verification_matrix.py
scripts/check_contract_coverage.py
```

`check_verification_matrix.py` 检查：

```text
- 每个 feature acceptance 必须有 tests 或 audit_check。
- tests 必须存在于 tests/test_catalog.yaml。
- authorities 路径必须存在。
- 涉及 production/live/security/data mutation 的 acceptance 必须有 negative 测试或 audit_check。
- MASTER §2 AC 必须能映射到 feature_verification_matrix。
```

`check_contract_coverage.py` 检查：

```text
- 每个 specs/contracts/*.yaml 必须有 coverage entry 或 explicit waiver。
- 每个 requirement 必须有 tests 或 audit_check。
- negative_required 必须有负向测试。
- tests 必须登记在 tests/test_catalog.yaml。
```

推荐命令：

```bash
uv run python scripts/check_verification_matrix.py
uv run python scripts/check_contract_coverage.py
```

### 5.5 协议接入点

修改复杂任务协议：

```text
Plan P1：每条 AC 必须绑定 feature_verification_matrix entry。
Plan P4：MASTER §9/§10 只能引用 matrix/catalog 中登记过的测试。
Execute：如果新增测试，必须同步 test_catalog 和 verification_matrix。
Audit A5：必须从 feature_verification_matrix 追踪 AC source-chain。
Audit A8：必须检查缺少负向测试的 production/live/security/data mutation AC。
```

### 5.6 P2 验收标准

```text
[ ] specs/verification/feature_verification_matrix.yaml 存在
[ ] specs/verification/contract_coverage.yaml 存在
[ ] scripts/check_verification_matrix.py 存在
[ ] scripts/check_contract_coverage.py 存在
[ ] 当前 Round 3 staged/live gate、Layer2 sensor、ResourceGuard、WriteManager 至少有 matrix entry
[ ] 生产/live/security/data mutation 相关 AC 有负向测试或 audit_check
[ ] MASTER §9/§10 引用未登记测试时 validator fail
```

---

## 6. P3 — 解决 evidence 散落

### 6.1 概念

每个复杂任务必须有统一 evidence 入口。agent 不能再遍历多个目录猜测最终证据。

新增四个任务级产物：

```text
context_pack.json
loop_manifest.json
evidence_index.json
audit_matrix.json
```

### 6.2 `loop_manifest.json`

职责：串联 AC → source → execute step → tests → evidence → audit → repair → final state。

示例：

```json
{
  "task": "06-21-round3-batch2-75-live-pilot",
  "status": "pass_after_repair",
  "acs": [
    {
      "id": "AC-1",
      "source": "docs/implementation_tasks/...",
      "master_section": "§2",
      "execute_steps": ["8.1", "8.2"],
      "tests": ["tests/test_batch275_live_pilot_gate.py"],
      "evidence": ["execute-evidence/8.1-green.txt"],
      "audit_dimensions": ["A3", "A5", "A8"],
      "repair_items": ["R-1", "R-2"],
      "final_state": "closed"
    }
  ]
}
```

### 6.3 `evidence_index.json`

职责：给所有 evidence 一个唯一索引。

示例：

```json
{
  "task": "06-22-round3-019-layer2-sensor",
  "plan": {
    "freeze": "plan.freeze.md",
    "context_pack": "context_pack.json"
  },
  "execute": {
    "steps": {
      "8.1": {
        "red": "research/execute-evidence/8.1-red.txt",
        "green": "research/execute-evidence/8.1-green.txt",
        "tests": ["tests/test_layer2_sensor_loader.py"]
      }
    }
  },
  "audit": {
    "matrix": "audit_matrix.json",
    "sections": {
      "A1": "research/audit-sections/A1.md",
      "A8": "research/audit-sections/A8.md"
    }
  },
  "repair": {
    "items": {}
  },
  "final": {
    "status": "PASS_AFTER_REPAIR",
    "merge_gate": "execute-evidence/merge_gate_report.md"
  }
}
```

### 6.4 `audit_matrix.json`

职责：让 Audit 结论机器可读。

示例：

```json
{
  "dimensions": {
    "A1": {
      "result": "pass",
      "evidence": "research/audit-sections/A1.md",
      "source_trace": true
    },
    "A3": { "result": "fail_then_fixed", "repair": ["R-1"] },
    "A8": { "result": "fail_then_fixed", "tests_added": ["tests/test_x.py"] }
  },
  "orthogonal_checks": {
    "spec_scope": "pass",
    "security": "pass_after_repair",
    "test_gap": "pass_after_repair",
    "prod_hash": "pass"
  },
  "final": "PASS_AFTER_REPAIR"
}
```

### 6.5 新增脚本

```text
scripts/check_task_evidence.py
scripts/loop_dashboard.py
```

`check_task_evidence.py` 检查：

```text
- context_pack.json 存在且路径有效。
- loop_manifest.json 覆盖 MASTER §2 AC。
- evidence_index.json 引用的证据文件存在。
- audit_matrix.json final 与 audit.report.md 最终结论一致。
- 任一 audit FAIL 必须有 repair 或 approved deferred。
- task.json status 与 audit/repair/final 状态一致。
```

`loop_dashboard.py` 输出所有任务状态：

```text
Task                                      Status              Blocker
06-21-round3-batch2-75-live-pilot         PASS_AFTER_REPAIR   final status sync needed
06-22-round3-batch3-staged-gate           CLOSED              none
06-22-round3-019-layer2-sensor            MERGE_GATE_FIXED    missing audit_matrix.json
```

推荐命令：

```bash
uv run python scripts/check_task_evidence.py .trellis/tasks/<task>
uv run python scripts/loop_dashboard.py
```

### 6.6 协议接入点

```text
Plan P4：生成 loop_manifest.json 初稿和 evidence_index.json 初稿。
Execute：每完成一个 §8.x，更新 evidence_index.json。
Audit：生成 audit_matrix.json。
Repair：更新 loop_manifest.json 和 evidence_index.json。
Finish：check_task_evidence 必须通过。
```

### 6.7 P3 验收标准

```text
[ ] scripts/check_task_evidence.py 存在
[ ] scripts/loop_dashboard.py 存在
[ ] 每个新复杂任务必须生成 context_pack.json / loop_manifest.json / evidence_index.json
[ ] Audit 阶段必须生成 audit_matrix.json
[ ] evidence_index 引用不存在文件时 fail
[ ] audit FAIL 但无 repair/deferred 时 fail
[ ] repair PASS 但 task.json 仍 in_progress 且无 blocker 说明时 fail
```

---

## 7. P4 — 解决项目地图 stale

### 7.1 概念

`MIGRATION_MAP.md` 和 `docs/INDEX.md` 保留给人阅读，但项目地图的机器入口必须自动生成。人工维护的大文件不能作为 agent 主要上下文来源。

### 7.2 新增生成文件

```text
docs/generated/project_map.generated.md
docs/generated/project_map.generated.json
```

### 7.3 新增脚本

```text
scripts/generate_project_map.py
```

输入：

```text
specs/context/authority_graph.yaml
tests/test_catalog.yaml
specs/verification/feature_verification_matrix.yaml
specs/verification/contract_coverage.yaml
```

输出内容：

```text
模块 → 实现目录 → 设计文档 → 契约 → 规则 → 测试 → 验证命令 → 禁止项 → evidence
```

推荐命令：

```bash
uv run python scripts/generate_project_map.py
uv run python scripts/generate_project_map.py --check
```

### 7.4 CI 接入

新增 CI gate：

```bash
uv run python scripts/generate_project_map.py --check
uv run python scripts/check_test_catalog.py
uv run python scripts/check_verification_matrix.py
uv run python scripts/check_contract_coverage.py
```

### 7.5 P4 验收标准

```text
[ ] docs/generated/project_map.generated.md 存在
[ ] docs/generated/project_map.generated.json 存在
[ ] scripts/generate_project_map.py 存在
[ ] --check 能发现 stale map
[ ] docs/INDEX.md 可链接 generated map
[ ] AGENTS.md 明确：agent 优先读取 generated map / context_pack，而不是人工搜索 MIGRATION_MAP
```

---

## 8. 复杂任务协议精简方案

当前复杂任务 Plan 可适度精简，但关键 skill 不得跳过。

### 8.1 不得跳过的核心 skill

复杂任务 Plan 中以下 skill 必须保留：

| Skill                                                  | 用途                                           | 是否可跳过   |
| ------------------------------------------------------ | ---------------------------------------------- | ------------ |
| `trellis-plan`                                         | 进入 Plan 模式、读取原始任务包、建立任务上下文 | 不可跳过     |
| `spec-driven-development`                              | 把需求转成可验证规格与 AC                      | 不可跳过     |
| `grill-me` / `interview-me` / `grill-with-docs` 三选一 | 对需求、边界、风险做反向质疑                   | 不可全部跳过 |
| `to-issues`                                            | 垂直切片与任务拆分                             | 不可跳过     |
| `writing-plans`                                        | 生成可执行步骤、RED/GREEN 命令、证据列         | 不可跳过     |
| `trellis-before-dev`                                   | 冻结实现上下文、manifest、规则对齐             | 不可跳过     |
| `doubt-driven-development`                             | 冻结前 fresh-context 对抗审查                  | 不可跳过     |

### 8.2 条件 skill

| Skill                       | 触发条件                                |
| --------------------------- | --------------------------------------- |
| `trellis-brainstorm`        | 用户需求模糊、目标不稳定、需要交互澄清  |
| `domain-modeling`           | 领域术语不清、缺少统一概念模型          |
| `api-and-interface-design`  | 新增/修改公共 API、模块接口、跨模块契约 |
| `codebase-design`           | 新模块、复杂重构、架构边界变更          |
| `prototype`                 | 高风险设计不确定，需要可丢弃验证        |
| `source-driven-development` | 依赖第三方库/API/框架细节               |

### 8.3 精简后的 Plan 阶段

#### P0 — Context Boot

目标：解决 agent 不读 docs/specs。

必做：

```text
1. Load trellis-plan。
2. 读取原始任务包入口。
3. 运行 context_router.py。
4. 生成 context_pack.json。
5. 生成 research/context-router-output.md。
6. 生成 research/original-plan-trace.md。
```

产物：

```text
context_pack.json
research/context-router-output.md
research/original-plan-trace.md
research/plan-boot.md
```

#### P1 — Spec & Boundary

目标：把需求变成可验证 AC，并完成边界质疑。

必做 skill：

```text
spec-driven-development
grill-me / interview-me / grill-with-docs 三选一
```

产物：

```text
MASTER.plan.md §1–§3
research/grill-me-session.md 或等价文件
```

要求：

```text
每条 AC 必须可验证。
每条 AC 必须能映射到 feature_verification_matrix。
禁止把“继续研究”“人工确认后再说”写成 AC。
```

#### P2 — Slices & Verification

目标：解决功能如何验证。

必做 skill：

```text
to-issues
```

产物：

```text
research/vertical-slices.md
loop_manifest.json 初稿
feature_verification_matrix 更新或任务级补丁
tests/test_catalog.yaml 更新或确认
```

要求：

```text
每个 slice 必须有 AC、allowed files、forbidden files、verification、evidence。
每个 slice 必须有 tests 或 audit_check。
生产/live/security/data mutation 相关 slice 必须有负向测试或 audit-sandbox 检查。
```

#### P3 — Design Only When Needed

目标：减少无必要 design.md 噪音，但保留真正需要的设计。

触发条件任一满足则必须进入 P3：

```text
1. 新增模块/package。
2. 新增会被两个以上 caller 调用的公共函数/类/接口。
3. 修改 schema/migration。
4. 修改生产/数据写入/权限/资源边界。
5. 涉及跨模块契约。
```

条件 skill：

```text
api-and-interface-design
codebase-design
prototype
source-driven-development
```

可跳过条件：

```text
任务只修改局部实现；
不新增公共接口；
不修改 schema；
不触碰生产/data/security/resource 边界。
```

跳过时必须写入 MASTER §0：

```text
skip_design_reason: <三条以上明确理由>
```

#### P4 — Execute Plan & Freeze

目标：冻结执行计划、上下文、测试、证据入口。

必做 skill：

```text
writing-plans
trellis-before-dev
doubt-driven-development
```

产物：

```text
MASTER.plan.md §8–§12
AUDIT.plan.md
implement.jsonl
audit.jsonl
check.jsonl
evidence_index.json 初稿
audit_matrix.json skeleton
plan.freeze.md
```

要求：

```text
§8 每步必须有 RED 命令、GREEN 命令、RED 证据、GREEN 证据。
implement.jsonl 第一条 = MASTER.plan.md。
implement.jsonl 第二条 = context_pack.json。
audit.jsonl 必须包含 AUDIT.plan.md 和 context_pack.json。
MASTER §9/§10 中的测试必须存在于 test_catalog / verification_matrix。
```

---

## 9. 精简后 Execute / Audit / Repair / Finish 调整

### Execute

新增硬规则：

```text
1. 先读 context_pack.json。
2. 每完成一个 §8.x，更新 evidence_index.json。
3. 新增或修改测试时，同步 test_catalog 和 verification_matrix。
4. 不得询问用户 docs/specs 路径。
```

### Audit

新增硬规则：

```text
1. A1 必须验证 context_pack 覆盖 source authority。
2. A5 必须验证 loop_manifest 中 AC source-chain 完整。
3. A8 必须验证 test_catalog / verification_matrix 是否存在测试缺口。
4. Audit 完成后必须生成 audit_matrix.json。
```

### Repair

新增硬规则：

```text
1. 每个 repair item 必须回写 loop_manifest。
2. 每个 repair evidence 必须登记到 evidence_index。
3. Repair PASS 后 audit_matrix.final 必须同步为 PASS_AFTER_REPAIR。
```

### Finish

新增硬规则：

```text
1. scripts/check_task_evidence.py 必须通过。
2. scripts/check_test_catalog.py 必须通过。
3. scripts/check_verification_matrix.py 必须通过。
4. scripts/generate_project_map.py --check 必须通过。
```

---

## 10. 用户介入最小化规则

新增文件：

```text
docs/ops/user_intervention_policy.md
```

必须问用户：

```text
1. 改变业务目标或验收标准。
2. 启用真实生产数据、真实账号、付费 API、外部网络。
3. 提高 ResourceGuard 限制。
4. 新增大型依赖或更换核心架构。
5. 前端最终信息架构、视觉、交互拍板。
6. 将 deferred 风险改成 accepted risk。
7. 需要用户业务授权或合规确认。
```

不得问用户，agent 必须自行解决：

```text
1. 去哪里找 docs/specs。
2. 某模块应读取哪些 contract。
3. 某测试验证什么。
4. 如何生成 context_pack。
5. 如何收集 evidence。
6. 如何运行普通本地/CI 验证。
7. 如何判断某测试失败对应哪个契约或规则。
```

---

## 11. 分阶段实施计划

### Phase 1 — P0 上下文路由

交付：

```text
specs/context/authority_graph.yaml
scripts/context_router.py
AGENTS.md / complex-task-planning-protocol.md 接入说明
```

验收：

```bash
uv run python scripts/context_router.py --module layer2_sensors
uv run python scripts/context_router.py --task .trellis/tasks/<sample-task> --check
```

### Phase 2 — P1 测试语义

交付：

```text
tests/test_catalog.yaml
scripts/check_test_catalog.py
```

验收：

```bash
uv run python scripts/check_test_catalog.py
```

### Phase 3 — P2 功能/契约验证矩阵

交付：

```text
specs/verification/feature_verification_matrix.yaml
specs/verification/contract_coverage.yaml
scripts/check_verification_matrix.py
scripts/check_contract_coverage.py
```

验收：

```bash
uv run python scripts/check_verification_matrix.py
uv run python scripts/check_contract_coverage.py
```

### Phase 4 — P3 证据集中

交付：

```text
scripts/check_task_evidence.py
scripts/loop_dashboard.py
任务级 context_pack.json / loop_manifest.json / evidence_index.json / audit_matrix.json 模板
```

验收：

```bash
uv run python scripts/check_task_evidence.py .trellis/tasks/<sample-task>
uv run python scripts/loop_dashboard.py
```

### Phase 5 — P4 自动项目地图

交付：

```text
scripts/generate_project_map.py
docs/generated/project_map.generated.md
docs/generated/project_map.generated.json
CI gate 更新
```

验收：

```bash
uv run python scripts/generate_project_map.py --check
```

---

## 12. CI 建议

新增 CI 步骤：

```bash
uv run python scripts/check_test_catalog.py
uv run python scripts/check_verification_matrix.py
uv run python scripts/check_contract_coverage.py
uv run python scripts/generate_project_map.py --check
uv run python scripts/loop_dashboard.py --check
```

可逐步从 warn-only 迁移到 fail-closed：

```text
第 1 周：warn-only，输出缺口列表。
第 2 周：P0/P1 fail-closed。
第 3 周：P2/P3 fail-closed。
第 4 周：P4 fail-closed。
```

---

## 13. 最小可行版本（MVP）

若执行资源有限，先做以下最小集合：

```text
specs/context/authority_graph.yaml
tests/test_catalog.yaml
specs/verification/feature_verification_matrix.yaml
scripts/context_router.py
scripts/check_test_catalog.py
scripts/check_verification_matrix.py
```

MVP 验收：

```text
1. agent 能通过 context_router 自动找到 docs/specs/tests。
2. Round 3 gate tests 在 test_catalog 中有 purpose/failure_meaning。
3. 至少 3 个功能有 AC→test/audit_check 映射。
4. 新复杂任务会生成 context_pack.json。
5. 新增测试未登记会被 check_test_catalog 拦截。
```

---

## 14. 完成定义

本任务流程改造完成，必须同时满足：

```text
[ ] P0：agent 自动读取 docs/specs 的 context router 已落地
[ ] P1：测试语义 test_catalog 已落地
[ ] P2：功能验证矩阵和契约覆盖矩阵已落地
[ ] P3：任务 evidence_index / loop_manifest / audit_matrix 已落地
[ ] P4：project map 自动生成与 stale 检查已落地
[ ] 精简后的复杂任务协议已写入 .trellis/spec/guides/complex-task-planning-protocol.md 或同等权威位置
[ ] AGENTS.md 已引用新规则
[ ] CI 或本地 gate 能检查上述文件一致性
[ ] 用户介入政策已写入 docs/ops/user_intervention_policy.md
```

完成后的目标效果：

```text
用户不再频繁提醒 agent 查 docs/specs；
agent 能解释每个测试验证什么；
每个功能 AC 都能追溯到测试或 audit check；
evidence 有统一入口；
项目地图由脚本生成，不再靠人工维护。
```
