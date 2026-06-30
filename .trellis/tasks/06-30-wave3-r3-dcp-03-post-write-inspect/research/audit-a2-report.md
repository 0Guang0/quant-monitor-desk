# Audit A2 — 可读性 / ponytail

## 元信息

| 字段 | 值 |
| ---- | -- |
| 维度 | A2 可读性 / ponytail |
| 任务 | `06-30-wave3-r3-dcp-03-post-write-inspect` |
| `plan_protocol_version` | 4.1 |
| 模板 | `agents/audit-a2-ponytail.md` |
| 日期 | 2026-06-30 |
| worktree | `C:\Users\Guang\Desktop\quant-monitor-desk-wt-dcp03` |
| 分支 | `feature/wave3-r3-dcp-03-post-write-inspect` |

---

## 维度证据

### Boot / diff

| 项 | 结果 |
| -- | ---- |
| `git diff --stat`（工作区） | `tests/test_catalog.yaml` 705 行 churn（登记新测）；**待提交** `tests/test_incremental_post_write_inspect.py`（131 行）、`tests/post_write_inspect_support.py`（202 行）为 `??` 未跟踪 |
| 任务测试净增（估） | ~333 行（131 + 202）；support 模块占 ~61% |
| AUDIT.plan A2 范围 | 五字段 docstring；参考/仓内注释分明；无重复 inspect 实现 |
| 审阅文件 | `tests/test_incremental_post_write_inspect.py`、`tests/post_write_inspect_support.py`、`research/execute-reference-read-evidence.md`、`research/reference-adoption-dcp03.md`（主仓 `.trellis/tasks/...`） |

### A2 checklist

- [x] `git diff --stat` 已记录（工作区 + 未跟踪新文件行数）
- [x] 每候选附 `file:line` + ponytail 梯级
- [ ] 与 A4 过度抽象交叉引用 — 无 A4 级新抽象；CLI helper 重复属测试样板，非 adapter 层
- [x] 阻塞 vs 建议已区分（P2 = Repair 必修）

### §3.2 候选删改追溯

| 候选删改（file:line） | ponytail 梯级 | 备注 |
| --------------------- | ------------- | ---- |
| `post_write_inspect_support.py:25-72` 与 `test_baostock_incremental_e2e.py:25-74` 增量 bootstrap 栈 | 梯级 2（复用） | ~48 行近乎逐字复制；`reference-adoption-dcp03.md` §1 已指 baostock e2e 为编排样板 |
| `test_incremental_post_write_inspect.py:36-38` `_run_qmd_db_inspect_cli` | 梯级 2（复用） | 与 `test_ops_db_inspector.py:56-58` 逐字相同；§1 已指巡检契约为 CLI 样板 |
| `test_incremental_post_write_inspect.py:48-62` vs `post_write_inspect_support.py:79-93` | 梯级 2（复用） | 测试 1 需「第一次增量后 inspect」故不能整段调用 `run_two_incremental`；setup 块仍可抽 `prepare_incremental_session` |
| `post_write_inspect_support.py:136-201` `build_evidence_bundle_from_fetch_log` | 梯级 6（新代码） | `reference-adoption-dcp03.md` §4.B 显式 AC；非 good_bundle 偷换；**保留** |
| `backend/app/ops/db_inspector.py` 调用 | 梯级 2（复用） | 无重复 inspect **实现**；仅测试编排 |

### 五字段 docstring

| 测试 | 五字段 |
| ---- | ------ |
| `test_postWriteInspect_twoIncremental_rowCountStable` | ✓ 覆盖/对象/目的/验证/失败 |
| `test_postWriteHealth_twoIncremental_marketBarP0` | ✓ |
| `test_postWriteCli_dbInspect_jsonIncludesSecurityBar1d` | ✓ |

`post_write_inspect_support.py` 无 `test_*`；模块 docstring 标明 R3-DCP-03 用途，合规。

### 参考采纳 vs 仓内复用

| 检查 | 结果 |
| ---- | ---- |
| 测试代码标 L1/L2/L3 | 无 |
| `execute-reference-read-evidence.md` §1 仅外部参考 | ✓；仓内路径在 §2「仓内复用」 |
| `reference-adoption-dcp03.md` §0 术语铁律 | ✓；与 execute 证据 §3 自检一致 |
| runtime 依赖 `参考项目/**` | 无 |

### `_run_qmd_db_inspect_cli` vs `test_ops_db_inspector`

| 对比项 | 结论 |
| ------ | ---- |
| 实现 | **逐字重复**（`sys.executable` + `qmd_ops.py db-inspect` + `subprocess.run`） |
| DbInspector 逻辑 | **未重复**；新测仅 CLI smoke |
| 现有 `_parse_cli_json` | 新测内联 `json.loads`；可复用但未构成第二处 inspect 实现 |
| ponytail | 应抽 `tests/support/qmd_ops_cli.py` 或从既有模块 import，而非第三份拷贝 |

### DOUBT（≥20 行可简化）

**有。** 搜索范围：`tests/post_write_inspect_support.py`、`tests/test_baostock_incremental_e2e.py`、`tests/test_ops_db_inspector.py`、`tests/test_incremental_post_write_inspect.py`；`grep` `_run_qmd_db_inspect_cli` / `bootstrap_db` / `DbInspector(` 全 `tests/`。

最深命中：**梯级 2** — baostock incremental bootstrap 栈 ~48 行重复，违反「先复用仓库已有模式」。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A2-P2-01 | P2 | baostock incremental bootstrap 栈 ~48 行重复 | `post_write_inspect_support.py:25-72` · `test_baostock_incremental_e2e.py:25-74` | Execute 从 DCP-01 e2e **拷贝**而非抽取共享 helper；违反 ponytail 梯级 2 与 AUDIT.plan「编排样板」精神 | 抽取 `tests/incremental_baostock_support.py`（或扩展现有 conftest）：`bootstrap_db`、`seed_watermark_row`、`build_service`、`incremental_spec` + 常量；`test_baostock_incremental_e2e.py` 与 `post_write_inspect_support.py` 均 import；`run_two_incremental` 仅保留 DCP-03 特有编排 | `uv run pytest tests/test_baostock_incremental_e2e.py tests/test_incremental_post_write_inspect.py -q` exit 0 |
| A2-P2-02 | P2 | `_run_qmd_db_inspect_cli` 与巡检契约测重复 | `test_incremental_post_write_inspect.py:36-38` · `test_ops_db_inspector.py:56-58` | 第二处拷贝 CLI 子进程包装；`reference-adoption-dcp03.md` §1 已列 `test_ops_db_inspector` 为 CLI 样板 | 将 `_run_qmd_db_inspect_cli`（可选 `_parse_cli_json`）迁至 `tests/support/qmd_ops_cli.py` 或自 `test_ops_db_inspector` 导入；删除 `test_incremental_post_write_inspect.py` 内副本 | `uv run pytest tests/test_ops_db_inspector.py tests/test_incremental_post_write_inspect.py -q` exit 0 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

已对抗搜索：`tests/` 全库 `grep` `class DbInspector`、`def inspect`、`def _run_qmd_db_inspect_cli`；`post_write*` 路径；`research/execute-reference-read-evidence.md` L1/L2/L3 误标仓内路径。**未发现**计划外重复 inspect 实现或参考等级标注错误。

---

## 正面观察（非裁决）

- 三个 `test_*` 五字段 docstring 完整，目的/验证与活卡 S01–S03 对齐。
- `DbInspector` / `run_data_health_profile` / `qmd_ops db-inspect` 均调用仓内生产模块，**无**测试内重写 inspect 逻辑。
- `build_evidence_bundle_from_fetch_log` 体量虽大，但对应 `reference-adoption-dcp03.md` §4.B 显式策略，非 YAGNI 膨胀。
- `execute-reference-read-evidence.md` 参考/仓内分区清晰，无把 `backend/` 标成 L1/L2/L3。
