# Audit A8 — 测试缺口 / pytest（R3-DCP-09）

| 元信息   | 值                                              |
| -------- | ----------------------------------------------- |
| 维度     | A8 QA — Red Flags · 测试契约 · `uv run pytest -q` |
| 任务     | `07-02-wave4-r3-dcp-09-backfill-ci`             |
| 协议     | `plan_protocol_version: 4.1`                    |
| 模板     | `agents/qa-expert.md`                           |
| 审计日期 | 2026-07-02                                      |
| 工作目录 | `quant-monitor-desk-wt-dcp09`                   |

> **AUDIT.plan §2 A8：** `uv run pytest -q`（Audit 须 `--basetemp=<task>/.audit-sandbox/pytest`，见 `testing-guidelines` §9）

---

## 维度证据 §3.8

### 1. 独立 pytest 复跑

| 步骤 | 命令 | exit | 关键证据 |
| ---- | ---- | ---- | -------- |
| 全量（A8 口径） | `mkdir -p .trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/.audit-sandbox/pytest` 后 `uv run pytest -q --basetemp=".trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/.audit-sandbox/pytest" --tb=no` | **1** | **14 FAILED**（无 collection ERROR）；含 DCP-09 `test_qmd_data_backfill_without_dry_run_requires_sandbox` |
| DCP-09 切片子集 | `uv run pytest tests/test_bounded_backfill_cap.py tests/test_qmd_data_backfill_cli.py tests/test_bounded_backfill_cli_e2e.py tests/test_wave3_isolated_acceptance_quick_profile.py tests/test_nightly_ci_manifest.py tests/test_wave3_live_acceptance_findings_gate.py tests/test_r3_dcp09_registry_closure.py tests/test_sync_orchestrator.py -k backfill -q --basetemp=.../pytest-dcp09` | **1** | 14 collected，**13 passed，1 failed**（同上 sandbox 测） |
| basetemp 对抗复现 | 同一测 `test_qmd_data_backfill_without_dry_run_requires_sandbox`：无 `--basetemp` → **pass**；`--basetemp=.../.audit-sandbox/pytest-compare` → **fail**（stderr `SYNC_FAILED`，非 `USER_AUTH_REQUIRED`） | — | `tmp_path` 落在 `.audit-sandbox/...` 内时，`QMD_DATA_ROOT=tmp_path/data` 的 `resolve().parts` 仍含 `.audit-sandbox`，gate 误放行 |

**注：** 首次未预建 `.audit-sandbox/pytest` 目录时，全量跑出现大量 `FileNotFoundError` collection/setup ERROR（WinError 3）；预建目录后 ERROR 消失，仅剩 FAILED。A8 审计以预建目录后的全量结果为准。

### 2. Red Flag / 切片 AC ↔ 测试追溯

| Red Flag / 切片 AC | 建议/现有测试 | 覆盖 | 缺口 |
| ------------------ | ------------- | ---- | ---- |
| **S00** cap + `plan_backfill_shards` | `test_bounded_backfill_cap.py`（4 测） | fail-closed · truncate planner · YAML SSOT | **无** CLI `--truncate-to-cap` 路径测；**无** `max_shards>12` → `INVALID_INPUT` CLI 测 |
| **S01** `qmd data backfill` CLI | `test_qmd_data_backfill_cli.py`（3 测） | dry-run JSON · cap exceeded · 非 dry-run gate | `test_qmd_data_backfill_without_dry_run_requires_sandbox` 在 A8 basetemp 下**不证明**「非 sandbox 拒写」 |
| **S02** replay e2e 隔离库 | `test_bounded_backfill_cli_e2e.py` | 2+ shards · SHARD_COMPLETE · 幂等 | — |
| **S03** `--quick` <5min | `test_wave3_isolated_acceptance_quick_profile.py` | step 列表无 `pytest_full` | **未**断言耗时 <5min（活卡 / S03 AC） |
| **S04** nightly manifest | `test_nightly_ci_manifest.py` | workflow_dispatch · `--run-network` · node id 子串 | 仅子串断言（可接受为 manifest smoke；无 YAML 结构解析） |
| **S05** findings severity gate | `test_wave3_live_acceptance_findings_gate.py`（2 测） | HIGH/CRITICAL · EXPECTED_DEFER · MEDIUM pass | — |
| **S06** 四台账 ID 关账 | `test_r3_dcp09_registry_closure.py` | ID 与 R3-DCP-09 字符串存在 | 未逐 ID 断言关账行语义（仅 `in pending` + 泛化 `关账`/`CLOSED`） |
| **INDEX §2** backfill runner 回归 | `test_sync_orchestrator.py -k backfill` | 分片 · ResourceGuard · 事件 | — |
| **AUDIT.plan §1** 全量绿 | `uv run pytest -q` | — | **未绿**（14 FAILED） |

### 3. 五字段 docstring / 断言质量（DCP-09 新建模块）

| 模块 | 五字段 | 语义断言 |
| ---- | ------ | -------- |
| `test_bounded_backfill_cap.py` | 4/4 有 | 是（cap 值、异常类型、shard 边界） |
| `test_qmd_data_backfill_cli.py` | 3/3 有 | 2/3 强；sandbox 测 stderr 子串弱且 basetemp 下失效 |
| `test_bounded_backfill_cli_e2e.py` | 1/1 有 | 是（DB 行数、事件计数） |
| `test_wave3_isolated_acceptance_quick_profile.py` | 1/1 有 | 是（step 名）；缺耗时 |
| `test_nightly_ci_manifest.py` | 1/1 有 | 子串级（manifest 用途可接受） |
| `test_wave3_live_acceptance_findings_gate.py` | 2/2 有 | 是（计数语义） |
| `test_r3_dcp09_registry_closure.py` | 1/1 有 | 偏弱（presence-only） |

### 4. test_catalog.yaml

DCP-09 七模块均已登记（`test_bounded_backfill_cap` · `test_bounded_backfill_cli_e2e` · `test_qmd_data_backfill_cli` · `test_nightly_ci_manifest` · `test_wave3_isolated_acceptance_quick_profile` · `test_wave3_live_acceptance_findings_gate` · `test_r3_dcp09_registry_closure`），`purpose` / `failure_meaning` 与模块 docstring 一致。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --------- | --- | ---- | ---- | ---- | -------- | ---- |
| A8-P0-001 | P0  | AUDIT.plan A8 门槛 `uv run pytest -q` 未绿 | AUDIT.plan §2 A8 · `EXECUTION_INDEX.md` §2「全量」 | 独立全量跑（A8 basetemp）exit **1**，14 FAILED；含 DCP-09 sandbox 测 | Repair：先修 A8-P1-001；再全量复跑至 exit 0 | `uv run pytest -q --basetemp=".trellis/tasks/07-02-wave4-r3-dcp-09-backfill-ci/.audit-sandbox/pytest"` exit 0 |
| A8-P1-001 | P1  | 非 dry-run sandbox 门禁测与 A8 basetemp 冲突，目的/目标在标准审计环境下不成立 | `tests/test_qmd_data_backfill_cli.py::test_qmd_data_backfill_without_dry_run_requires_sandbox` · `data_commands._require_baostock_sync_operator_or_sandbox:296` | `tmp_path` 在 `--basetemp=.../.audit-sandbox/pytest` 下使 `QMD_DATA_ROOT` 路径 `parts` 含 `.audit-sandbox`；gate 放行后 backfill 真跑并以 `SYNC_FAILED` 失败，断言 `USER_AUTH_REQUIRED`/`sandbox` 失败 | 将 `QMD_DATA_ROOT` 设为**不含** `.audit-sandbox` 的绝对路径（如 `tmp_path.parent.parent / "outside-sandbox-data"` 或 `PROJECT_ROOT / "data"`）；断言 `error_code == USER_AUTH_REQUIRED`（JSON parse stderr）；**不改**测试目的 | 无 basetemp：**仍 pass**；A8 basetemp：**pass** |
| A8-P1-002 | P1  | S00 AC `--truncate-to-cap` CLI 无 pytest | `to-issues-slices.md` S00 · `main.py:60` `--truncate-to-cap` · `plan-spec` / ADR-030 | 仅 planner 层 `test_plan_backfill_shards_respects_max_shards_truncate`；CLI 未覆盖 | 新增 `test_qmd_data_backfill_truncate_to_cap_cli`：超窗 + `--truncate-to-cap` + dry-run → `shard_count≤max_shards` 且 JSON `truncate_to_cap=true` | `uv run pytest tests/test_qmd_data_backfill_cli.py -k truncate -q` |
| A8-P2-001 | P2  | `ABSOLUTE_MAX_BACKFILL_SHARDS=12` CLI 硬顶无测 | `to-issues-slices.md` Cap 表 · `data_commands.backfill_plan:547-555` | 无 `--max-shards 13` 或 `0` 用例 | 新增测：`--max-shards 13` dry-run → `CliFailure` / `INVALID_INPUT` | `uv run pytest tests/test_qmd_data_backfill_cli.py -k max_shards -q` |
| A8-P2-002 | P2  | S03 AC「quick <5min」无计时证据 | `to-issues-slices.md` S03 · `WAVE3-ACC-OPT-01` | `test_wave3_isolated_acceptance_quick_profile` 只验 step 名 | 对 `_build_steps(quick=True)` 各步 mock subprocess 或 marker 测；或文档化 defer 绑后续 perf 任务并在 INDEX §2.1 登记阈值 | `uv run pytest tests/test_wave3_isolated_acceptance_quick_profile.py -q` 扩展后绿 |
| A8-P3-001 | P3  | S06 台账关账测断言偏弱 | `tests/test_r3_dcp09_registry_closure.py` | 仅 `registry_id in pending` + 全局 `关账`/`CLOSED` | 逐 ID 断言表格行含 `R3-DCP-09` + `CLOSED`/`关账`（regex 或结构化解析） | `uv run pytest tests/test_r3_dcp09_registry_closure.py -q` |

---

## 计划外发现

| ID        | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --------- | --- | ---- | ---- | ---- | -------- | ---- |
| A8-P2-003 | P2  | 同源 basetemp 污染导致 baostock/mootdx operator 门禁测在全量 A8 跑法中失败 | `tests/test_qmd_data_sync_baostock.py::test_qmdData_syncBaostock_operatorAuthRequired` · `tests/test_qmd_data_sync_mootdx.py::test_qmdData_syncMootdx_operatorAuthRequired` | 与 A8-P1-001 相同：`tmp_path` 继承 `.audit-sandbox` | 统一修复模式：显式 non-sandbox `QMD_DATA_ROOT`；断言 `USER_AUTH_REQUIRED` | `uv run pytest tests/test_qmd_data_sync_baostock.py tests/test_qmd_data_sync_mootdx.py -k operatorAuth -q --basetemp=.../.audit-sandbox/pytest` |
| A8-P3-002 | P3  | 全量 14 FAIL 中多数非 DCP-09 切片（adapter/layer1/ops probe 等） | 全量 short summary · `tests/test_adapter_skeletons.py` 等 | basetemp 下路径/产物缺失或环境 flake（与 DCP-09 实现无直接因果） | Repair 各模块 owner 按失败栈修 fixture 路径或 basetemp 兼容；或阶段外置绑非 DCP-09 任务 | 同 A8-P0-001 全量命令 exit 0 |

已对抗搜索：`tests/test_*backfill*` · `tests/test_qmd_data_backfill_cli.py` · `tests/test_nightly_ci_manifest.py` · `tests/test_wave3_*` · `tests/test_r3_dcp09_registry_closure.py` · `tests/test_sync_orchestrator.py -k backfill` · `backend/app/cli/data_commands.py`（`truncate_to_cap` / `ABSOLUTE_MAX_BACKFILL_SHARDS`）· `to-issues-slices.md` 全切片表 · `test_catalog.yaml` DCP-09 条目 · AUDIT.plan §2 A8 · A7 `audit-a7-report.md`（fingerprint / basetemp 交叉项未重复开 P1，仅 A8 测缺口视角引用 basetemp 行为）。
