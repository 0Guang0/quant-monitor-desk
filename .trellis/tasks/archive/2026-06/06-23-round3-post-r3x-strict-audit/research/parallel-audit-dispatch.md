# PROMPT_18 并行对抗审计 — 派发计划 v2

> Worktree: `../quant-monitor-desk-wt-review-r3-post-r3x-strict-audit`  
> 基准: `master` @ `61436a51` · **只读** · staged-only  
> 协调者: 主会话 · 用户可并行审阅各 agent 产出

## 审核范围（任务卡摘要）

**不是**重扫 69 项清单；**是**对 PROMPT_11–17 / R3X 已声称 FIXED/CLOSED 的结论做**反证**：

| 维度        | 必答问题                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| 修复真实性  | closed 项是否有 runtime 路径 + 测试 + evidence？                                                         |
| 旁路        | staged pilot 能否绕过 DataSourceService / RoutePlanner / WriteManager / ValidationGate / ResourceGuard？ |
| no-mutation | DB 存在/缺失/schema-only/row-count-only 四类 proof 是否可信？                                            |
| registry    | RESOLVED/UNRESOLVED/DEFERRED 是否与 merge 报告一致？                                                     |
| 下一步      | 是否允许 pilot v2、data health v1？                                                                      |

**代码面（可读、不可改）：** `backend/app/datasources|db|storage|sync|ops|layer2_sensors|layer5_evidence/` + `specs/datasource_registry/` + `tests/` + Trellis merge evidence。

**禁止：** 改实现/spec/registry/DB；live fetch；启用 disabled source；full market scan。

---

## 并行派发矩阵（1 agent = 1 垂直 issue）

| Issue          | Agent ID                   | 深挖模块                                                  | 模板                                        | 必跑测试（只读）                                                                          | 产出                                                                     |
| -------------- | -------------------------- | --------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **R3Y-AUD-01** | `r3y-aud-01-closed-claims` | PROMPT_11–17 merge_gate + `.trellis/tasks/fix-*` evidence | `agents/audit-a5-completion.md`             | `test_r3x_residual_open_items_closure.py`                                                 | `review-evidence/R3Y-AUD-01-closed-claims.md` + `closed-claim-matrix.md` |
| **R3Y-AUD-02** | `r3y-aud-02-source-route`  | `backend/app/datasources/` + registry yaml                | `agents/security-auditor.md`                | `test_datasource_service.py` `test_source_route_planner.py` `test_source_capabilities.py` | `review-evidence/R3Y-AUD-02-source-route.md`                             |
| **R3Y-AUD-03** | `r3y-aud-03-write-gate`    | `backend/app/db/` `storage/` `sync/`                      | `agents/security-auditor.md` + `sql-pro.md` | `test_db_validation_gate.py` `test_write_manager.py` `test_raw_store.py`                  | `review-evidence/R3Y-AUD-03-write-validation.md`                         |
| **R3Y-AUD-04** | `r3y-aud-04-staged-pilot`  | `backend/app/ops/staged_pilot.py` `mutation_proof.py`     | `agents/database-administrator.md`          | `test_staged_pilot.py`                                                                    | `review-evidence/R3Y-AUD-04-staged-pilot.md`                             |
| **R3Y-AUD-05** | `r3y-aud-05-lineage`       | `layer2_sensors/` `layer5_evidence/` lineage              | `agents/audit-a5-completion.md`             | `test_layer2_sensor_loader.py` `test_layer5_evidence_foundation.py`                       | `review-evidence/R3Y-AUD-05-lineage.md`                                  |
| **R3Y-AUD-06** | `r3y-aud-06-registry`      | 三 registry + post-14 docs                                | `agents/audit-a1-spec.md`                   | `test_round3_audit_registry_alignment.py`                                                 | `review-evidence/R3Y-AUD-06-registry.md` + `registry-drift-table.md`     |
| **R3Y-AUD-07** | `r3y-aud-07-test-depth`    | `tests/test_r3x_*` `test_staged_pilot.py` 深度            | `agents/qa-expert.md`                       | 上述 + `test_r3x_ponytail_structural_bucket_b.py`                                         | `review-evidence/R3Y-AUD-07-test-quality.md`                             |
| **R3Y-AUD-08** | **协调者**（等 01–07）     | 汇总 go/no-go                                             | —                                           | —                                                                                         | `review.report.md` + `R3Y-AUD-08-go-no-go.md`                            |

v0 单 agent 浅表结论已标记 **`review-evidence/v0-monolithic/`**（供对比，不作为最终 gate）。

---

## 每个 agent 交付格式（强制）

```markdown
# R3Y-AUD-0X — <title>

**Result:** PASS | WARN | BLOCK

## 目标与反证假设

## 读取文件（含 call path 追溯）

## 核查方法（code trace + pytest 命令与结果）

## Findings（HIGH/WARN，文件:行号）

## 反证结论（修复是否进入 runtime）

## 阻塞项 / 建议
```

Skill: `doubt-driven-development` · 可用 GitNexus `query`/`context` 追溯 call graph。

---

## 用户审阅入口

并行完成后逐文件打开 `review-evidence/R3Y-AUD-*.md`；若某 issue 需加深或改范围，告知协调者重派该 issue agent。

**AUD-08 gate** 在 01–07 全部落盘后由协调者合成，不与其他 agent 并行抢结论。
