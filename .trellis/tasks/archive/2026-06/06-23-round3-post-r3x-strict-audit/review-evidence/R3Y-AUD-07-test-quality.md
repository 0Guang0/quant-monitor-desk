# R3Y-AUD-07 — Test quality 反证

**Result: WARN**

Worktree: `quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` · 基准 `master` @ `61436a51`  
审计模式：只读 · 未修改任何测试或实现

---

## 目标与反证假设

**反证假设：** PROMPT_11–17 / R3X 声称 FIXED/CLOSED 的项，其回归测试若大量停留在 `hasattr` / `import` / 文件存在性 / 注册表键检查，则「测试绿」不能证明修复已进入 runtime path。

**本 issue 范围：**

| 文件                                             | 用例数 | 角色                        |
| ------------------------------------------------ | ------ | --------------------------- |
| `tests/test_r3x_residual_open_items_closure.py`  | 18     | PROMPT_15 伞测              |
| `tests/test_r3x_ponytail_structural_bucket_b.py` | 19     | POST14 Bucket B 结构性回归  |
| `tests/test_staged_pilot.py`                     | 26     | PROMPT_14 staged pilot 门禁 |

另交叉核查：**ADV-R3X-SYNC-001** 是否在上述或关联模块有 runtime 级回归。

---

## 读取文件（含 call path 追溯）

| 类别                 | 路径                                                                                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| 派发 / 任务卡        | `.trellis/tasks/06-23-round3-post-r3x-strict-audit/research/parallel-audit-dispatch.md`                 |
| R3Y §4 issue 定义    | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md` |
| QA 模板              | `agents/qa-expert.md`                                                                                   |
| 测试规范             | `.claude/skills/testing-guidelines/SKILL.md`                                                            |
| 目标测试             | 上表三文件                                                                                              |
| SYNC-001 声称        | `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md` §4.1  |
| Runtime 路径         | `backend/app/sync/orchestrator.py` L127–164、`backend/app/sync/runners.py` L42–75 / L325–328            |
| 关联 service-path 测 | `tests/test_sync_orchestrator.py`（`test_servicePath_*`，不在本 issue 必跑集内）                        |

---

## 核查方法（code trace + pytest）

### 深度分类标准（对齐 testing-guidelines §2–3）

| 等级                | 判定                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| **Runtime-strong**  | 调用真实业务 API，断言可观测结果（状态码、DB 行、异常类型+消息、事件顺序、持久化字段）           |
| **Runtime-medium**  | 执行纯函数/门禁逻辑，输入→输出语义明确；或 mock **仅** 外部 I/O（网络/akshare）且断言 payload/DB |
| **Structural-weak** | `hasattr` / `callable` / `in _ADAPTER_TYPES` / 读源文件 LOC / `is_file` / 配置文件 substring     |
| **Evidence-only**   | 仓库内 markdown/授权文件存在性（审计追溯合理，但不证明 runtime）                                 |

### Pytest 执行记录

```text
cd quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
python -m pytest tests/test_r3x_residual_open_items_closure.py \
                 tests/test_r3x_ponytail_structural_bucket_b.py \
                 tests/test_staged_pilot.py -q --tb=no
```

| 指标     | 结果               |
| -------- | ------------------ |
| 收集用例 | 63（18 + 19 + 26） |
| 通过     | 63                 |
| 失败     | 0                  |
| 跳过     | 0                  |
| 耗时     | ~7.7s              |

**结论：** 目标集全部绿；绿不等于深度足够（见下表）。

---

## Test-depth findings

### 1. `test_r3x_residual_open_items_closure.py` — 混合，伞测偏强但有关键缺口

| 测试                                                              | 深度                | 说明                                                                 |
| ----------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------- |
| `test_advR3xRoute001_*`                                           | Runtime-strong      | `production_route_planner().plan()` → `route_status` / `skip_reason` |
| `test_advR3xRoute003_*`                                           | Runtime-strong      | `DISABLED_SOURCE` + quality flag                                     |
| `test_advR3xRoute004_*`                                           | Runtime-strong      | Validation 角色 → `VALIDATION_SOURCE_USED`                           |
| `test_advR3xService001_*`                                         | Runtime-strong      | `DataSourceService.fetch` → `AdapterConfigurationError`              |
| `test_advR3xConflict001_*`                                        | Runtime-medium      | 阈值查找 + alias 映射（未跑完整 conflict 流水线）                    |
| `test_advR3xL1_002_*`                                             | Runtime-strong      | `InterpretationRejectedError` 真实拒绝                               |
| `test_advR3xWrite002_*` / `test_advA1_001_*` / `test_advA1_012_*` | Runtime-strong      | WriteManager + DuckDB sandbox                                        |
| `test_advA2_002_*`                                                | Runtime-medium      | adapter `health_check()` 结构化 stub                                 |
| `test_advA3_016_*`                                                | Runtime-strong      | deferred API → `NotImplementedError`（非 SYNC-001）                  |
| `test_advA2_009_*` / `test_advR3xCap002_*`                        | **Structural-weak** | 仅 `"tdx_pytdx" in _ADAPTER_TYPES`                                   |
| `test_advA2_004_*`                                                | **Structural-weak** | 仅 `CninfoAdapter.supported_domains` 类属性                          |
| `test_advR3xCap001_*`                                             | **Structural-weak** | 空 dict 断言（与 bucket*b `test_ds04*\*` 重复）                      |
| `test_defaultOperation_coversAllDomainRoles`                      | **Structural-weak** | YAML key → `_default_operation` 非空                                 |
| `test_advA5_001_*` / `test_advA6_004_*`                           | **Evidence-only**   | `.gitignore` / `vite.config.ts` 文本模式                             |

**统计：** Runtime-strong/medium **11/18**；Structural-weak **5/18**；Evidence-only **2/18**。

**HIGH — ADV-R3X-SYNC-001 无伞测映射**

- merge_gate 声称 **FIXED**：`orchestrator → DataSourceService fetch_callable`（`merge_gate_report.md` L37）。
- 本文件 **无任何** `ADV-R3X-SYNC-001` / `advR3xSync001` 用例。
- Code trace：`run_incremental` 仍接受 `adapter=` 与 `datasource_service=` 二选一（`orchestrator.py` L131–156）；`IncrementalJobRunner.run` 禁止同时传入两者（`runners.py` L327–328），但 **adapter-only 路径仍合法**，可绕过 `DataSourceService` 路由/门禁。
- 关联覆盖：`tests/test_sync_orchestrator.py` 有 `test_servicePath_*`（3 条，走 `datasource_service=`），但同文件大量 `adapter=_*Adapter()` 用例仍绿——证明 adapter 旁路 **未被测试禁止**，仅新增 service 路径可选。
- `test_r3x_ponytail_pilot_prep_bucket_a.py::test_sy04_*` 只测 `_fetch_with_guard` helper 统一，**不是** orchestrator 级「禁止裸 adapter」契约。

---

### 2. `test_r3x_ponytail_structural_bucket_b.py` — 结构性为主，runtime 薄

文件头注释已声明「结构性 ponytail 回归」；与 R3Y 反证「runtime 行为」目标 **部分错位**。

| 深度            | 数量 | 代表用例                                                                                                                                                                     |
| --------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Runtime-strong  | 1    | `test_write_manager_rejects_unimplemented_contract_modes`                                                                                                                    |
| Runtime-medium  | 3    | `test_snapshot_lineage_kernel_*`、`test_health_check_stub_*`、`test_ds06_default_operation_*`                                                                                |
| Structural-weak | 15   | `test_op03_*`（`hasattr` + `inspect.getsource`）、`test_l1_04/06/07/09/12_*`、`test_sy02/06/07_*`、`test_l2_04/05/06_*`、`test_live_pilot_modules_under_loc_cap`（LOC 计数） |

**统计：** Runtime **4/19**（21%）；Structural **15/19**（79%）。

**WARN — 典型脆化/存在性断言（testing-guidelines §2 违规模式）**

```83:85:tests/test_r3x_ponytail_structural_bucket_b.py
    assert hasattr(fetch_port_common, "recent_window_start")
    assert "_recent_window_start" not in inspect.getsource(live_pilot_fetch_ports)
    assert "_recent_window_start" not in inspect.getsource(interface_probe_fetch_ports)
```

- 通过只证明符号/源码形态，**不证明** `recent_window_start` 在 pilot/probe fetch 中返回正确窗口或 dedupe 行为。
- `test_l2_04_*`：`assert Layer2SnapshotWriter is not None` — 等价于 import 成功。

**与 residual 伞测重复：** `test_ds04_compat_map_empty` ↔ `test_advR3xCap001_*`（同一空 map，零新增 runtime 信号）。

---

### 3. `test_staged_pilot.py` — 整体最好，仍有门禁浅层与 proof 缺口

| 深度            | 数量 | 说明                                                                                                                      |
| --------------- | ---- | ------------------------------------------------------------------------------------------------------------------------- |
| Runtime-strong  | 14   | 授权 fail-closed、mock fetch 不触发、network cap、WriteManager STAGED 路径、DB `can_write_clean=False`、cninfo 字段校验等 |
| Runtime-medium  | 5    | `parse_pilot_date_window`、closeout 派生、taxonomy 分类、route preview 字段                                               |
| Structural-weak | 4    | `isinstance` factory 命名、`approved_pilot_requests` 集合、`validate_authorization` 无异常即过                            |
| Evidence-only   | 3    | 授权 md 存在、evidence 相对路径、validator **名字**在 JSON 中声明                                                         |

**亮点（runtime 反证有效）：**

- `test_stagedPilot_missingAuthorization_blocksBeforeFetch` — patch `DataSourceService.fetch` + 断言未调用。
- `test_stagedPilot_mockFetchSuccess_usesWriteManagerStagedQualityFlag` — 断言 `file_registry_write_path == "WriteManager"` 与 `quality_flag == "STAGED"`。
- `test_stagedPilot_sandboxValidationReport_canWriteCleanFalse` — 查 DuckDB `validation_report` 行。

**WARN — 语义深度不足**

| ID               | 问题                                                                                                                                                                                                                                                      |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADV-POST14-A-006 | `test_stagedPilot_validationReport_declaresSandboxValidators` 只断言 JSON 字符串含类名，**未调用** `DbValidationGate` / `DataQualityValidator`                                                                                                            |
| Mutation proof   | `test_stagedPilot_mutationProof_inconclusiveWhenProductionDbMissing` 仅覆盖 DB **缺失**；`capture_route_preview_matrix` 对 `VERIFIED` 分支为条件断言，CI 无生产库时常落 `INCONCLUSIVE`，**未测** schema-only / row-count-only / hash 变化四类 R3Y §3 情形 |
| Route ordering   | staged pilot 无「ROUTE_PLAN 事件早于 FETCHING」类断言（该深度在 `test_sync_orchestrator.py::test_servicePath_routePlanBeforeFetching`）                                                                                                                   |

**统计：** Runtime-strong/medium **19/26**（73%）；弱/证据 **7/26**（27%）。

---

### 4. ADV-R3X-SYNC-001 专项 — 缺 dedicated runtime 回归

| 检查项                                         | 状态                                                                |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| 伞测 `test_r3x_residual_open_items_closure.py` | ❌ 无                                                               |
| bucket_b                                       | ❌ 无（仅 `hasattr(_PipelineMixin, "_finalize_staged")` 等）        |
| staged_pilot                                   | ❌ 不适用（不同模块）                                               |
| `test_sync_orchestrator.py` service path       | ⚠️ 有 3 条正向 service 测，但 adapter 旁路仍大量覆盖且合法          |
| merge_gate FIXED 声称                          | ⚠️ 实现为「新增 fetch_callable 路径」，非「移除/拒绝 adapter 旁路」 |

**反证结论：** SYNC-001 的 FIXED 状态 **不能** 由本 issue 三文件证明；现有测试不能反证「sync 仍可通过 `adapter=` 绕过 DataSourceService」。

---

## 反证结论（修复是否进入 runtime）

| 模块                                         | 测试能否支撑 runtime 闭合                    | 评级 |
| -------------------------------------------- | -------------------------------------------- | ---- |
| Source route / validation-only / disabled    | 是（伞测 route001/003/004）                  | PASS |
| WriteManager fail-closed                     | 是（伞测 + bucket_b 各 1）                   | PASS |
| Staged pilot 授权/禁用/网络 cap/STAGED write | 是（staged_pilot 多条 strong）               | PASS |
| Ponytail Bucket B 结构拆分                   | **否**（79% 存在性/LOC）                     | WARN |
| ADV-R3X-SYNC-001 service-only fetch          | **否**（无 dedicated 测 + adapter 旁路仍开） | WARN |
| Production mutation proof 四类               | **部分**（仅 missing DB；VERIFIED 路径弱）   | WARN |
| CAP-002 / A2-009 工厂注册                    | **否**（仅 dict 键）                         | WARN |

**总评：** 核心 pilot 与 route/write 门禁有足够 runtime 测试支撑 staged-only 继续；但 **PROMPT_15 伞测与 bucket_b 混有大量结构性断言**，且 **SYNC-001 与 mutation proof 深度** 不足以支撑「全部 closed 项均有 runtime 反证」的强结论。

---

## Findings 汇总

| 级别     | ID                     | 摘要                                                                | 位置                                                                          |
| -------- | ---------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **HIGH** | SYNC-001-GAP           | merge_gate FIXED 无对应 pytest；`adapter=` 旁路仍合法且大量旧测覆盖 | 伞测缺失；`orchestrator.py` L131–156；`test_sync_orchestrator.py` L173–177 等 |
| **WARN** | BUCKET-B-SHALLOW       | 19 条中 15 条 hasattr/LOC/inspect/callable                          | `test_r3x_ponytail_structural_bucket_b.py`                                    |
| **WARN** | CAP-002-WEAK           | `tdx_pytdx in _ADAPTER_TYPES` 不验证 fetch/route                    | `test_r3x_residual_open_items_closure.py` L167–170                            |
| **WARN** | STAGED-VALIDATOR-DECL  | 只声明 validator 类名，不执行 gate                                  | `test_staged_pilot.py` L335–347                                               |
| **WARN** | MUTATION-PROOF-PARTIAL | 缺 VERIFIED / schema-only / tampered hash 场景                      | `test_staged_pilot.py` L306–319, L168–192                                     |
| **LOW**  | DUP-CAP001             | 空 compat map 双文件重复                                            | 伞测 L220–224 + bucket_b L146–150                                             |
| **LOW**  | EVIDENCE-ONLY          | gitignore/vite/授权 md 存在性                                       | 伞测 L135–145；staged L292–303                                                |

---

## 阻塞项 / 建议

### 阻塞项（本 issue 视角）

- **无 BLOCK：** 目标 pytest 全绿；staged pilot 与 route/write 关键路径有实质 runtime 测。
- **WARN 不单独阻塞 AUD-08**，但应写入 go/no-go 控制项（见 R3Y-AUD-04 / AUD-01 交叉引用）。

### 建议补测方向（供后续 fix 分支，**本审计不改测试**）

1. **ADV-R3X-SYNC-001：** `run_incremental(..., adapter=X)` 在 production 入口应 reject **或** 文档化 adapter 仅测试专用；至少一条 orchestrator 级测断言 `datasource_service.fetch` 被调用且 route 事件顺序。
2. **bucket_b：** 将 OP-03/L1-04 等从 `hasattr` 升级为调用 `recent_window_start(...)` / `resolve_task_sandbox_db(...)` 的输出断言。
3. **CAP-002：** 工厂注册 + `create_adapter("tdx_pytdx")` + disabled-by-default route 行为（非仅 dict 键）。
4. **staged mutation proof：** 增加 tmp_path DuckDB fixture 的 `VERIFIED` + row-count 变化检测反例。
5. **A-006：** `capture_validation_report` 在 stub manifest 下触发一次 validation gate 失败/通过 observable 字段。

---

## 与 v0 monolithic 对比

| 项               | v0     | 本报告                                             |
| ---------------- | ------ | -------------------------------------------------- |
| 结论             | WARN   | **WARN**（一致，本报告量化深度比例 + pytest 记录） |
| bucket_b hasattr | 提及   | 15/19 结构性 + 代码引用                            |
| SYNC-001         | 提及   | HIGH + orchestrator/runner trace                   |
| staged_pilot     | 未细分 | 19/26 runtime + mutation/validator 缺口            |

---

**R3Y-AUD-07 签署：** WARN — 关键 pilot/route/write runtime 覆盖尚可；结构性桶测与 SYNC-001/CAP-002/mutation proof 深度不足，closed 声称不能完全被测试反证。
