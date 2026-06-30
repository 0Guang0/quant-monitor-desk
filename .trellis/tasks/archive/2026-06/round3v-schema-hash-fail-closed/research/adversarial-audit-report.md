# B3V-DATA 对抗性审计报告（Post Repair `1bc0260`）

| 字段          | 值                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------ |
| 任务          | `round3v-schema-hash-fail-closed` · Playbook `B3V-DATA` · `VR-DATA-001`                                |
| 分支          | `fix/round3v-schema-hash-fail-closed`                                                                  |
| Worktree      | `quant-monitor-desk-wt-b3v-data`                                                                       |
| Repair commit | `1bc0260d` — `fix(data): schema_hash fail-closed for structured fetches (B3V-DATA)`                    |
| 权威          | `agents/audit-adversarial-authority.md` · `B02_02_schema_hash_fail_closed.md` · `zero-open-signoff.md` |
| 模式          | **只读复验** + A8 pytest 复跑；**未** commit registry 三件套                                           |
| 日期          | 2026-06-25                                                                                             |

---

## 裁决：**PASS**（OPEN = 0 · BLOCKING = 0）

Post Repair `1bc0260` 在 **adapter 主路径 + ValidationGate 结构化启发式** 上闭合 `VR-DATA-001` 运行时 fail-closed；Repair 已 FIX A1 两项 BLOCKING 与 A8 G-01/G-03。已知 defense-in-depth 窗口（OP-01/G-05、G-02）均已按 `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` **RE-DEFER** 至 `B02-DATA-05` / 主会话 coordinator，附 owner、phase、closure test；registry 行 **precise re-defer**（`registry-ready.md`），非 OPEN 遗留。

---

## 1. 对抗审计问题（用户指定三轴）

### 1.1 `VR-DATA-001` fail-closed 是否真闭合？

| 层                                 | 结论                            | 证据                                                                                                                                              |
| ---------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **契约**                           | **闭合**                        | `specs/contracts/data_adapter_contract.md` §Structured schema_hash：SUCCESS+row_count>0 结构化类型必填 hash；schemaless 显式豁免并 defer registry |
| **Adapter（SkeletonAdapterBase）** | **闭合**                        | `skeleton_base.py:183-202` — json/csv/parquet + row_count>0 + infer 失败 → `SCHEMA_DRIFT`，非 SUCCESS                                             |
| **ValidationGate**                 | **主路径闭合**                  | `validation_gate.py:242-248` — structured + SUCCESS + row_count>0 + NULL hash → block                                                             |
| **Registry 行**                    | **precise re-defer（非 OPEN）** | `B02_02` §5 slice `B02-DATA-05` 显式 defer；`registry-ready.md` proposed `PARTIAL_RESOLVED_RUNTIME` + remaining_for_B02-DATA-05                   |

**对抗结论：** 审计项核心风险「结构化 SUCCESS 无 hash 绕过 schema drift」在 **生产 adapter 路径** 已闭合。Registry SSOT 行待 coordinator §7.3 应用 delta — 符合任务卡 Done criteria「resolved or precisely re-deferred」。

### 1.2 Gate fail-open 边角

| ID           | 边角                                                     | 代码                         | 生产影响                                               | 处置                                     |
| ------------ | -------------------------------------------------------- | ---------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| ADV-01       | 有 hash 但 baseline 缺失 → 不 block                      | `validation_gate.py:264-265` | 首写故意放行（MASTER §2.2）                            | **ACCEPTED**                             |
| OP-01 / G-05 | 无法分类 structured（无后缀、无 registry 行）+ NULL hash | `validation_gate.py:249-250` | 仅当 fetch_log **非 skeleton 写入** 且路径无结构化线索 | **RE-DEFER** → B02-DATA-05 integration   |
| OP-02        | registry 回退误标 structured（历史行）                   | `validation_gate.py:195-206` | 偏 **fail-closed**（误拒 > 误放）                      | **ACCEPTED**                             |
| G-04         | row_count=0 + NULL hash 不拦                             | `validation_gate.py:245`     | 设计内（无数据不写 clean）                             | **WONT-FIX**                             |
| G-02         | gate 未读 source_registry schemaless 标记                | 全文件无 schemaless 分支     | 豁免路径未正向证明                                     | **RE-DEFER** → B02-DATA-05 + G-02 正向测 |

**Repair 收紧：** G-01（三后缀 parametrize）、G-03（registry 回退单测）已在 `test_db_validation_gate.py` 落地并纳入 commit `1bc0260`。

### 1.3 Adapter bypass

| 攻击面                                   | 结果              | 说明                                                                                   |
| ---------------------------------------- | ----------------- | -------------------------------------------------------------------------------------- |
| 生产 adapter 绕过 `_fetch_impl` 守卫     | **未发现**        | 全部 vendor adapter（akshare/baostock/cninfo/qmt/tdx/yahoo）继承 `SkeletonAdapterBase` |
| `FetchLogWriter` 持久化层                | **缺口（defer）** | `_validate_for_persist` 不校验 structured+SUCCESS+hash；属 OP-01 defense-in-depth      |
| `sync/runners._run_fetch` 双写 fetch_log | **无 bypass**     | `adapter.fetch(..., record_fetch_log=False)` + 单独 write；result 仍经 skeleton 守卫   |
| `DataSourceService.fetch`                | **无 bypass**     | 经 `create_adapter` → skeleton                                                         |
| 损坏文件 → SUCCESS                       | **闭合**          | corrupt 测试 + infer `None` → `SCHEMA_DRIFT`                                           |

**B3V-AUD-05 负向保全：** `test_schemaHashDriftWithoutApproval_rejects` 未改动；新增负向均为 additive。

---

## 2. A8 pytest 复跑证据（对抗复验）

**环境：** `QMD_DATA_ROOT=<task>/.audit-sandbox/data` · `--basetemp=.audit-sandbox/pytest`（跑前清理 basetemp）

### 2.1 AUDIT.plan 权威选择器

```text
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest
```

| 指标   | Repair 前（A8 报告） | Post Repair 对抗复跑 |
| ------ | -------------------- | -------------------- |
| passed | 103                  | **106**              |
| exit   | 0                    | **0**                |

增量 +3：`test_missingSchemaHashOnStructuredFetch_rejects` parametrize 三后缀（+2 net）+ `test_missingSchemaHash_registryFallback_rejects`（+1）。

原始输出：`.trellis/tasks/round3v-schema-hash-fail-closed/research/adversarial-a8-rerun.txt`

### 2.2 MASTER §5.3 冻结子集 + Repair 增项

```text
10 passed · exit 0
```

含 §5.3 七项 + G-03 registry 回退 + parametrize 额外两后缀实例。

---

## 3. A1–A8 对抗复核（Post `1bc0260`）

| 维  | 修复前 OPEN | Post Repair | 对抗复核                                                    |
| --- | ----------- | ----------- | ----------------------------------------------------------- |
| A1  | 2 BLOCKING  | 0           | **PASS** — commit 入库 + `datasource-adapters.md` §3 已同步 |
| A2  | 0           | 0           | **PASS** — ponytail 建议项 WONT-FIX                         |
| A3  | 0           | 0           | **PASS** — fail-closed 偏安全                               |
| A4  | 0           | 0           | **PASS** — OP-01/02 已 disposition                          |
| A5  | 1 NB        | 0           | **PASS** — §4.3 re-defer 登记                               |
| A6  | 0           | 0           | **PASS** — 有界 I/O                                         |
| A7  | 0           | 0           | **PASS** — 无 DB mutation                                   |
| A8  | 7 NB gaps   | 0           | **PASS** — G-01/G-03 FIX；其余 re-defer/wont-fix            |

---

## 4. 计划外发现

**对抗搜索声明：** 已检索 `backend/` 中 `schema_hash`、`FetchLogWriter`、`SUCCESS`、`SkeletonAdapterBase`；对照 `validation_gate._schema_hash_blocks_write` 全分支、`skeleton_base._fetch_impl` 守卫；审阅 commit `1bc0260` diff；复跑 A8 三文件 pytest；对照 `zero-open-signoff.md` 逐项 disposition。

| ID           | 场景                               | 若只按 MASTER §5.3 测会漏什么          | 严重度       | Post Repair 处置                                            | OPEN?  |
| ------------ | ---------------------------------- | -------------------------------------- | ------------ | ----------------------------------------------------------- | ------ |
| G-01         | Gate 缺 hash 仅 `.csv` 单测        | parquet/json 后缀无独立证据            | NON-BLOCKING | **FIX** — parametrize 三后缀                                | **否** |
| G-03         | registry 回退无单测                | 无后缀 + file_registry structured 漏拦 | NON-BLOCKING | **FIX** — `test_missingSchemaHash_registryFallback_rejects` | **否** |
| G-02         | schemaless 正向豁免                | 误拒/误放未证明                        | NON-BLOCKING | **RE-DEFER** B02-DATA-05                                    | **否** |
| G-05 / OP-01 | 非 skeleton 直写 fetch_log         | gate 启发式 fail-open                  | NON-BLOCKING | **RE-DEFER** B02-DATA-05                                    | **否** |
| G-04         | row_count=0 边界                   | 条件回归无对照测                       | NON-BLOCKING | **WONT-FIX** 设计内                                         | **否** |
| G-06         | adapter→gate E2E 正向              | 分层单测未串联                         | NON-BLOCKING | **WONT-FIX** AC 已满足                                      | **否** |
| G-07         | write_contract 无 validation_tests | YAML 与 pytest 无绑定                  | NON-BLOCKING | **RE-DEFER** 全局策略                                       | **否** |
| ADV-01       | baseline 缺失 fail-open            | 首写放行                               | NON-BLOCKING | **ACCEPTED** MASTER §2.2                                    | **否** |
| ADV-02       | Parquet 落盘 infer                 | 10MB 上限                              | NON-BLOCKING | **ACCEPTED** ponytail                                       | **否** |
| VR-REG       | registry 三件套未 commit           | SSOT 行仍 INDEX 态                     | —            | **RE-DEFER** coordinator §7.3；**禁止**本分支直接 commit    | **否** |

**本轮对抗新增 OPEN：** **0**

---

## 5. Registry 三件套边界（遵守用户约束）

| 文件                                 | 本分支状态            |
| ------------------------------------ | --------------------- |
| `docs/AUDIT_DEFERRED_REGISTRY.md`    | **未修改、未 commit** |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | **未修改、未 commit** |
| `docs/RESOLVED_ISSUES_REGISTRY.md`   | **未修改、未 commit** |

Proposed delta 仅见于 `repair-evidence/registry-ready.md`；coordinator 合并后应用。

---

## 6. DOUBT 攻击摘要

| Claim                                         | 攻击                     | Post Repair 结论                                         |
| --------------------------------------------- | ------------------------ | -------------------------------------------------------- |
| 「VR-DATA-001 已 RESOLVED」                   | registry 行未更新        | **不成立** — runtime **PARTIAL**；precise re-defer 合法  |
| 「gate 永不 fail-open」                       | OP-01 无 structured 分类 | **不成立** — 已知 defer 窗口；非 skeleton 路径外生产面低 |
| 「adapter 无法产出 SUCCESS+null hash 结构化」 | skeleton 主路径          | **成立**                                                 |
| 「Repair 削弱 B3V-AUD-05」                    | diff 审查                | **不成立** — 仅 additive 负向                            |
| 「A8 绿即可签收」                             | 需 sandbox + basetemp    | **成立**（本次复跑满足）                                 |

---

## 7. 签收

| 计数         | 值       |
| ------------ | -------- |
| **OPEN**     | **0**    |
| **BLOCKING** | **0**    |
| **对抗裁决** | **PASS** |

分支 `fix/round3v-schema-hash-fail-closed`（`1bc0260`）可进入 coordinator merge 队列；`VR-DATA-001` registry 闭合待主会话 `registry-ready.md` + `B02-DATA-05`。

---

_审计员：trellis-check 对抗复验 · 只读 · 未修改 registry 三件套 · 未 commit_
