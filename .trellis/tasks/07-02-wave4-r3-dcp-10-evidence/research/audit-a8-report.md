# Audit A8 — R3-DCP-10 测试缺口（test-gap only）

> **维：** A8 · **任务：** `07-02-wave4-r3-dcp-10-evidence` · **协议：** v4.1  
> **模板：** `agents/qa-expert.md` · **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp10`

---

## 维度证据

### 独立复验命令与结果

| 命令 | 结果 | 备注 |
| --- | --- | --- |
| `uv run pytest -q`（默认 tmp） | **exit 0** | 全量约 4.5min，无失败 |
| `uv run pytest -q --basetemp=.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/.audit-sandbox/pytest` | **exit 1** | 须先 `mkdir` sandbox；S02 等因路径过长失败 |
| `uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py -q` | **exit 0**（无 basetemp） | DCP-10 相关 14 项全绿 |
| 同上 + audit `--basetemp` | **exit 1** | `test_mootdxBarClean_layer5Provenance_matchesSameRunBundle` FAIL |

Execute 自述 `research/execute-evidence/s02-green.txt` 声称 S02 绿；**独立复验在 audit 规定 basetemp 下失败**。

### Red Flag / 切片 AC 追溯（§3.8）

| Red Flag / AC（来源） | 测试或 defer | 证据 |
| --- | --- | --- |
| ADR-031 P0 竖切 mootdx · sh.600519 · security_bar_1d | `test_layer5_provenance_bridge.py` + `test_layer5_mootdx_bar_clean_e2e.py` | S02 在 audit basetemp 下红 |
| 三哈希 / schema_hash → `source_dataset_ids` | S01 `test_layer5Provenance_finalizeBundle_mapsAdr031Fields` | S02 e2e **未**断言 schema 编码 |
| 非 staged 占位（`fetch-staged-001`） | S01 foundation + S02 `!= fetch-staged-001` | 通过（无 basetemp 时） |
| fail-closed：`source_fetch_id` 缺失 | `test_layer5Provenance_missingFetchId_raises` | 通过 |
| fail-closed：`content_hash` 缺失（digital-oracle / reference-adoption §2.2） | **无** | 见 A8-P2-02 |
| 同 run fetch bundle → Layer5 provenance（EasyXT forbidden） | S02 e2e | 意图覆盖；helper 脆弱 + basetemp 红 |
| replay 关 G5 子集；live optional | ADR-027 / plan-doubt Cycle 3 defer | 无 live pytest（计划内 defer） |
| 无 evidence_chain DB | plan-doubt Cycle 4 out of scope | 无 DB 测（计划内 defer） |
| 不假关 L1–L5 全链 | S03 台账；无全链 pytest | 计划内 defer |

### 五字段 docstring（testing-guidelines §9.1）

DCP-10 新增 4 个 `test_*`（S01×3 + S02×1）均含覆盖范围 / 测试对象 / 目的/目标 / 验证点 / 失败含义。**PASS**。

### test_catalog.yaml

`test_layer5_provenance_bridge.py`、`test_layer5_mootdx_bar_clean_e2e.py` 已登记 purpose。**PASS**。

### 对抗搜索（计划外扫描）

- 阅读 `backend/app/layer5_evidence/provenance.py`、`tests/test_layer5_mootdx_bar_clean_e2e.py::_load_raw_bundle_from_incremental_run`
- debug：`run_incremental` 后 raw 落盘路径为 `raw/raw/baostock/...`，bundle 内 `source_id=mootdx`（路由选 baostock adapter 目录 + mootdx fetch_port 内容）
- Windows 长路径：audit basetemp 下完整路径 >260 字符 → `FileNotFoundError`（glob 命中但 `read_text` 失败）

---

## §维度裁决

**FAIL**

---

## §计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| A8-P0-01 | P0 | S02 e2e 在 audit 规定 `--basetemp` 下失败 | `tests/test_layer5_mootdx_bar_clean_e2e.py::test_mootdxBarClean_layer5Provenance_matchesSameRunBundle` · AUDIT.plan §2 A8 · qa-expert checklist | `tmp_path` 嵌套 `.trellis/tasks/.../.audit-sandbox/pytest/.../raw/raw/baostock/.../{64hex}.json` 超 Windows MAX_PATH；glob 返回路径后 `read_text` FileNotFound | 缩短 basetemp（如 repo 根 `.audit-sandbox/pytest`）或 S02 用 `data_root=tmp_path` 去掉 `raw_root=tmp_path/"raw"` 双层；或 e2e 通过 `FetchResult.raw_file_paths` / job 事件取 bundle 路径，避免深 glob | `uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q --basetemp=.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/.audit-sandbox/pytest` **exit 0** |
| A8-P1-01 | P1 | S02 raw bundle 加载未绑定 mootdx 源目录 | `test_layer5_mootdx_bar_clean_e2e.py::_load_raw_bundle_from_incremental_run` L33–38 | glob `raw/*/cn_equity_daily_bar/{as_of}/*.json` 不筛 `source_id`；增量 run 将 raw 写在 `baostock/` 目录（路由 primary）虽 bundle 内容为 mootdx | glob 改为 `raw/mootdx/...` 或按 `spec.source_id` 过滤；长期：raw_store.save 的 `source` 应与 `req.source_id` 一致 | 同上 + debug 脚本确认路径含 `mootdx`；e2e 绿 |
| A8-P2-01 | P2 | S02 e2e 未断言 schema_hash / source_dataset_ids 三件套 | `to-issues-slices.md` S02 AC「source_fetch_id + content_hash + schema_hash match bundle」· ADR-031 | e2e 仅断言 `source_fetch_ids` / `source_content_hashes`；schema 编码仅在 S01 单测 | 在 S02 增加与 S01 相同的 `source_dataset_ids` 断言（`schema:{hash}@...` 等） | `uv run pytest tests/test_layer5_mootdx_bar_clean_e2e.py -q` 绿且断言覆盖三字段 |

---

## §计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| A8-P2-02 | P2 | 缺 content_hash 空值 fail-closed 单测 | `provenance.py` L21–22 · reference-adoption-dcp10.md §2.2 | 仅有 `test_layer5Provenance_missingFetchId_raises`；`content_hash` 空串未测 | 新增 `test_layer5Provenance_missingContentHash_raises`（`pytest.raises(ValueError, match="content_hash")`） | `uv run pytest tests/test_layer5_provenance_bridge.py -q` 绿 |
| A8-P3-01 | P3 | audit sandbox 父目录未 bootstrap 时全量 pytest 大规模 ERROR | qa-expert「`--basetemp=<task>/.audit-sandbox/pytest`」 | pytest `mkdir` 无 `parents=True` 时父路径不存在 → 全库 setup ERROR | Repair 或 CI 前置 `New-Item -Force` 创建 `.audit-sandbox/pytest`；或 conftest `pytest_configure` 确保目录 | 空 clone 下 `uv run pytest -q --basetemp=...` 非 ERROR 风暴 |

已对抗搜索：`tests/test_layer5_*.py`、`tests/test_mootdx_incremental_e2e.py`、`backend/app/layer5_evidence/provenance.py`、增量 run raw 落盘路径、Windows basetemp 长路径、test_catalog、五字段门禁、plan-doubt-review Cycle 1–5。
