# A8 QA / 测试缺口审计 — B3V-STOR

> **角色：** Audit-A8 · `round3v-rawstore-atomic-write`  
> **Worktree：** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-stor`  
> **Owned VR：** `VR-STOR-001`  
> **审计对象：** `tests/test_raw_store.py`（31 项）  
> **权威：** `agents/audit-adversarial-authority.md` → `B02_03_rawstore_atomic_write.md` → `AUDIT.plan.md` §2 A8 → `MASTER.plan.md` §5  
> **Skill：** `testing-guidelines` · `doubt-driven-development`  
> **审计日期：** 2026-06-28

---

## 1. 裁决

| 项 | 结论 |
| --- | --- |
| **A8 总裁决** | **PASS** |
| **§5.3 冻结用例** | 5/5 存在且语义对齐 |
| **AC-STOR-01..04 测试追溯** | 全覆盖（见 §3） |
| **五字段注释** | 31/31 用例齐全 |
| **独立复跑** | `31 passed`（见 §2） |
| **阻断项** | 0 |

---

## 2. 独立复跑证据

| 命令 | 结果 | exit | 备注 |
| --- | --- | --- | --- |
| `uv run pytest tests/test_raw_store.py -q` | **31 passed** | **0** | A5 cli-sandbox 口径 |
| `uv run pytest tests/test_raw_store.py -q --basetemp=.trellis/tasks/round3v-rawstore-atomic-write/.audit-sandbox/pytest` | **31 passed** | **0** | A8 隔离口径；**须先 `mkdir -p` 父目录**（Windows 下 pytest 不自动建 `.audit-sandbox`） |

证据路径：`execute-evidence/full-pytest-2026-06-28.txt`（全库含本模块 31 绿；全库其余失败与 STOR 无关，归 A5 环境门禁）。

---

## 3. AC / 场景追溯矩阵

### 3.1 B3V 切片 AC（MASTER §2 + B02_03 §6）

| AC | 场景 | 主测用例 | 辅助回归 | 裁决 |
| --- | --- | --- | --- | --- |
| AC-STOR-01 | S1 原子 helper | `test_writeBytesAtomic_writesCompleteFile` | `test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent`、`test_writeBytesAtomic_writeFailure_cleansTemp` | PASS |
| AC-STOR-02 | S2 save 接线 | `test_save_writesFileAndComputesHash`、`test_save_pathLayout_matchesConvention` | 入参校验 5 项 + `test_save_csvFileType_writesWithCsvSuffix` | PASS |
| AC-STOR-03 | S3 crash 无半写 | `test_save_midWriteFailure_leavesTargetAbsentOrUnchanged`、`test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes` | `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes`（helper 强证） | PASS |
| AC-STOR-04 | S4 幂等 | `test_save_repeatedSameContent_isIdempotent` | — | PASS |
| AC-STOR-05 | S5 registry closeout | —（YAML 证据，非本文件 pytest） | `research/registry_proposed_delta.yaml` | defer → A5 |

### 3.2 MASTER §5.3 冻结用例对照

| 冻结 `test_*` | 断言语义（冻结） | 实现断言 | 对齐 |
| --- | --- | --- | --- |
| `test_writeBytesAtomic_writesCompleteFile` | 目标存在且字节一致 | `dest.read_bytes() == payload` | ✅ |
| `test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent` | replace 前失败：无目标；temp 清理 | `not dest.exists()` + `glob(".*.tmp.*") == []` | ✅ |
| `test_save_midWriteFailure_leavesTargetAbsentOrUnchanged` | save 中途失败：无半写 | `not dest.exists()` | ✅ |
| `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes` | 已有文件失败：原字节不变 | 同 content 二次 save + `read_bytes() == original` | ✅（repair 后语义正确） |
| `test_save_repeatedSameContent_isIdempotent` | 两次 save 同路径同内容 | `local_path`/`content_hash` 相同 + 字节不变 | ✅ |

### 3.3 Repair 增补用例（§5 未逐条点名但闭合 A4/A8 缺口）

| 用例 | 目的 | AC |
| --- | --- | --- |
| `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes` | helper 层异 content 同路径 replace 失败 | AC-STOR-03 |
| `test_writeBytesAtomic_writeFailure_cleansTemp` | open/write 阶段失败 temp 清理（A8-D01） | AC-STOR-01 |
| `test_save_csvFileType_writesWithCsvSuffix` | csv 后缀 + 原子写接线（A8-D02） | AC-STOR-02 |

---

## 4. Red Flag 追溯（§3.8）

| Red Flag（MASTER §7 / B02_03） | 覆盖方式 | 证据 |
| --- | --- | --- |
| 水平改 gate/sync | 非测试面；切片 diff 未触 gate | A1 scope |
| 无 RED 勾 §9 | Execute `9.1-red.txt`…`9.4-red.txt` 已归档 | execute-evidence |
| 改测试 purpose | 对照 §5.3：名称与断言语义未漂移 | 本审读 31 项 docstring |
| Execute 跑 trellis-check | 归 A1 | — |
| Windows 长路径回归 | `test_save_windowsLongPath_writesSuccessfully`（NT only；`pytest.skip` 非 NT） | PASS |
| 路径穿越 / 沙箱 | `test_save_pathTraversal_raises` 等 3 项 | PASS |
| 半写目标 / temp 残留 | §3.1 S1/S3 用例簇 | PASS |
| 同内容幂等 | `test_save_repeatedSameContent_isIdempotent` | PASS |
| JSON/CSV/Parquet 后缀不变 | json 回归 + csv 专项；parquet 见 §6 计划外 | PARTIAL（parquet defer） |
| staged registry 旁路不得公开 | `test_stagedEvidence_*` 4 项 | PASS（切片外但同文件回归） |

---

## 5. 五字段与 testing-guidelines 合规

| 检查项 | 结果 |
| --- | --- |
| 每用例含 `覆盖范围` / `测试对象` / `目的/目标` / `验证点` / `失败含义` | **31/31** |
| mock 打在 `open` / `write` / `os.replace` 边界 | ✅ crash 类用例符合 MASTER §5.0 |
| 无 tautological 断言（仅 `assert True` 等） | ✅ |
| `tests/test_catalog.yaml` 登记 | ✅ `tests/test_raw_store.py` |
| flaky 风险（未控网络/时序） | ✅ 全本地 `tmp_path` / DuckDB 内存或 sandbox |

**注：** 文件头模块 docstring 仅 3 行（Round 1 遗留），不替代用例五字段；不阻断。

---

## 6. 对抗性深审 — 弱断言与真实性

### 6.1 同路径 replace-fail（首轮 A4 BLOCKING 已修）

| 层 | 用例 | 对抗结论 |
| --- | --- | --- |
| helper | `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes` | **强证据**：预置 `dest`，异 content 写失败，目标字节不变 |
| save | `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes` | **可接受**：hash 命名下「同路径」⇔「同 content」；若实现绕过 `os.replace`，`pytest.raises(OSError)` 会红 |

`RawStore.save` 经 `write_bytes_atomic(dest_path, content)` 接线；replace 前不触碰目标文件。

### 6.2 mock 天花板

| 攻击面 | 严重度 | 说明 |
| --- | --- | --- |
| mock `os.replace` 不代表磁盘满/权限 errno | NON-BLOCKING | 单元级可接受；B02_03 要求 simulate exception |
| 无 parent-dir fsync | NON-BLOCKING | `path_compat.py` ponytail 注释已声明天花板 |
| save 层无法测「异 content 同路径」 | NON-BLOCKING | 生产不可能（`filename = {content_hash}.{ext}`）；helper 层已覆盖 |

---

## 7. 计划外发现

> 对抗性搜索范围：`test_raw_store.py` 全文、`backend/app/storage/{raw_store,path_compat}.py`、B02_03 §6、`MASTER §5.2` 边界表、`specs/contracts/resource_limits.yaml`（大小上限由 `test_save_oversizedContent_raises` 间接覆盖）。

| ID | 严重度 | 发现 | 建议 |
| --- | --- | --- | --- |
| A8-D-STOR-01 | NON-BLOCKING | 无 `file_type=parquet` 原子写 smoke（仅白名单拒绝测提及 parquet） | parquet 落盘增多时补一条与 csv 对称的 smoke |
| A8-D-STOR-02 | NON-BLOCKING | 无显式断言 `save` 必须调用 `write_bytes_atomic`（仅行为+接线推断） | 若未来重构，靠 §5.3 回归集约束；可选 spy 测 defer |
| A8-D-STOR-03 | OPERATIONAL | A8 `--basetemp` 父目录 `.audit-sandbox/` 须预先创建（Windows） | 审计脚本 `New-Item -Force` 或文档一行 |
| A8-D-STOR-04 | NON-BLOCKING | `test_stagedEvidence_noProductionReferenceToRegistryBypass` 为静态 grep，非运行时 | 对 R3Y 旁路封口足够；不改变 purpose |

**显式声明：** 已对抗搜索；上表外未发现 BLOCKING 测试缺口。

---

## 8. 31 项测试清单（分组）

### 8.1 B3V 原子写切片（8 项）

1. `test_writeBytesAtomic_writesCompleteFile`
2. `test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent`
3. `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes`
4. `test_writeBytesAtomic_writeFailure_cleansTemp`
5. `test_save_midWriteFailure_leavesTargetAbsentOrUnchanged`
6. `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes`
7. `test_save_csvFileType_writesWithCsvSuffix`
8. `test_save_repeatedSameContent_isIdempotent`

### 8.2 RawStore 核心回归（9 项）

`test_sha256Hex_*`、`test_save_writes*`、`test_save_pathLayout_*`、`test_save_fileIdFormat_*`、入参校验 5 项

### 8.3 FileRegistry 集成（8 项）

`test_register_*`、`test_exists_*`

### 8.4 Staged evidence 旁路（4 项）

`test_stagedEvidence_*`

### 8.5 平台回归（1 项）

`test_save_windowsLongPath_writesSuccessfully`

### 8.6 模块计数

**合计：31**（与 AUDIT.plan §2 A8「31 tests」一致）

---

## 9. AUDIT.plan §2 A8 勾选

| 检查 | 状态 |
| --- | --- |
| crash/idempotency 五字段齐全 | [x] |
| §5.3 用例绿 | [x] |
| pytest-isolated basetemp 可跑（父目录已建） | [x] |

---

## 10. 结论与交接

- **A8 PASS**：`test_raw_store.py` 31 项满足冻结测试契约；AC-STOR-01..04 可追溯；Red Flags 均有测试或 explicit defer（AC-STOR-05 → registry YAML）。
- **不补测**：计划外 parquet smoke 为 NON-BLOCKING defer，不改变既有 purpose。
- **主会话 A9**：可汇总 A8 PASS；全库 pytest 门禁仍由 A5 单独裁决（与本模块无关的失败不回调 A8）。

---

*审计员：Audit-A8 · B3V-STOR · 2026-06-28*
