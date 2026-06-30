# B3V-STOR 对抗性审计报告（Post Repair f3281ad）

> **Worktree:** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-stor`  
> **Branch:** `fix/round3v-rawstore-atomic-write`  
> **Repair commit:** `f3281ad380df4ff1ecdd76286d1c5a2faa08d23b`  
> **审计日期:** 2026-06-25  
> **权威层级:** `agents/audit-adversarial-authority.md` → B02_03 任务卡 → A1–A8 报告 → `zero-open-signoff.md`

---

## 1. 执行摘要

| 维度                           | 裁决                                                               |
| ------------------------------ | ------------------------------------------------------------------ |
| **切片 AC（B02_03 §5–§8）**    | **PASS**                                                           |
| **Zero-Open Repair 闭合**      | **PASS**（repair scope 0 OPEN）                                    |
| **同路径 replace-fail 真实性** | **PASS**（helper 层强验 + save 层语义耦合可接受）                  |
| **VR-STOR-001**                | **PROPOSED**（coordinator merge 待办，未直接改 registry 三件套）   |
| **全库 pytest 门禁**           | **NON-BLOCKING 环境红**（44 失败均为 ResourceGuard，与 STOR 无关） |
| **对抗性总裁决**               | **PASS_WITH_ENV_CAVEAT**                                           |

---

## 2. 复跑验证（本审计员独立执行）

| 命令                                                            | 结果                   | exit  |
| --------------------------------------------------------------- | ---------------------- | ----- |
| `uv run pytest tests/test_raw_store.py -q`                      | **31 passed**          | **0** |
| `uv run ruff check backend/app/storage tests/test_raw_store.py` | All checks passed      | **0** |
| `uv run pytest -q`                                              | **44 failed**（见 §5） | **1** |

证据：本报告生成时于 worktree 根目录复跑；`repair-evidence/repair-verification.txt` 记录 repair 当日切片绿。

---

## 3. 同路径 replace-fail — 对抗性深审

### 3.1 首轮 A4 BLOCKING 根因（已修）

首轮 `audit-a4-report.md` 指出：`test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes` 用**不同 content** 触发写失败，因 content_hash 命名导致落盘路径不同，**从未测到「同路径 replace 失败」**。

Repair `f3281ad` 新增/修正两条用例：

| 用例                                                                            | 层                   | 对抗动作                                                                                          |
| ------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------- |
| `test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes` | `path_compat` helper | 预置 `dest` 为 `b'{"v":1}'`，尝试写 `b'{"v":2}'`，mock `os.replace` 抛错，断言 dest 仍为 original |
| `test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes`             | `RawStore.save`      | **同 content** 二次 save，第二次 mock `os.replace` 抛错，断言 `dest.read_bytes() == original`     |

### 3.2 实现路径核对

```49:71:backend/app/storage/path_compat.py
def write_bytes_atomic(path: Path, data: bytes) -> None:
    ...
    try:
        with open(extended_temp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(extended_temp), str(extended_dest))
    except BaseException:
        try:
            extended_temp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
```

`RawStore.save` 经 `write_bytes_atomic(dest_path, content)` 接线（`raw_store.py:74`），**replace 前不触碰目标文件**——mock replace 失败时目标应保持原字节。

### 3.3 对抗性追问：测的是真场景吗？

| 攻击面                                           | 结论                                                                                                                                                             | 严重度                   |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| mock `os.replace` 能否代表真实 OS 失败？         | 单元级可接受；未覆盖权限/磁盘满等真实 errno，属 ponytail 天花板                                                                                                  | NON-BLOCKING             |
| save 层同 content 二次 save 是否过弱？           | **语义耦合**：hash 路径下「同路径」⇔「同 content」，若 replace 未被调用则第二次 save 会**成功**而非抛 `OSError`，`pytest.raises` 会红；故仍约束 replace 在路径上 | NON-BLOCKING             |
| 同 content 能否掩盖 replace 前直写 dest 的损坏？ | 理论上若实现先截断 dest 再 replace，同 content 断言仍绿；**helper 层异 content 用例已堵住该洞**                                                                  | NON-BLOCKING（双层覆盖） |
| 不同 content 同路径在生产是否可能？              | **不可能**（`filename = f"{content_hash}.{ext}"`）；helper 异 content 测的是 helper 契约，非 save 真实路径组合                                                   | 已声明，可接受           |

**裁决：** 同路径 replace-fail **已真实验证**——helper 层为强证据，save 层为接线 + replace-on-path 约束；符合 B02_03 AC-STOR-03 与 A4 修复意图。

### 3.4 计划外发现

| ID          | 严重度       | 发现                                                              | 建议                                         |
| ----------- | ------------ | ----------------------------------------------------------------- | -------------------------------------------- |
| ADV-STOR-01 | NON-BLOCKING | 无 parquet 原子写失败路径专项测（仅 json/csv 覆盖）               | 若后续 parquet 落盘增多，补一条 smoke        |
| ADV-STOR-02 | NON-BLOCKING | `write_bytes_atomic` 无 parent-dir fsync（ponytail 已注释天花板） | 维持 repair `perf-tradeoff-note.md` 触发条件 |
| ADV-STOR-03 | NON-BLOCKING | 全量 pytest 长跑触发 host ResourceGuard HARD_STOP                 | CI/normal profile 下复验；非 STOR 回归       |

---

## 4. A1–A8 对抗性复验矩阵

| 维            | 首轮         | Post-Repair              | 对抗备注                                                                     |
| ------------- | ------------ | ------------------------ | ---------------------------------------------------------------------------- |
| A1 Spec       | PASS         | **PASS**                 | B02_03 scope 无 gate/sync/DB 越界；`content_hash` 命名未改                   |
| A2 Ponytail   | PASS         | **PASS**                 | 单行 `import raw_store`；ponytail 天花板注释在 `path_compat.py`              |
| A3 Security   | PASS         | **PASS**                 | docstring 路径 containment 由 caller 负责；既有 `pathTraversal` 测仍绿       |
| A4 Quality    | **BLOCKING** | **PASS**                 | 同路径 replace-fail 两条用例已对齐 A4 要求                                   |
| A5 Completion | **BLOCKING** | **PASS_WITH_ENV_CAVEAT** | 切片 pytest 绿；全量 pytest exit 1 为 ResourceGuard（§5），非 loop/docs 回归 |
| A6 Perf       | SKIP         | **SKIP**                 | `perf-tradeoff-note.md` 已闭合                                               |
| A7 Ops        | PASS         | **PASS**                 | `orphan-tmp-runbook.md` 已闭合                                               |
| A8 Test gap   | PASS         | **PASS**                 | A8-D01/D02 用例在 `test_raw_store.py`；五字段注释齐全                        |

---

## 5. 全库 pytest 门禁（A5 prod-path）

### 5.1 结果

```
uv run pytest -q  →  exit 1
44 FAILED（无 test_raw_store / path_compat / storage 相关项）
```

### 5.2 失败聚类

全部 44 项失败堆栈指向：

```
ResourceGuardBlockedError: resource guard blocked: HARD_STOP
reason=system memory usage above threshold
available_memory_gb=2.72
profile=eco
```

涉及模块：`layer1_interpretation`、`layer1_observation_ingestion`、`layer2_sensor_loader`、`batch275_live_pilot_gate`、`r3x_*` 等——**与 B3V-STOR diff 无交集**。

### 5.3 对抗性裁决

| 问题                                            | 裁决                                                                                                                                                        |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 首轮 A5 BLOCKING（loop/docs index）是否仍成立？ | **否** — `f3281ad` 已含 `loop_maintain`/`test_catalog` 修复；当前红因不同                                                                                   |
| STOR 切片能否单独合并？                         | **是** — 任务卡 §7 AC 命令全绿                                                                                                                              |
| 合并前是否须全绿 pytest？                       | **Coordinator 策略** — BATCH_3V playbook §8.3 Tier A 理想全绿；本 host eco+内存压测为 **环境 NON-BLOCKING**，须在 CI/normal profile 或 coordinator 门禁复验 |

---

## 6. VR-STOR-001（proposed）

`repair-evidence/registry_proposed_delta.yaml`：

| 字段               | 值                                                                             |
| ------------------ | ------------------------------------------------------------------------------ |
| decision           | `RESOLVED_EXECUTE`                                                             |
| commit_policy      | `proposed_only_no_direct_registry_commit`                                      |
| coordinator_status | `COORDINATOR-QUEUED`                                                           |
| evidence           | `path_compat.py`、`raw_store.py`、`test_raw_store.py`、execute/repair-evidence |

**对抗性检查：**

- ✅ 未违反 hardening「agent 不得直接 commit registry 三件套」
- ✅ rationale 与实现一致（same-dir temp → flush/fsync → `os.replace` → fail cleanup）
- ⚠️ **合并 coordinator 前**须：adversarial PASS 签收 + registry delta 正式 apply

---

## 7. Zero-Open Signoff 对照

`repair-evidence/zero-open-signoff.md` 声明 **0 OPEN (repair scope)**。

本审计独立确认：

| ID                        | 签收                          |
| ------------------------- | ----------------------------- |
| A4-BLOCK-01 / A4-BLOCK-02 | ✅ 用例逻辑与 §3 一致         |
| A1-NB-01 .. A8-D02        | ✅ 证据路径存在且与 diff 对齐 |
| VR-STOR-001               | ✅ proposed，待 coordinator   |

---

## 8. 最终裁决

### PASS_WITH_ENV_CAVEAT

**理由：**

1. Repair `f3281ad` 已闭合首轮 A4 BLOCKING；同路径 replace-fail 在 helper 层有强验证，save 层在 hash 命名模型下语义正确。
2. 任务卡 AC 命令（切片 pytest + ruff）**exit 0**。
3. VR-STOR-001 以 proposed delta 形式排队，符合 BATCH_3V hardening。
4. 全库 pytest **exit 1** 为 host ResourceGuard 环境红，**非 STOR 回归**；建议在 CI/coordinator 合并门前再跑一轮 `uv run pytest -q` 作最终门禁。

### Coordinator 下一步

1. 签收本报告 → 应用 `registry_proposed_delta.yaml` 中 VR-STOR-001。
2. 在 normal/batch profile 或 CI 复跑 `uv run pytest -q` 确认全绿。
3. 合并 `fix/round3v-rawstore-atomic-write` → 协调分支。

---

## 9. 计划外发现（显式声明）

已对抗搜索：storage 写路径、FileRegistry 旁路、Windows 长路径、temp 孤儿、parquet 缺口、全量 pytest 失败聚类。

上表 §3.4 ADV-STOR-01..03 为本轮全部计划外项；**无 BLOCKING 开放项**（repair scope）。
