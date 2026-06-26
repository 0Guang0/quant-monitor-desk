# PLAN REVIEW — R3FR-07（请用户审阅）

> **Trellis 任务目录：** `.trellis/tasks/06-27-06-27-round3fr-cleanup-rehome/`  
> **建议分支：** `chore/round3fr-cleanup-rehome`  
> **状态：** Plan 完成 · **未** `task.py start` · **未** Execute

---

## 1. 任务目的与价值（一句话）

在 R3FR-01~06 已合并的前提下，**关门 Batch 3F-R**：清掉过时 placeholder 叙事、给旧 shim 标明 canonical 去向、更新路线图使 **Round 3G 成为合法下一入口**——避免重复劳动与微切片回归。

---

## 2. 实现范围（做什么 / 不做什么）

### 做

| 类别    | 内容                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------------- |
| 文档    | 修正 `ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md` 等仍写 `health_check` placeholder 的段落；更新 manifest DONE 状态 |
| Runtime | `check_daily_bars` / `health_check` / TDX probe 文件：**注释 + 可选 DRY**（行为不变）                                  |
| 索引    | `PROJECT_IMPLEMENTATION_ROADMAP` · `ROUND3_HANDOFF` · 3G README · `MODULE_COMPLETION_RATING`                           |
| 测试    | 新建 `tests/test_r3fr07_legacy_wrapper_cleanup.py`；回归 §5 五档 + `test_provider_catalog`                             |

### 不做

- 3G sandbox clean write 实现
- 新 profile / provider / registry 行
- 删归档 Trellis 证据
- 关闭 B2.5-O-05 / Eastmoney DEFERRED（留给 3H）

---

## 3. 做到什么程度 = Done

满足 `PROJECT_IMPLEMENTATION_ROADMAP.md` **条件 A**：Batch 3F-R 全部完成（R3FR-07 为最后一张卡）。

可机械验证：

1. 六条 AC（`EXECUTION_INDEX.md` §0.1）全绿
2. 任务卡 §5 四档 targeted pytest 绿
3. `uv run pytest -q` 全绿
4. `loop_maintain.py` check 通过
5. HANDOFF/ROADMAP 写明 **3F-R CLOSED → 3G next**

---

## 4. 执行步骤摘要（8 步 TDD）

| Step | 内容                        | 关键证据                                |
| ---- | --------------------------- | --------------------------------------- |
| 9.0  | 基线 pytest                 | `9.0-green.txt`                         |
| 9.1  | 规划叙事清理                | 新测 README 无 stale placeholder        |
| 9.2  | `check_daily_bars` redirect | docstring 测试 + `test_ops_data_health` |
| 9.3  | `health_check` redirect     | docstring 测试 + `test_qmd_data_cli`    |
| 9.4  | TDX probe redirect          | delegate 文档 + tdx 回归                |
| 9.5  | 3F-R 关门 / 3G 入口         | roadmap/handoff/3G README/rating 测试   |
| 9.6  | guardrails + loop           | 文档索引                                |
| 9.7  | 全量 pytest + handoff 校验  | `9.7-green.txt`                         |

完整 RED/GREEN 命令见 `EXECUTION_INDEX.md` §1。

---

## 5. 架构与规则边界

```text
Canonical（勿在 cleanup 中削弱）
  run_data_health_profile / market_bar_p0     ← data health + CLI
  TdxPytdxFetchPort                           ← TDX fetch
  provider_catalog.yaml                       ← source 元数据

Shim（可保留，须 redirect）
  check_daily_bars          ← evidence-path 兼容
  TdxPytdxProbeFetchPort    ← 已委托 port

不变治理
  DataSourceService · WriteManager · ResourceGuard
  禁止 参考项目/** runtime import
  禁止 production-live 声明
```

---

## 6. 并行 / 串行

- **R3FR-07：严格串行，单分支** `chore/round3fr-cleanup-rehome`
- **合并 master 后** 才可 Plan/Execute **3G-01**（3G 内部仍 R3G-01→02→03 串行）
- 可选债务轨（CI gate 等）**不要**与本分支争用 `data_health.py` / ROADMAP

---

## 7. 风险与缓解

| 风险                                 | 缓解                                          |
| ------------------------------------ | --------------------------------------------- |
| DRY `check_daily_bars` 改行为        | TDD + 失败则只留 docstring                    |
| 文档-only 假完成                     | `test_r3fr07_*` 静态锁门                      |
| master 领先 origin 19 commits        | 从当前 master 开分支                          |
| 3G 文案更新破坏 downstream 16 卡治理 | 9.6 全量 `test_reference_adoption_guardrails` |
| `context_pack.json` 空               | Boot 以 §3 manifest 为准                      |

---

## 8. 对抗性审计（2026-06-27 已修复）

报告：[`research/adversarial-plan-audit.report.md`](research/adversarial-plan-audit.report.md) · 倒查：[`research/project-map-omission-check.md`](research/project-map-omission-check.md)

| 修复项          | 前 → 后                                                   |
| --------------- | --------------------------------------------------------- |
| §3 Execute 必读 | 5 行 → **27 行**（`implement.jsonl` 31 行含 Boot）        |
| AC              | 6 → **8**（batch map、inventory redirect）                |
| 9.0 回归        | 无 → `test_provider_catalog.py`                           |
| 9.3 契约        | 无 → `test_data_cli_contract.py`                          |
| Audit A1/A3     | 增补 manifest 计数 + stale-doc rg + downstream governance |

**残留（不阻塞）：** Trellis 目录 `06-27-06-27-*` 双日期；`context_router` 未填 modules。

---

## 9. 审阅后请你确认

- [ ] **批准 Plan** → 我将 `task.py start` 并在 `chore/round3fr-cleanup-rehome` 上 Execute
- [ ] **修改意见** → 指出需调整的 AC/步骤/范围
- [ ] **暂缓** → 不启动 Execute

### 批准后第一条命令（Execute 会话）

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
git checkout -b chore/round3fr-cleanup-rehome master
uv run python .trellis/scripts/task.py start .trellis/tasks/06-27-06-27-round3fr-cleanup-rehome
```

---

## 10. Plan 产出物索引

| 文件                                                     | 用途                    |
| -------------------------------------------------------- | ----------------------- |
| `EXECUTION_INDEX.md`                                     | Execute/Audit 步骤与 AC |
| `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` | 冻结正文 SSOT           |
| `AUDIT.plan.md`                                          | 审计矩阵                |
| `research/plan-boot.md`                                  | P0 已读清单             |
| `research/grill-me-session.md`                           | 对抗性质问闭合          |
| `research/integration-ledger.md`                         | 允许/禁止文件           |
| `research/adversarial-plan-audit.report.md`              | 对抗性 Plan 审计        |
| `research/project-map-omission-check.md`                 | cleanup targets 倒查    |

活任务卡（Plan 加固）：`docs/implementation_tasks/.../R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`
