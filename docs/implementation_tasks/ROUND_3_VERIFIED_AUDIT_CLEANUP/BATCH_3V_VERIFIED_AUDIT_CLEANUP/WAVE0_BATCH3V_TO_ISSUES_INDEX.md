# Wave 0 — Batch 3V `/to-issues` 任务卡骨架

> **格式：** `.claude/skills/to-issues/SKILL.md` · tracer-bullet 垂直切片（非按层横切）  
> **波次定位：** `R3H_PASS_EXECUTION_PLAN.md` Wave 0 — Round4 前 trust 底座；**不**做 production clean write / live fetch  
> **权威任务卡：** 本目录 `B02_*` / `B03_01` + `BATCH_3V_TASK_CARD_MANIFEST.md`  
> **协调：** `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.5 文件锁 · §7 merge 顺序  
> **状态：** 粒度 quiz 已裁决（§0.2）；Plan 3.5 冻结前同步 Trellis `research/vertical-slices.md`

---

## 0. Wave 级门控

| 项             | 内容                                                                               |
| -------------- | ---------------------------------------------------------------------------------- |
| **Wave 目标**  | 六张 Batch 3V 卡全部 **CLOSED**（或 VR 精确 re-defer + 主会话 registry reconcile） |
| **并行**       | 六路 worktree **可同时 Execute**；遵守 §2.5 核心文件组互斥                         |
| **串行 merge** | `integration/round3-batch3v` → 顺序 **C05 → C06 → C01 → C02 → C03 → C04**          |
| **Wave Done**  | 全量 `uv run pytest -q` 绿 + manifest/registry 主会话批闭合 + 六卡 archive         |
| **下游**       | 解锁 `R3H-06` Clean Schema（Wave 1）                                               |

### 0.1 六卡一览

| Manifest | Playbook | Trellis slug（已有/建议）               | 分支                                           | Track     |
| -------- | -------- | --------------------------------------- | ---------------------------------------------- | --------- |
| B3V-C05  | B3V-REG  | `round3v-registry-manifest-consistency` | `fix/round3v-registry-manifest-consistency`    | debt-lite |
| B3V-C06  | B3V-L5R  | `round3v-layer5-model-schema-reconcile` | `review/round3v-layer5-model-schema-reconcile` | debt-lite |
| B3V-C01  | B3V-OPS  | `round3v-contract-drift-write-modes`    | `fix/round3v-contract-drift-write-modes`       | complex   |
| B3V-C02  | B3V-DATA | `round3v-schema-hash-fail-closed`       | `fix/round3v-schema-hash-fail-closed`          | complex   |
| B3V-C03  | B3V-STOR | `round3v-rawstore-atomic-write`         | `fix/round3v-rawstore-atomic-write`            | complex   |
| B3V-C04  | B3V-SYNC | `round3v-sync-support-matrix-recovery`  | `fix/round3v-sync-support-matrix-recovery`     | complex   |

### 0.2 粒度 quiz 裁决（2026-06-28）

| 卡               | 裁决                                                                          | GitHub issue 数                                         |
| ---------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------- |
| **B3V-C05 REG**  | 整卡 **1 个 issue**（REG + DOC 竖条内用 checklist，不再拆 DOC-01/02/03 三票） | **1**                                                   |
| **B3V-C04 SYNC** | **SYNC-06 拆 3 票**：实现 → 测试 → 关账（路径 B 时实现票改为 handoff 文档票） | **+2**（相对原单票 SYNC-06；SYNC-BOOT..05 仍各 1 Step） |
| 其余四卡         | 维持 INDEX 默认竖条，不再 quiz                                                | 见各 §                                                  |

---

## 1. B3V-C05 · B3V-REG — Migration Registry & Manifest

**活卡：** [`B02_05_migration_registry_and_manifest_consistency.md`](B02_05_migration_registry_and_manifest_consistency.md)  
**Owns：** `VR-REG-001`, `VR-DOC-001`

### What to build

迁移 009 CHECK 覆盖与 `schema.sql` / registry / `MIGRATION_COVERAGE.md` 对齐；`FINAL_AUDIT_REPORT.md` restore-or-replace 决策并同步 README/MANIFEST/allowlist；manifest 存在性/哈希校验可失败可证明。

### Acceptance criteria

- [ ] `VR-REG-001` closed 或精确 re-defer（含 evidence / owner / phase）
- [ ] `VR-DOC-001` closed 或精确 re-defer
- [ ] `tests/test_manifest_files_check.py` TDD 绿；`check_manifest_files.py` 与 manifest 一致
- [ ] README/MANIFEST/final package rules 不再与文件树矛盾
- [ ] **禁止**伪造 `FINAL_AUDIT_REPORT.md` 内容；**禁止**无只读 DB 证据声称 prod 已 apply migration 009

### Blocked by

无（Wave 0 内 **merge 序 1**；Execute 可与其他卡并行）

### GitHub issue（整卡 1 票 · 用户 quiz 2026-06-28）

| Issue           | 标题（建议）                                              | 范围                             |
| --------------- | --------------------------------------------------------- | -------------------------------- |
| **REG-ISSUE-1** | `[B3V-REG] migration 009 + manifest/doc 树对齐 + checker` | `VR-REG-001` + `VR-DOC-001` 全卡 |

### 票内执行 checklist（非独立 issue）

| 序  | ID       | 竖条（票内 Step）                      | 交付物                                                                                     | 依赖              |
| --- | -------- | -------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------- |
| 0   | REG-BOOT | 基线矩阵                               | migration 009 ↔ schema ↔ registry 现状断言                                                 | —                 |
| 1   | REG-01   | Coverage matrix                        | `research/migration-009-coverage-matrix.md`                                                | BOOT              |
| 2   | REG-02   | Registry reconcile                     | proposed delta；UNRESOLVED/RESOLVED 无矛盾                                                 | REG-01            |
| 3   | DOC-ALL  | 文档树 + checker（原 DOC-01..03 合并） | restore/replace 决策 + README/MANIFEST/allowlist 一致 + `check_manifest_files.py` + pytest | REG-02 可并行起步 |

### Issue 骨架（复制到 GitHub）

```markdown
## [B3V-REG] migration 009 + manifest/doc 树对齐 + checker

**What to build:** 一张票关 `VR-REG-001` 与 `VR-DOC-001`：009 CHECK 覆盖矩阵与 registry 对齐；`FINAL_AUDIT_REPORT.md` restore-or-replace 并同步文档树；manifest 存在性/哈希检查可 FAIL 可证明。

**Acceptance criteria:**

- [ ] REG-01：coverage matrix 每 CHECK 一行（migration / schema / registry）
- [ ] REG-02：proposed registry delta；无 UNRESOLVED/RESOLVED 重复矛盾
- [ ] DOC-ALL：restore/replace ADR；README/MANIFEST/allowlist/final_package_rules 与文件树一致
- [ ] DOC-ALL：`tests/test_manifest_files_check.py` TDD 绿；`check_manifest_files.py` 与 manifest 一致
- [ ] 主会话批闭合 registry（本票只交 proposed delta）

**Blocked by:** 无

**Out of scope:** 伪造 FINAL_AUDIT 内容；无只读 DB 证据声称 prod 已 apply migration 009；无测试证明前重写 migration 009
```

---

## 2. B3V-C06 · B3V-L5R — Layer5 & Model Schema Reconcile

**活卡：** [`B03_01_layer5_model_schema_reconcile.md`](B03_01_layer5_model_schema_reconcile.md)  
**Owns：** `VR-L5-001`, `VR-MODEL-001`

### What to build

post Batch 01 master 上核对 Layer5 证据链与 L3/L4/L5 表「设计 vs 实现 vs deferred」矩阵； stale 关账或拆独立 follow-up branch；**本分支只 reconcile，不混 Batch 02 runtime 大改**。

### Acceptance criteria

- [ ] `research/l5-reconcile-matrix.md` 每 `VR-*` 一行（evidence / stale / follow-up）
- [ ] `tests/test_layer5_evidence_chain.py` + `tests/test_migration_coverage.py` 绿
- [ ] `VR-L5-001` / `VR-MODEL-001` closed、stale 或精确 split task
- [ ] **禁止** staged 测试通过即声称 Layer5 production-ready
- [ ] runtime 缺口 → **独立分支**，不在本 reconcile 分支改 `layer5_evidence/**`

### Blocked by

无（Wave 0 内 **merge 序 2**；只读 reconcile 可最早并行）

### Vertical slices

| 序  | ID        | 垂直切片        | 交付物                                                    | 依赖            | Step                                  |
| --- | --------- | --------------- | --------------------------------------------------------- | --------------- | ------------------------------------- |
| 0   | L5R-BOOT  | 基线证据        | post-Batch-01 commit + 现有测试绿快照                     | —               | `9.0-green.txt`                       |
| 1   | L5-01     | Layer5 状态矩阵 | evidence chain / provenance / agent-text / lineage 覆盖表 | BOOT            | `research/l5-reconcile-matrix.md` §L5 |
| 2   | L5-02     | Layer5 验证     | 上表每行有 test 名或 follow-up task ID                    | L5-01           | `9.1-green.txt`                       |
| 3   | MODEL-01  | L3/L4/L5 表矩阵 | designed / implemented / deferred 三列                    | BOOT            | `research/model-table-matrix.md`      |
| 4   | MODEL-02  | 文档对齐        | architecture/modules/schema 与矩阵一致                    | MODEL-01        | `9.2-green.txt`                       |
| 5   | L5R-CLOSE | VR 关账或 split | registry proposed delta + 必要时新 task 卡 ID             | L5-02, MODEL-02 | 主会话 registry                       |

---

## 3. B3V-C01 · B3V-OPS — Contract Drift & Write Modes

**活卡：** [`B02_01_contract_drift_and_write_modes.md`](B02_01_contract_drift_and_write_modes.md)  
**Trellis 草案：** `.trellis/tasks/round3v-contract-drift-write-modes/research/vertical-slices.md`  
**Owns：** `VR-OPS-001`, `VR-WRITE-001`

### What to build

`ops_db_inspect_contract.yaml` 为 db-inspect SSOT（或生成只读常量）；`write_contract.yaml` 区分 `implemented_modes` / `reserved_modes` 并与 `WriteManager` 漂移测试对齐。

### Acceptance criteria

- [ ] db-inspect **只读**；YAML↔运行时 key_tables + deferred 全量一致测绿
- [ ] `implemented_modes == WriteManager.SUPPORTED_MODES`
- [ ] 每个 `reserved_modes` 调用 `write()` 稳定错误、行数 0
- [ ] **禁止**实现 `manual_patch` / `replace_partition` / `schema_migration` 运行时行为

### Blocked by

无 Execute 阻塞；**B3V-C04 推荐**在本卡 merge 后 rebase（write crash-window 语义）

### Vertical slices

| 序  | ID       | 垂直切片        | 交付物                                    | 依赖     | Step                |
| --- | -------- | --------------- | ----------------------------------------- | -------- | ------------------- |
| 1   | OPS-01   | db-inspect SSOT | 从 YAML 加载 key_tables + deferred        | —        | `9.1-red/green.txt` |
| 2   | OPS-02   | OPS 漂移测      | 改 YAML 无代码则 RED                      | OPS-01   | `9.2-red/green.txt` |
| 3   | WRITE-01 | 写模式契约      | implemented / reserved 字段 + schema 引用 | —        | `9.3-red/green.txt` |
| 4   | WRITE-02 | 实现集漂移      | implemented == SUPPORTED_MODES            | WRITE-01 | `9.4-red/green.txt` |
| 5   | WRITE-03 | 预留模式拒绝    | reserved 稳定 ValueError                  | WRITE-01 | `9.5-red/green.txt` |

**不在切片内：** registry 闭合 — 主会话批处理。

---

## 4. B3V-C02 · B3V-DATA — Schema Hash Fail-Closed

**活卡：** [`B02_02_schema_hash_fail_closed.md`](B02_02_schema_hash_fail_closed.md)  
**Trellis 草案：** `.trellis/tasks/round3v-schema-hash-fail-closed/research/vertical-slices.md`  
**Owns：** `VR-DATA-001`

### What to build

结构化 fetch 无 `schema_hash` 不得 SUCCESS；`DbValidationGate` 缺失 current/baseline hash fail-closed；损坏 CSV/Parquet 负向不可 clean-write。

### Acceptance criteria

- [ ] 契约 `data_adapter_contract.md` 有 schema_hash 规则 + schemaless 豁免句
- [ ] adapter infer 有界；gate block 测绿；损坏文件 → FAILED/SCHEMA_DRIFT
- [ ] **禁止** unrelated routing 改动；**禁止** production clean write

### Blocked by

无（**merge 序 4**；与 C03 避免同时改 storage helper 若冲突）

### Vertical slices

| 序  | ID      | 垂直切片        | 交付物                                   | 依赖    | AC            |
| --- | ------- | --------------- | ---------------------------------------- | ------- | ------------- |
| 1   | DATA-01 | 契约规则        | schema_hash + schemaless 豁免            | —       | AC-DATA-01    |
| 2   | DATA-02 | Adapter infer   | CSV/Parquet 有界推导；无 hash 不 SUCCESS | DATA-01 | AC-DATA-02,04 |
| 3   | DATA-03 | Validation gate | 缺失 hash fail-closed                    | DATA-01 | AC-DATA-03,05 |
| 4   | DATA-04 | 负向损坏        | corrupt → 不可写                         | DATA-02 | AC-DATA-04    |

**不在切片内：** B02-DATA-05 registry — 主会话。

---

## 5. B3V-C03 · B3V-STOR — RawStore Atomic Write

**活卡：** [`B02_03_rawstore_atomic_write.md`](B02_03_rawstore_atomic_write.md)  
**Trellis 草案：** `.trellis/tasks/round3v-rawstore-atomic-write/research/vertical-slices.md`  
**Owns：** `VR-STOR-001`

### What to build

同目录 temp + flush/fsync + `os.replace` 原子写；`RawStore.save` 接入；中途失败无半写；同 content_hash 幂等。

### Acceptance criteria

- [ ] `write_bytes_atomic` 单测绿
- [ ] 写中途异常：目标 absent 或 unchanged
- [ ] 重复 save 同 hash 字节/路径一致
- [ ] **禁止**改 content_hash 命名；**禁止** Windows 依赖 POSIX-only directory fsync

### Blocked by

无（**merge 序 5**）

### Vertical slices

| 序  | ID      | 垂直切片         | 交付物                           | 依赖        | 证据                |
| --- | ------- | ---------------- | -------------------------------- | ----------- | ------------------- |
| 1   | STOR-01 | Atomic helper    | `path_compat.write_bytes_atomic` | —           | `9.1-red/green.txt` |
| 2   | STOR-02 | RawStore wiring  | `save` → atomic                  | STOR-01     | `9.2-red/green.txt` |
| 3   | STOR-03 | Crash simulation | 无半写文件                       | STOR-02     | `9.3-red/green.txt` |
| 4   | STOR-04 | Idempotency      | 同 content 重复 save             | STOR-02     | `9.4-red/green.txt` |
| 5   | STOR-05 | VR closeout      | proposed registry delta          | STOR-03..04 | 主会话              |

---

## 6. B3V-C04 · B3V-SYNC — Sync Job Support & Recovery

**活卡：** [`B02_04_sync_job_support_and_recovery.md`](B02_04_sync_job_support_and_recovery.md)  
**Trellis 草案：** `.trellis/tasks/round3v-sync-support-matrix-recovery/research/vertical-slices.md`  
**Owns：** `VR-SYNC-002`, `VR-SYNC-001`

### What to build

`sync_job_contract.yaml` 含 implemented / reserved job types；runtime parity；reserved 稳定 `DeferredJobTypeError`；`VR-SYNC-001` crash-window **路径 A 关账** 或 **路径 B handoff Round 3F.4**。

### Acceptance criteria

- [ ] 契约 == `IMPLEMENTED_JOB_TYPES` == 可调用 `run_*` 集
- [ ] `run_full_load` / `run_data_quality` / `run_revision_audit` deferred 稳定错误元数据
- [ ] SYNC-06 三票：**06A 实现** → **06B 测试** → **06C 关账**（路径 B 时 06A 换 handoff 文档票，06B 可 skip）
- [ ] **禁止** `qmd data` CLI release；**禁止** production clean write

### Blocked by

- **推荐：** B3V-C01 merged（write mode / crash-window 语义）
- Wave 0 内 **merge 序 6**（最后）

### Vertical slices（SYNC-BOOT..05 不变）

| 序  | ID        | 垂直切片            | 交付物                                   | 依赖    | AC           |
| --- | --------- | ------------------- | ---------------------------------------- | ------- | ------------ |
| 0   | SYNC-BOOT | 基线 RED            | parity + deferred 现状                   | —       | AC-SYNC-PLAN |
| 1   | SYNC-01   | Support matrix 契约 | implemented / reserved + deferred 元数据 | BOOT    | AC-SYNC-002  |
| 2   | SYNC-02   | Runtime parity      | 常量 == 契约 == run\_\*                  | SYNC-01 | AC-SYNC-002  |
| 3   | SYNC-03   | Reserved deferred   | 稳定 DeferredJobTypeError                | SYNC-02 | AC-SYNC-002  |
| 4   | SYNC-04   | Registry reconcile  | proposed delta + test purpose 更新       | SYNC-03 | AC-SYNC-REG  |
| 5   | SYNC-05   | Crash-window 审查   | ADR-001 窗口 + hook 点文档               | SYNC-03 | AC-SYNC-001  |

### SYNC-06 拆票（用户 quiz 2026-06-28 · 3 个 GitHub issue）

| Issue | ID           | 标题（建议）                                       | 交付物                                                                                        | 依赖               | 路径 B 替代                                         |
| ----- | ------------ | -------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------- |
| 1     | **SYNC-06A** | `[B3V-SYNC] VR-SYNC-001 最小恢复实现`              | `recover_stuck_writing_job`（或等价）+ SYNC-05 hook 点接线；不改 write_contract/ADR 语义      | SYNC-05            | → `research/sync-001-handoff.md` 草稿（不实现恢复） |
| 2     | **SYNC-06B** | `[B3V-SYNC] crash-window pytest WRITING→COMPLETED` | 注入写提交后/COMPLETED 前失败；断言 WRITING+write_id 可恢复 COMPLETED                         | SYNC-06A           | skip（handoff 票代替关账路径）                      |
| 3     | **SYNC-06C** | `[B3V-SYNC] VR-SYNC-001 关账或 handoff 闭合`       | 路径 A：proposed delta 关 VR-SYNC-001；路径 B：handoff 定稿 + 精确 re-defer + 主会话 registry | SYNC-06B 或 06A(B) | 同左                                                |

#### Issue 骨架 — SYNC-06A（实现）

```markdown
## [B3V-SYNC] VR-SYNC-001 最小恢复实现

**What to build:** 在 `IncrementalJobRunner` crash-window（写提交后、COMPLETED 前）提供最小恢复入口，使 stuck WRITING job 可继续到 COMPLETED。

**Acceptance criteria:**

- [ ] 实现与 SYNC-05 文档化 hook 点一致
- [ ] 不改 `write_contract.yaml` / WriteManager 写模式语义
- [ ] 单元/集成级 smoke 可调用恢复路径（完整 pytest 在 SYNC-06B）

**Blocked by:** SYNC-05

**Out of scope:** 路径 B handoff（若 Plan 门控选 B，本票改为 handoff 文档票）
```

#### Issue 骨架 — SYNC-06B（测试）

```markdown
## [B3V-SYNC] crash-window pytest WRITING→COMPLETED

**What to build:** pytest 注入 crash-window 失败，证明 SYNC-06A 恢复逻辑可让 WRITING+write_id job 到达 COMPLETED。

**Acceptance criteria:**

- [ ] RED→GREEN 证据：`execute-evidence/9.6-red.txt` / `9.6-green.txt`（或等价 Step 编号）
- [ ] 测试文件：`tests/test_sync_orchestrator.py` 或新建 `tests/test_sync_job_contract.py`
- [ ] 五字段 docstring 齐全

**Blocked by:** SYNC-06A（路径 A）

**Out of scope:** registry 闭合（SYNC-06C）
```

#### Issue 骨架 — SYNC-06C（关账）

```markdown
## [B3V-SYNC] VR-SYNC-001 关账或 handoff 闭合

**What to build:** 关闭或精确 defer `VR-SYNC-001`；提交 registry proposed delta 或 `research/sync-001-handoff.md` → Round 3F.4。

**Acceptance criteria:**

- [ ] 路径 A：06B 绿 + proposed delta 完整
- [ ] 路径 B：handoff 含 owner/phase/closure test；本分支不 CLOSED VR-SYNC-001
- [ ] 主会话批 reconcile registry

**Blocked by:** SYNC-06B（路径 A）或 SYNC-06A handoff 票（路径 B）
```

### 测试路径替换（任务卡 vs 仓库）

| 任务卡引用                   | 实际                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| `tests/test_sync_runners.py` | **不存在** → `tests/test_sync_orchestrator.py` + 可选新建 `tests/test_sync_job_contract.py` |

---

## 7. Wave 0 协调 Checklist（主会话）

```text
[ ] Playbook + 本 INDEX 已 commit 到 master
[ ] 六 worktree 已开；每 agent 单一核心文件组（§2.5）
[ ] 每卡 Trellis Plan 冻结：validate-plan-freeze exit 0
[ ] Execute：每切片 RED→GREEN + execute-evidence
[ ] merge 顺序 C05→C06→C01→C02→C03→C04；每步全量 pytest
[ ] registry proposed deltas 批 reconcile（子 agent 禁止直接 CLOSED）
[ ] integration/round3-batch3v → master；Wave 0 Done 记入 R3H_PASS_EXECUTION_PLAN
```

---

## 8. 与 R3H PASS 路径关系

```text
Wave 0（本文 Batch 3V CLOSED）
  → Wave 1 R3H-06 Clean Schema
  → Wave 2 R3H-07 ∥ R3H-10
  → Wave 3 R3H-08A..D Live 产品化
  → Wave 4 R3H-05 审计 → PASS_ROUND4_REAL_DATA_READY
  → Round 4（B04-01 先）
```

**Wave 0 明确不做：** live fetch、production clean write、`web_search` 真 API（见 `R3H_PASS_EXECUTION_PLAN.md` §1.2）。

---

## 9. 下一步（Plan 3.5 冻结前）

| 动作                                                                            | 状态            |
| ------------------------------------------------------------------------------- | --------------- |
| 粒度 quiz：C05 整卡 1 issue；SYNC-06 拆 06A/B/C                                 | **已裁决** §0.2 |
| 同步 Trellis `round3v-sync-support-matrix-recovery/research/vertical-slices.md` | 随 INDEX 更新   |
| C05/C06 建 Trellis 任务 + `vertical-slices.md`                                  | 待主会话        |
| `validate-plan-freeze` per task                                                 | Plan 完成时     |
