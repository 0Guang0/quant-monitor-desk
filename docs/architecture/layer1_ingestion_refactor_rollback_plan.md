# Layer 1 Ingestion 拆分回滚方案

> **Scope:** `backend/app/layer1_axes/ingestion.py`（~1500 LOC）ponytail / 解耦重构  
> **Status:** PLANNING ONLY — **未在本分支执行**  
> **台账:** `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md` §3.3  
> **原则:** 外部 API 不变；行为由现有 pytest + evidence JSON 快照守卫；每步可独立 revert。

---

## 1. 为什么后置

审计项 A03-P1-01、A07-P1-01 等要求拆分，但：

- 文件承载 Phase 2–4 runtime + 任务证据生成；
- 一次大拆易引入 fetch_log 重复、guard bypass、证据格式漂移；
- 当前全量测试 + phase evidence 测试已绿，应**先固化回归再动刀**。

---

## 2. 不可破坏的不变量（回滚验收标准）

任何拆分 PR 合并前必须全部满足；任一失败即 **revert 该 PR**：

| #   | 不变量                                                   | 验证命令                                                            |
| --- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| I1  | `Layer1ObservationIngestionService` 公开方法签名不变     | `tests/test_layer1_observation_ingestion.py` 全绿                   |
| I2  | phase3 `file_registry_delta == 1`                        | `test_layer1Ingestion_phase3_taskEvidenceArtifacts` + deep basetemp |
| I3  | phase4 clean write + snapshot                            | `test_layer1Ingestion_phase4_taskEvidenceArtifacts`                 |
| I4  | 单 fetch 单 fetch_log                                    | micro-fetch 测试 `fetch_log_delta == 1`                             |
| I5  | 证据 JSON 字段集合不变（允许空白/顺序差异）              | 对比 `execute-evidence/phase3_micro_fetch_evidence.json` 键集       |
| I6  | 无项目 `data/` 根污染                                    | `staged_acceptance_policy.md` sandbox 路径断言                      |
| I7  | `from backend.app.layer1_axes.ingestion import …` 仍可用 | 保留 facade re-export 一个发布周期                                  |

---

## 3. 分步实施顺序（每步一个 PR，可单独回滚）

```text
PR-R2a  提取 ingestion_evidence.py（仅移动 capture_* / format_* 函数 + 常量）
        ingestion.py 改为 import 并 re-export（零逻辑变更）
        → 跑 I1–I7

PR-R2b  提取 sandbox_bootstrap.py（phase1/2/3/4 共享 DB/data_root 构建）
        → 跑 I1–I7 + Windows deep basetemp

PR-R2c  拆分 commit_clean_observation_and_snapshots 为私有方法
        （validate / conflict / write / snapshot / lineage 五段，仍在同一类内）
        → 跑 I1–I7

PR-R2d  （可选）commit 子模块独立文件 ingestion_commit.py
        → 仅当 PR-R2c 稳定且 review 通过
```

**禁止跳步:** 不得从 PR-R2a 直接到 PR-R2d。

---

## 4. Git 回滚操作（每步失败后）

```powershell
# 假设问题出在最新拆分 commit 上（未 push）
git revert HEAD --no-edit

# 已 push 到 fix/audit-report-issues-* 或 feature 分支
git revert <bad-commit-sha> --no-edit
git push origin HEAD

# 紧急恢复 runtime 文件（仅当 revert 冲突）
git checkout origin/master -- backend/app/layer1_axes/ingestion.py
# 然后手动恢复 path_compat 等已合并的独立修复
```

回滚后**必须**重跑：

```powershell
pytest tests/test_layer1_observation_ingestion.py -q --basetemp=.audit-sandbox/pytest-9agent-restored-targeted
pytest -q
```

---

## 5. 机械检查清单（PR 作者）

- [ ] 未改 `MicroFetchResult` / `IngestionCommitResult` dataclass 字段
- [ ] 未改 `capture_task_phase*_evidence` 函数签名
- [ ] 未改证据目录名（`.phase3-micro-fetch-sandbox` 等）
- [ ] `git diff` 无 `data/`、`*.duckdb` 生产路径
- [ ] `ruff check` + `pytest -q` 绿
- [ ] `detect_changes()` 风险非 CRITICAL（GitNexus）

---

## 6. 与 Batch 2.75 / Batch 3 的关系

- **Batch 2.75 live pilot** 与拆分**并行禁止**：先 pilot 或先 PR-R2a，不要同 sprint 混做。
- **Batch 3** 规划文档必须继续声明 **staged-only downstream**，不因拆分而扩大为 production-live。
