# Audit 计划 — B3F-LIN lineage / Layer3 registry closure

| 字段            | 值                                      |
| --------------- | --------------------------------------- |
| slug            | `round3f-batch6-lineage-layer3-closure` |
| Playbook ID     | B3F-LIN                                 |
| audit.jsonl     | 第一条 = 本文件                         |
| AUDIT_PROD_ROOT | N/A（staged/tmp_path only）             |

## 0.1 Trace Authority Set

| 类别          | 文件                                             | 用途                   |
| ------------- | ------------------------------------------------ | ---------------------- |
| 协调包        | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.2 / §8.2   | scope / PASS 命令      |
| MASTER        | `MASTER.plan.md` §8–§9                           | Execute 证据与全量验收 |
| manifest      | `research/closure-evidence-manifest.yaml`        | pytest→roadmap 映射    |
| registry 草案 | `research/registry-proposed-delta.md`            | PROPOSED only          |
| lineage 契约  | `specs/contracts/snapshot_lineage_contract.yaml` | A1/A4                  |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行 |
| --- | ---------------- | --------------------------------------------------------- | -------- | ------ |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]    |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]    |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做     | [ ]    |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做     | [ ]    |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]    |
| A6  | audit-perf       | doubt-driven-development                                  | **SKIP** | [ ]    |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]    |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]    |
| A9  | 主会话           | —                                                         | 必做     | [ ]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                                                                                   | 环境          | 通过条件                                              | 已执行 |
| --- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ----------------------------------------------------- | ------ |
| A1  | read-only       | 对照 `MASTER.plan.md` §8、`closure-evidence-manifest.yaml`、`registry-proposed-delta.md`；`git diff 7f628c9..HEAD` 无 `backend/` 生产逻辑变更 | local         | scope intact；无 RESOLVED registry                    | [ ]    |
| A2  | review-only     | ponytail-review `tests/test_layer2_sensor_loader.py` autouse ResourceGuard mock                                                               | local         | ponytail 注释 + `@pytest.mark.resourceguard` 专项豁免 | [ ]    |
| A3  | static          | `rg` production clean write / live source 默认 / 三 registry RESOLVED                                                                         | local         | 零越界                                                | [ ]    |
| A4  | review-only     | lineage VR 绑定 + L3 manifest fail-closed 链一致                                                                                              | local         | 无阻断质量问题                                        | [ ]    |
| A5  | trace-ac        | AC R3F-LIN-01..03 + R3F-L3-01..02 ↔ `research/execute-evidence/*.txt`                                                                         | local         | RED/GREEN 含真实 pytest 输出                          | [ ]    |
| A5  | cli-sandbox     | Playbook §8.2 全命令（见下）                                                                                                                  | audit-sandbox | exit 0                                                | [ ]    |
| A6  | —               | **SKIP** — 无 hot path / SLA 变更                                                                                                             | —             | SKIP 记录                                             | [ ]    |
| A7  | cli-sandbox     | 见 §2.1 A7 冻结命令                                                                                                                           | audit-sandbox | init 幂等；§8.2 绿；无 prod 写                        | [ ]    |
| A8  | pytest-isolated | `tests/test_round3f_lineage_layer3_registry_closure.py` + L2 VR 负向（含 hash-only）                                                          | audit-sandbox | 五字段齐全；manifest 六键对齐                         | [ ]    |

### 2.1 A7 冻结命令（运维面）

```bash
uv sync --locked
QMD_DATA_ROOT=.audit-sandbox/data-a7-lin uv run python scripts/init_db.py
QMD_DATA_ROOT=.audit-sandbox/data-a7-lin uv run python scripts/init_db.py
QMD_RESOURCE_PROFILE=normal uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer2_sensor_loader.py -q
QMD_RESOURCE_PROFILE=normal uv run pytest tests/test_round3_audit_registry_alignment.py -q -k lineage
QMD_RESOURCE_PROFILE=normal uv run pytest tests/test_round3f_lineage_layer3_registry_closure.py -q
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/round3f-batch6-lineage-layer3-closure
```

| 步骤               | 通过条件                                                 |
| ------------------ | -------------------------------------------------------- |
| init 第 1 次       | exit 0；migrations applied                               |
| init 第 2 次       | exit 0；`applied none (up to date)`                      |
| Playbook §8.2 子集 | layer2+layer3 pytest exit 0                              |
| registry lineage   | `-k lineage` exit 0                                      |
| closure gate       | `test_round3f_lineage_layer3_registry_closure.py` exit 0 |
| handoff            | `validate-execute-handoff` exit 0                        |

**禁止项（A7）：** production DuckDB clean write；`docs/quality/` 三 registry 直接 RESOLVED；migration 列变更。

### 2.2 Playbook §8.2 全量验收（A5/A7 共用）

```bash
uv sync --locked
uv run pytest tests/test_layer3_snapshot_builder.py tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q -k lineage
uv run pytest tests/test_round3f_lineage_layer3_registry_closure.py -q
uv run pytest -q && uv run ruff check .
```

> closure gate 第三行与 `MASTER.plan.md` §9 对齐；Playbook §8.2 主表已交叉引用。

## 3. Audit Source Trace

| Item            | 原文                                          | AC                        | 证据                                                          |
| --------------- | --------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| R3F-L3-01       | `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY` O-01 | malformed bar fail-closed | `test_layer3Snapshot_malformedBarElement_rejects`             |
| R3F-L3-02       | O-02                                          | full row tuple rebuild    | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash` |
| R3F-LIN-02      | R3Y-LINEAGE-VR-001                            | VR binding ±              | `test_layer2Snapshot_lineage*`                                |
| R3F-LIN-01      | ADV-R3X partial                               | L3/L4 lineage             | `test_marketSnapshot_lineageUpstreamFromLayer3`               |
| R3F-LIN-03      | Wave-B reconcile                              | manifest + proposed delta | `test_round3f_lineage_layer3_registry_closure.py`             |
| partial hygiene | B01-LIN `06bcfde1`                            | 非 3D.3 全关              | `registry-proposed-delta.md`                                  |

## 4. Audit DoD

- [ ] A1–A8 报告 + `audit.report.md`
- [ ] A6 SKIP 已记录
- [ ] registry RESOLVED 由 B3F-REG / 主会话批处理（非本 Audit 必达）
- [ ] PASS 前不 finish-work
