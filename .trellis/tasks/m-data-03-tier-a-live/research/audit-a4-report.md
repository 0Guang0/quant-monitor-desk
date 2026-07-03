# Audit A4 — Code Quality（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                     |
| ----------------------- | -------------------------------------- |
| 维度                    | A4 — code-reviewer                     |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live` |
| `plan_protocol_version` | 4.1                                    |
| 模板                    | `agents/code-reviewer.md`              |
| 审计日期                | 2026-07-03                             |
| 分支                    | `feature/m-data-03-tier-a-live`        |

---

## 维度证据 §3.4

### Boot / 对抗动作

- 已 Read：`agents/audit-boot-v4.1.md` · `agents/audit-finding-schema.md` · `agents/audit-adversarial-authority.md` · `agents/code-reviewer.md` · `AUDIT.plan.md` §2 A4 · `research/plan-spec.md` · `research/to-issues-slices.md` · `research/gitnexus-audit-summary.md` · `specs/contracts/live_tier_a_evidence_v1.yaml`
- GitNexus：`query tier_a_live acceptance`（索引未收录 `run_acceptance_report`；以代码 Read 为准，见 gitnexus-audit-summary.md）
- 实现锚点：`backend/app/ops/tier_a_live_acceptance.py` · `tests/test_live_tier_a_evidence_contract.py` · `tests/test_tier_a_live_acceptance_report.py` · `tests/test_tier_a_live_b2_acceptance.py` · `tests/test_tier_a_live_dispatch.py`

### 验证命令

```bash
uv run pytest tests/test_live_tier_a_evidence_contract.py tests/test_tier_a_live_acceptance_report.py tests/test_tier_a_live_b2_acceptance.py -q
# 45 passed

uv run pytest tests/test_tier_a_live_dispatch.py::test_runSourceLiveAcceptance_plannedWithZeroCleanFails -q
# 1 passed — 仅覆盖 run_source_live_acceptance，未覆盖 --report 路径
```

### 五轴审查

| 轴         | 评估   | 要点                                                                                                            |
| ---------- | ------ | --------------------------------------------------------------------------------------------------------------- |
| **正确性** | 中     | manifest 形状与 11 源 binding 对齐；`--report` 路径缺 zero-clean/raw 守卫，与 CLI 路径不一致                    |
| **可读性** | 中     | 单文件内 `_process_source_for_report` 与 `run_source_live_acceptance` 双轨，gate 顺序不同，维护成本高           |
| **架构**   | 中     | 统一验收层名义上在 `_process_source_for_report`，但 `run_acceptance` 仍走独立函数；FAIL_EXTERNAL/adr_ref 未接线 |
| **安全**   | 可接受 | `assert_isolated_live_data_root` fail-closed；无密钥进 manifest                                                 |
| **性能**   | 可接受 | 11 源串行可接受；inspect 已 FAIL 仍跑 F0/B2（浪费但非 blocker）                                                 |

### §3.4 轴表

| 轴     | 发现                           | 证据                                                                                                    |
| ------ | ------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 正确性 | `--report` 缺 zero-clean 守卫  | `tier_a_live_acceptance.py:348-362` vs `:513-521` / `:524-580`                                          |
| 架构   | 双 acceptance pipeline         | `run_acceptance` → `run_source_live_acceptance`；`run_acceptance_report` → `_process_source_for_report` |
| 正确性 | FAIL_EXTERNAL / adr_ref 未实现 | `tier_a_live_acceptance.py:569` · `:638-655`                                                            |
| 正确性 | fetch 子结构无契约测           | `test_live_tier_a_evidence_contract.py` 仅断言顶层字段                                                  |
| 可读性 | schema_hash 占位无 ponytail    | `tier_a_live_acceptance.py:447`                                                                         |

### 做得好的地方

- `build_live_tier_a_evidence_manifest` + `REPORT_FAILURE_TO_MANIFEST` 提供 11 源统一信封；`@pytest.mark.parametrize` 覆盖全 `TIER_A_SOURCES`
- `_process_source_for_report` 将 F0/B2 结果写入 manifest acceptance 段，report 行与 manifest 字段同步（B2/E2 测可证）
- `write_acceptance_failure_artifact` 符合 contract `failure_artifact` 形状；负向测 `test_reportRun_writesFailureArtifactOnFixableFail` 存在
- 隔离根路径校验清晰（`.audit-sandbox/m-data-03` + 主库拒绝）

### DOUBT 对抗搜索

已搜索：`tier_a_live_acceptance.py` 全文件 · `classify_source_report_failure` · `FAIL_EXTERNAL`/`adr_ref` · `clean_row_count` 守卫 · manifest fetch 字段 · contract `required_tests` 三模块 · `test_tier_a_live_dispatch.py` acceptance 测 · plan-spec pipeline 顺序。

---

## §维度裁决

**FAIL**

（§计划内 3 条 + §计划外 2 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                  | 锚点                                                                           | 根因                                                                                                                                                                           | 修复方案                                                                                                                                                                                       | 验证                                                                                                                                                             |
| --------- | --- | ------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A4-P1-001 | P1  | `--report` 路径缺 zero-clean/raw 守卫 | `backend/app/ops/tier_a_live_acceptance.py:513-521` · `:524-580` vs `:348-362` | `classify_source_report_failure` 仅查 inspect/sync；`run_source_live_acceptance` 的 COMPLETED/PLANNED + `clean_row_count<1` 且无 raw 检查未复用到 `_process_source_for_report` | 提取共享 `evaluate_source_gates(outcome, data_root)`（含 fred raw 例外）；`_process_source_for_report` 与 `run_source_live_acceptance` 共用；补 `test_reportRun_plannedWithZeroCleanFails`     | `uv run pytest tests/test_tier_a_live_acceptance_report.py tests/test_tier_a_live_dispatch.py -q`；mock COMPLETED/PLANNED + clean_row_count=0 → disposition=fail |
| A4-P2-001 | P2  | 双 acceptance pipeline 口径分叉       | `tier_a_live_acceptance.py:303-371` · `:524-580` · `:374-398` · `:611-660`     | `run_acceptance` 与 `run_acceptance_report` 各走独立编排；gate 顺序不同（CLI：F0→B2→inspect；report：classify→F0→B2）                                                          | 单一 `run_source_acceptance_pipeline(...)` 返回 row+manifest；两入口仅包装 env/report 写出                                                                                                     | 两入口共用函数后现有 45+ dispatch 测仍绿；grep 仅一处 gate 逻辑                                                                                                  |
| A4-P2-002 | P2  | FAIL_EXTERNAL / adr_ref 未接入 report | `tier_a_live_acceptance.py:569` · `:638-655`                                   | `classify_source_report_failure` 仅产出 PASS/FAIL_FIXABLE；`adr_ref` 恒 `None`；contract exit 0 + ADR 路径未实现                                                               | 按 contract `failure_class_canonical` 在 sync/网络/RATE_LIMIT 等分支映射 FAIL_EXTERNAL；读 env/配置 ADR ref；`run_acceptance_report` exit 0 当且仅当全源 PASS 或 FAIL_EXTERNAL 且 adr_ref 有效 | 单测 mock RATE_LIMITED outcome → FAIL_EXTERNAL + adr → exit 0；无 ADR → exit 1                                                                                   |

---

## 计划外发现

| ID        | P   | 标题                              | 锚点                                                                                            | 根因                                                                  | 修复方案                                                                                                                               | 验证                                                                    |
| --------- | --- | --------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| A4-P2-003 | P2  | manifest fetch 子结构无契约测     | `tests/test_live_tier_a_evidence_contract.py:75-97` · contract `envelope.fetch.required_fields` | 测仅断言 `required_top_level_fields`；fetch 七字段缺位时无 RED        | 新增 parametrize 11 源：`test_buildManifest_fetchRequiredFieldsPerSource` 断言 `envelope.fetch.required_fields` 全在且 `status` ∈ enum | `uv run pytest tests/test_live_tier_a_evidence_contract.py -q`          |
| A4-P3-001 | P3  | fetch.schema_hash 占位无 ponytail | `tier_a_live_acceptance.py:447`                                                                 | `sha256(source_id)` 非真实 schema hash；无 `ponytail:` 注释说明天花板 | 加 `ponytail:` 注释（或接 raw bundle schema_hash）；文档说明与 raw_evidence 对齐路径                                                   | 读 `_build_fetch_block` 注释；若有真实 hash 则单测断言非 source_id 派生 |

已对抗搜索：acceptance 分类逻辑 · exit code · deribit dispatch · DB 路径同构 · pass 过宽分支 · fetch 子结构 · 双入口 pipeline。
