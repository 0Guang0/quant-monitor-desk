# MASTER 计划 — B3V-STOR RawStore Atomic Write

> **Execute 入口** — verified-audit cleanup；**不得**声称 production-live。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **必须读原文：** 任务卡 `B02_03_rawstore_atomic_write.md` 及 playbook §3.4

---

## 0. 元信息

| 字段                      | 值                                                               |
| ------------------------- | ---------------------------------------------------------------- |
| 任务 slug                 | `round3v-rawstore-atomic-write`                                  |
| Playbook / Manifest       | `B3V-STOR` / `B3V-C03`                                           |
| 分支                      | `fix/round3v-rawstore-atomic-write`                              |
| Worktree                  | `../quant-monitor-desk-wt-b3v-stor`                              |
| 模型                      | `composer-2.5`                                                   |
| Owned VR                  | `VR-STOR-001`                                                    |
| manifest_protocol_version | `3`                                                              |
| analysis_waiver           | `false`                                                          |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md`   |
| `EVIDENCE_ROOT`           | `.trellis/tasks/round3v-rawstore-atomic-write/execute-evidence/` |

### Batch 3V 边界（Playbook §2.5 / §2.6）

| Owns（可写）                                             | Must not own                                                 |
| -------------------------------------------------------- | ------------------------------------------------------------ |
| `backend/app/storage/raw_store.py`                       | `validation_gate.py`、adapter schema_hash 路径               |
| `backend/app/storage/path_compat.py`                     | `WriteManager` 写模式契约                                    |
| `tests/test_raw_store.py`（原子/crash/idempotency 用例） | `backend/app/sync/**`                                        |
| `research/registry_proposed_delta.yaml`（proposed only） | FileRegistry **语义**变更（除非测试证明必需）                |
|                                                          | registry 三件套 / `UNRESOLVED` / `RESOLVED` 直接 commit      |
|                                                          | production clean write · live fetch · production DB mutation |

### Failure modes / 回滚

| 场景                          | 处理                                      |
| ----------------------------- | ----------------------------------------- |
| 写失败留半拉子目标文件        | 中止；不勾 GREEN；修复原子路径            |
| 误改 FileRegistry 语义        | revert；退回 Plan                         |
| Windows 长路径回归失败        | 中止；检查 `to_extended_path` 与原子 temp |
| production DB 变异            | 中止；`MUTATION_DETECTED`                 |
| GitNexus impact HIGH/CRITICAL | 停；主会话裁定后继续                      |

### 0.1 门控速查

| 项        | 值                                                   |
| --------- | ---------------------------------------------------- |
| 怎么测    | §9 RED→GREEN；`tests/test_raw_store.py`              |
| 怎么验收  | playbook §8.3 + §10                                  |
| 什么叫过  | §2 AC-STOR-\* 全部 + `VR-STOR-001` proposed closeout |
| prod-path | Tier B：`uv run pytest -q`                           |
| 6.pre     | `research/gitnexus-summary.md`（impact MEDIUM）      |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。  
标记 **必须读原文** 的任务卡不得仅用摘要替代。

### 0.3a Ponytail

Boot 起 Read `.cursor/rules/ponytail.mdc`；在 `path_compat` 一处实现原子写；`RawStore.save` 最小一行替换；无新依赖。

### 0.3b 测试纪律

五字段 docstring（playbook §2.2.1）；TDD RED→GREEN；每步 GREEN 后 `incremental-implementation` + 全量 pytest；**禁止弱化测试目的**。

### 0.4 上下文打包（v3）

Execute 以 MASTER + ledger + implement.jsonl 为准。

### Source Context Index（Playbook §3.1 + §3.4）

#### §3.1 共用底座

| 路径                                                              | 遵守什么              | 摘要                 | implement |
| ----------------------------------------------------------------- | --------------------- | -------------------- | --------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                | §2.5–§2.7 · §4 · §8.3 | 文件锁；正式线流水线 | [x]       |
| `BATCH_3V_TASK_CARD_MANIFEST.md`                                  | C03 路由              | B3V-C03 分支         | [x]       |
| `BATCH_3V_HARDENING_RULES.md`                                     | §1–§7                 | 禁 production 措辞   | [x]       |
| `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`                       | Batch 入口            | Round 3V 目标        | [x]       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                               | Round 3V              | `R3V-B02-STOR-01`    | [x]       |
| `complex-task-planning-protocol.md` Phase 8D                      | debt-lite 对照        | 本任务 complex       | [x]       |
| `agent-toolchain.md`                                              | 工具路由              | GitNexus 同级        | [x]       |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR 路由               | `VR-STOR-001`        | [x]       |
| `BATCH_3V_ADVERSARIAL_AUDIT.md`                                   | 对抗性                | Batch 纪律           | [x]       |
| `BATCH_3V_SELF_CHECK.md`                                          | 派发门禁              | PASS_FOR_DISPATCH    | [x]       |
| `ROUND3_HANDOFF.md`                                               | handoff               | post Batch 01        | [x]       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×4                                 | 全局                  | 执行/测试/资源/模板  | [x]       |
| `MIGRATION_MAP.md`                                                | 架构                  | storage 放置         | [x]       |
| `specs/context/authority_graph.yaml`                              | 模块图                | storage 域           | [x]       |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md`              | **只读**              | 主会话闭合           | [x]       |

#### §3.4 B3V-STOR 分支必读

| 路径                                             | 遵守什么  | 摘要                   | implement |
| ------------------------------------------------ | --------- | ---------------------- | --------- |
| `B02_03_rawstore_atomic_write.md`                | 任务卡 AC | 原子写五切片           | [x]       |
| `backend/app/storage/raw_store.py`               | **独占**  | `save` 写路径          | [x]       |
| `backend/app/storage/path_compat.py`             | 路径 I/O  | `write_bytes` → atomic | [x]       |
| `specs/contracts/snapshot_lineage_contract.yaml` | 证据链    | 只读对照               | [x]       |
| `specs/contracts/resource_limits.yaml`           | 资源上限  | `MAX_RAW` 邻接         | [x]       |
| `tests/test_raw_store.py`                        | 测试基线  | 扩展 crash 测          | [x]       |
| `research/gitnexus-summary.md`                   | impact    | MEDIUM · 18 节点       | [x]       |

---

## 1. 目标与目的

### 1.1 目标

为 RawStore 支持的原始证据文件（json/csv/parquet）实现原子写：同目录临时文件 → flush/fsync（平台支持）→ `os.replace`；失败不留半写目标；同内容重复保存幂等。

### 1.2 目的

关闭审计项 `VR-STOR-001`，保障证据链在进程崩溃或 I/O 异常时不会引用截断文件。

### 1.3 前置

post Batch 01 `master`；worktree `fix/round3v-rawstore-atomic-write`。

### 1.4 约束

- Batch 3V hardening：无 production clean write / 无 live fetch / 无 production DB 写
- 不改 `content_hash` 命名与路径布局
- Windows 不得依赖 POSIX-only 目录 fsync

### 1.5 停止条件

| #   | 事件                                    | 处理                         |
| --- | --------------------------------------- | ---------------------------- |
| 1   | 触及 forbidden 文件组（§2.6）           | 立即停止 Execute             |
| 2   | production DB 写入检测到                | 中止；不勾 GREEN             |
| 3   | scope 偏离 B02_03（改 sync/gate 等）    | 退回 Plan                    |
| 4   | RED 异常（非本步预期失败）              | 停当前 §9 步                 |
| 5   | GitNexus `impact` 升至 HIGH/CRITICAL    | 停；主会话书面批准后继续     |
| 6   | **本任务特有：** crash 测试仍见截断目标 | 禁止勾 STOR-03 GREEN；修实现 |

### 1.6 原计划归并

| 来源          | 内容                                        |
| ------------- | ------------------------------------------- |
| `B02_03_*.md` | 五切片 · 验收命令 · forbidden               |
| playbook §3.4 | 必读路径表                                  |
| playbook §8.3 | PASS 维度：原子性 + VR 关闭                 |
| 纠偏          | registry 仅 proposed delta（主会话 commit） |

---

## 2. 架构与设计

### 2.1 架构

```
RawStore.save → mkdir_parents → write_bytes_atomic(dest, content)
write_bytes_atomic:
  1. temp = dest_dir / f".{dest.name}.tmp.{pid}.{token}"
  2. write temp via to_extended_path; flush+fsync
  3. os.replace(temp, dest)
  4. on error: unlink temp (ignore missing); re-raise; dest untouched
```

### 2.2 设计规则

- 临时文件与目标**同目录**（`os.replace` 同卷要求）
- 复用 `to_extended_path` 处理 Windows MAX_PATH
- **不**对目录做 POSIX-only `fsync` 作为 Windows 正确性前提
- 保留 `write_bytes` 供非本任务路径；仅 `RawStore.save` 切换原子写

### 2.3 规则

GLOBAL + Batch 3V hardening + playbook §2.2 TDD/ponytail

### 2.4 契约

- `specs/contracts/resource_limits.yaml` — 邻接（`MAX_RAW_FILE_BYTES` 已在 `raw_store.py`）
- `specs/contracts/snapshot_lineage_contract.yaml` — 证据链只读

### 2.5 AC 表

| AC ID      | 描述                                       | 场景 |
| ---------- | ------------------------------------------ | ---- |
| AC-STOR-01 | `write_bytes_atomic` 存在且单测覆盖        | S1   |
| AC-STOR-02 | `RawStore.save` 使用原子写；类型白名单不变 | S2   |
| AC-STOR-03 | 写中途失败：目标 absent 或字节不变         | S3   |
| AC-STOR-04 | 同内容重复 save 幂等                       | S4   |
| AC-STOR-05 | `VR-STOR-001` proposed registry closeout   | S5   |

---

## 3. 需求与场景矩阵

| 场景# | Given            | When                               | Then                           | AC         | 测试（§5.2） | 验证 Tier |
| ----- | ---------------- | ---------------------------------- | ------------------------------ | ---------- | ------------ | --------- |
| S1    | 空目录           | 调 `write_bytes_atomic` 写完整字节 | 目标文件存在且等于输入         | AC-STOR-01 | helper 成功  | Tier A    |
| S2    | 合法 save 参数   | `RawStore.save`                    | 路径布局与 hash 不变；文件完整 | AC-STOR-02 | save 回归    | Tier A    |
| S3    | 无目标或已有目标 | 写中途抛异常                       | 目标不存在或内容等于写前       | AC-STOR-03 | crash 失败   | Tier A    |
| S4    | 已成功 save 一次 | 同 content 再 save                 | 同路径同字节；无损坏           | AC-STOR-04 | 幂等         | Tier A    |
| S5    | STOR-01..04 绿   | 产出 registry delta                | YAML 含 VR-STOR-001 闭合字段   | AC-STOR-05 | closeout     | Tier A    |

**3.1 需求说明：** 原子写 raw/json/csv/parquet 证据；不改 hash 命名；不改 FileRegistry API。  
**3.2 范围：** in `raw_store.py` · `path_compat.py` · `test_raw_store.py` · out/defer validation_gate、sync、write 模式、Layer5、registry commit。

---

## 4. 预期结果

| #          | 预期结果                        | 验证链         |
| ---------- | ------------------------------- | -------------- |
| AC-STOR-01 | 原子 helper 可测                | S1 → §9.1 → §6 |
| AC-STOR-02 | save 走原子写且无布局回归       | S2 → §9.2 → §6 |
| AC-STOR-03 | crash 无半写目标                | S3 → §9.3 → §6 |
| AC-STOR-04 | 幂等 save                       | S4 → §9.4 → §6 |
| AC-STOR-05 | `VR-STOR-001` proposed 闭合证据 | S5 → §9.5 → §6 |

---

## 5. 测试契约

> purpose **冻结**；改 purpose 须回 Plan。

### 5.0 规范

1. 五字段：`覆盖范围` / `测试对象` / `目的/目标` / `验证点` / `失败含义`
2. mock 仅打在 `open`/`write`/`os.replace` 边界；不得 mock 掉被测断言
3. RED 必须先 FAIL（helper 不存在或行为未实现）

### 5.1 测试文件路径

| 路径                      | 目标文件                             | 测试目的（冻结）                             | §9 步 |
| ------------------------- | ------------------------------------ | -------------------------------------------- | ----- |
| `tests/test_raw_store.py` | `backend/app/storage/path_compat.py` | 验证 `write_bytes_atomic` 完整写与 temp 清理 | 9.1   |
| `tests/test_raw_store.py` | `backend/app/storage/raw_store.py`   | 验证 `save` 仍正确落盘且走原子路径           | 9.2   |
| `tests/test_raw_store.py` | `backend/app/storage/raw_store.py`   | 验证写失败不损坏/不创建半写目标              | 9.3   |
| `tests/test_raw_store.py` | `backend/app/storage/raw_store.py`   | 验证同内容重复 save 幂等                     | 9.4   |

### 5.2 成功/失败语义

| 能力        | 成功怎么测                                     | 失败怎么测                                       | 场景 | 边界                              |
| ----------- | ---------------------------------------------- | ------------------------------------------------ | ---- | --------------------------------- |
| 原子 helper | 写后目标字节等于输入；无残留 `.tmp.`           | patch `os.replace` 抛错：目标不存在；temp 已清理 | S1   | 同目录 temp                       |
| save 接线   | 既有 `test_save_*` 全绿                        | 若仍直写目标：新测 FAIL                          | S2   | json/csv/parquet                  |
| crash 窗口  | 中途异常：目标 absent 或 `read_bytes` 等于写前 | 目标存在且字节变短/变了 → FAIL                   | S3   | mock `Path.write_bytes` 或 `open` |
| 幂等        | 两次 save 同 path、同 hash、同 bytes           | 第二次改变内容或抛错 → FAIL                      | S4   | 不经过 FileRegistry               |

### 5.3 用例设计

| 测试文件                  | `test_*` 名称                                                          | 断言语义                          | 场景 | RED 命令                                                                                                         | GREEN 命令 |
| ------------------------- | ---------------------------------------------------------------------- | --------------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------- | ---------- |
| `tests/test_raw_store.py` | `test_writeBytesAtomic_writesCompleteFile`                             | 目标存在且字节一致                | S1   | `uv run pytest tests/test_raw_store.py::test_writeBytesAtomic_writesCompleteFile -v`                             | 同上       |
| `tests/test_raw_store.py` | `test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent` | replace 前失败：无目标；temp 清理 | S1   | `uv run pytest tests/test_raw_store.py::test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent -v` | 同上       |
| `tests/test_raw_store.py` | `test_save_midWriteFailure_leavesTargetAbsentOrUnchanged`              | save 中途失败：无半写             | S3   | `uv run pytest tests/test_raw_store.py::test_save_midWriteFailure_leavesTargetAbsentOrUnchanged -v`              | 同上       |
| `tests/test_raw_store.py` | `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes`    | 已有文件时失败：原字节不变        | S3   | `uv run pytest tests/test_raw_store.py::test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes -v`    | 同上       |
| `tests/test_raw_store.py` | `test_save_repeatedSameContent_isIdempotent`                           | 两次 save 同路径同内容            | S4   | `uv run pytest tests/test_raw_store.py::test_save_repeatedSameContent_isIdempotent -v`                           | 同上       |

### 5.4 四层测试

| 层   | 环境      | 命令                                       | 通过   | 证据             |
| ---- | --------- | ------------------------------------------ | ------ | ---------------- |
| 单元 | local/ci  | `uv run pytest tests/test_raw_store.py -q` | exit 0 | execute-evidence |
| 集成 | local/ci  | 同上（含 FileRegistry 既有测）             | exit 0 | —                |
| 管道 | prod-path | `uv run pytest -q`                         | exit 0 | §10              |
| E2E  | —         | **不测**                                   | SKIP   | —                |

---

## 6. 验证

| Tier | 环境      | 命令                                                            | 场景       | 通过条件 | 勾  |
| ---- | --------- | --------------------------------------------------------------- | ---------- | -------- | --- |
| A    | local/ci  | `uv run pytest tests/test_raw_store.py -q`                      | S1–S4      | exit 0   | [x] |
| B    | prod-path | `uv run pytest -q`                                              | S2–S4 回归 | exit 0   | [ ] |
| C    | prod-path | `uv run ruff check backend/app/storage tests/test_raw_store.py` | —          | exit 0   | [ ] |

**6.1 交接门槛：** §9 证据齐 · §5.1 用例已建 · S1–S4 有对应用例 · §5.4+§6 B/C 已跑 · §1.5 未触发

---

## 7. Red Flags

| 风险                     | 预防                                                |
| ------------------------ | --------------------------------------------------- |
| 水平改 gate/sync         | §2.6 + §1.5 #3                                      |
| 无 RED 勾 §9             | 每步 RED 须 FAIL                                    |
| 改测试 purpose           | 只许 §5.3 名称与断言语义                            |
| Execute 跑 trellis-check | → Audit A1                                          |
| Windows 长路径回归       | 保留 `test_save_windowsLongPath_writesSuccessfully` |

---

## 8. 实现顺序（垂直切片）

| 序  | ID      | 交付物（完标准）                               | 依赖        | AC         |
| --- | ------- | ---------------------------------------------- | ----------- | ---------- |
| 1   | STOR-01 | `write_bytes_atomic` + helper 单测绿           | —           | AC-STOR-01 |
| 2   | STOR-02 | `RawStore.save` 改调 atomic；既有 save 测绿    | STOR-01     | AC-STOR-02 |
| 3   | STOR-03 | crash 模拟测绿；无半写目标                     | STOR-02     | AC-STOR-03 |
| 4   | STOR-04 | 幂等测绿                                       | STOR-02     | AC-STOR-04 |
| 5   | STOR-05 | `registry_proposed_delta.yaml` + closeout 说明 | STOR-03..04 | AC-STOR-05 |

---

## 9. 实现步骤（RED/GREEN）

### 9.0 Boot

> **必读：** §0.3 Execute 强制必读 — 逐行 Read `implement.jsonl`；Boot 前先读 `research/integration-ledger.md`（v3 routing）。

| RED 命令                                   | GREEN 命令 | 证据                            | 绑定 Execute Skill                | 已执行 |
| ------------------------------------------ | ---------- | ------------------------------- | --------------------------------- | ------ |
| `uv run pytest tests/test_raw_store.py -q` | 同上       | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [x]    |

### 9.1 STOR-01 — Atomic helper

| 字段               | 内容                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------ |
| 切片               | STOR-01（§8 序 1）                                                                   |
| RED 命令           | `uv run pytest tests/test_raw_store.py::test_writeBytesAtomic_writesCompleteFile -v` |
| GREEN 命令         | 同上                                                                                 |
| 证据               | `9.1-red.txt` / `9.1-green.txt`                                                      |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines                   |
| 通过               | RED FAIL；GREEN 0；§5.2 S1                                                           |
| 已执行             | [x]                                                                                  |

### 9.2 STOR-02 — RawStore wiring

| 字段               | 内容                                                                           |
| ------------------ | ------------------------------------------------------------------------------ |
| 切片               | STOR-02                                                                        |
| RED 命令           | `uv run pytest tests/test_raw_store.py -k "save_writes or save_pathLayout" -q` |
| GREEN 命令         | 同上                                                                           |
| 证据               | `9.2-red.txt` / `9.2-green.txt`                                                |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                           |
| 通过               | §5.2 S2                                                                        |
| 已执行             | [x]                                                                            |

### 9.3 STOR-03 — Crash simulation

| 字段               | 内容                                                            |
| ------------------ | --------------------------------------------------------------- |
| 切片               | STOR-03                                                         |
| RED 命令           | `uv run pytest tests/test_raw_store.py -k "midWriteFailure" -q` |
| GREEN 命令         | 同上                                                            |
| 证据               | `9.3-red.txt` / `9.3-green.txt`                                 |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines                   |
| 通过               | §5.2 S3                                                         |
| 已执行             | [x]                                                             |

### 9.4 STOR-04 — Idempotency

| 字段               | 内容                                                                                   |
| ------------------ | -------------------------------------------------------------------------------------- |
| 切片               | STOR-04                                                                                |
| RED 命令           | `uv run pytest tests/test_raw_store.py::test_save_repeatedSameContent_isIdempotent -v` |
| GREEN 命令         | 同上                                                                                   |
| 证据               | `9.4-red.txt` / `9.4-green.txt`                                                        |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                                   |
| 通过               | §5.2 S4                                                                                |
| 已执行             | [x]                                                                                    |

### 9.5 STOR-05 — VR-STOR-001 closeout

| 字段               | 内容                                                                                                                               |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| 切片               | STOR-05                                                                                                                            |
| RED 命令           | `test -f .trellis/tasks/round3v-rawstore-atomic-write/research/registry_proposed_delta.yaml`（Windows: `if not exist ... exit 1`） |
| GREEN 命令         | 同上 exit 0                                                                                                                        |
| 证据               | `registry_proposed_delta.yaml`                                                                                                     |
| 绑定 Execute Skill | incremental-implementation                                                                                                         |
| 通过               | YAML 含 `VR-STOR-001` resolution 字段                                                                                              |
| 已执行             | [x]                                                                                                                                |

---

## 10. 验收命令（Playbook §8.3）

```bash
uv sync --locked
uv run pytest tests/test_raw_store.py -q
uv run ruff check backend/app/storage tests/test_raw_store.py
uv run pytest -q && uv run ruff check .
```

---

## 11. Execute Skill 冻结

| Skill                      | 绑定                | 已读 |
| -------------------------- | ------------------- | ---- |
| trellis-execute            | Boot                | [ ]  |
| test-driven-development    | §9 RED              | [ ]  |
| incremental-implementation | §9 SLICE            | [ ]  |
| karpathy-guidelines        | GREEN               | [ ]  |
| testing-guidelines         | 写测                | [ ]  |
| gitnexus-impact            | 改 symbol           | [ ]  |
| trellis-check              | **不用** → Audit A1 | —    |

---

## 12. Plan 质检 §3.10（Agent-2）

| 路径                                             | 已入 MASTER/implement | 摘要                                 | 遗漏风险 |
| ------------------------------------------------ | --------------------- | ------------------------------------ | -------- |
| Playbook §3.1 共用底座                           | [x]                   | Source Context Index §3.1 表         | 无       |
| Playbook §3.4 B3V-STOR                           | [x]                   | raw_store/path_compat/tests/VR index | 无       |
| `B02_03_rawstore_atomic_write.md`                | [x]                   | 五切片 AC                            | 无       |
| `BATCH_3V_HARDENING_RULES.md`                    | [x]                   | §1.5 停止条件                        | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.5/§2.6     | [x]                   | Boundary 表                          | 无       |
| `specs/contracts/snapshot_lineage_contract.yaml` | [x]                   | 只读对照                             | 无       |
| `specs/contracts/resource_limits.yaml`           | [x]                   | MAX_RAW 邻接                         | 无       |
| `research/gitnexus-summary.md`                   | [x]                   | impact MEDIUM                        | 无       |
| `validate-plan-freeze`                           | [x]                   | 2026-06-25 exit 0                    | 无       |
| authority_graph storage 域                       | [x]                   | project-overview                     | 无       |

**Agent-2 复检（2026-06-28）：** Plan质检确认 §3.10 零遗留；见 `research/plan-qc-report.md` §13 对抗性审 PASS。

---

## 13. Execute 交接 DoD

- [ ] §9 证据齐 · Boot 产物齐 · §5.4+§6 证据 · §11 Skill 必做 `[x]` · `validate-execute-handoff` 0 · 未 finish-work
