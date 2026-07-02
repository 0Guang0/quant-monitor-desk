Audit A6 — 性能（M-DATA-03 Tier A Live）

| 字段                  | 值                                                                                              |
| --------------------- | ----------------------------------------------------------------------------------------------- |
| 维度                  | A6 性能（audit-perf）                                                                           |
| 任务                  | `.trellis/tasks/m-data-03-tier-a-live`                                                          |
| plan_protocol_version | 4.1                                                                                             |
| 模板                  | `agents/performance-engineer.md`                                                                |
| 日期                  | 2026-07-03                                                                                      |
| 焦点                  | 11 源串行验收成本 · network 默认 skip · `ensure_isolated_db` registry sync · 默认 pytest 无回归 |

---

## 维度证据

### Boot / 范围

| 项                              | 证据                                                                                                                                                          |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AUDIT.plan §2 A6 行             | 「registry 三件套（S-MERGE 主会话）」— **非** perf SLO 冻结；本维按派发指令审 perf 四项                                                                       |
| EXECUTION_INDEX §2              | AC 含「各源 e2e `-m network`（默认 `pytest -q` skip）」；**无** §2.1 perf tier / smoke budget                                                                 |
| ENTRY §2 / §3                   | 双轨：`uv run pytest -q` 默认 CI；live 须 `QMD_ALLOW_LIVE_FETCH=1` + `--run-network` 或 acceptance CLI                                                        |
| plan-spec.md Interface Contract | `@pytest.mark.network` 默认 skip；`--quick` = fred+baostock 试点子集                                                                                          |
| ADR-034 §Decision #3            | 默认 replay/mock；live 走 network mark 或 `tier_a_live_acceptance.py`                                                                                         |
| 性能权威（背景）                | `docs/ops/performance_limits.md` — 桌面 eco 模式；**本票未绑定具体阈值**                                                                                      |
| GitNexus 7.pre                  | `research/gitnexus-audit-summary.md`；`query`/`context` 对新符号（`run_acceptance`/`ensure_isolated_db`）**索引未收录**（工作区新增）；以下以代码静态审读为准 |

### §3.6 指标对照（perf checklist）

| 指标                               | 冻结阈值                            | 实测 / 审读                                                                                                                                                                              | 证据（命令 / 锚点）                                                                           | 裁决                                                           |
| ---------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| S-ACCEPT 11 源串行 wall-clock      | **无**（plan 未冻结秒级预算）       | `run_acceptance` 对 `sources` **顺序** `for` 循环；每源 `run_source_live_acceptance` → live fetch + `DbInspector.inspect()`                                                              | `tier_a_live_acceptance.py` L232–255 · `tier_a_live_incremental_dispatch.py` L445–467         | **设计内**；瓶颈为 vendor 网络 I/O，非本地 CPU                 |
| `--quick` 分层                     | plan-spec：nightly 试点子集         | `QUICK_SOURCE_IDS = ("fred", "baostock")`；CLI `--quick` 仅 2 源                                                                                                                         | `tier_a_live_acceptance.py` L19–20 · L127–128 · `scripts/tier_a_live_acceptance.py` L21–25    | **PASS**（显式分层，非 perf 违约）                             |
| 默认 CI 不跑 live network          | ADR-034 #3 · plan-spec L62          | `pyproject.toml` marker `network: … skipped unless --run-network`；`conftest.py` `pytest_collection_modifyitems` 无 flag 则 `pytest.mark.skip`                                           | `pyproject.toml` L48–50 · `tests/conftest.py` L147–162                                        | **PASS**                                                       |
| M-DATA-03 network 用例规模         | 无上限冻结                          | 11 个 `test_*_incremental_e2e.py` 各 **2** 个 `@pytest.mark.network`（≈22）；`test_tier_a_live_harness.py` +2（含 skip smoke）                                                           | `rg '@pytest.mark.network' tests/test_*_incremental_e2e.py`                                   | 默认套件 **全 skip**，不增 CI 真网耗时                         |
| network skip 可证                  | S00-INFRA AC                        | `test_networkMark_skippedInDefaultPytestRun` 子进程跑单测，断言 `skipped`/`SKIPPED`                                                                                                      | `tests/test_tier_a_live_harness.py` L260–284                                                  | **PASS**                                                       |
| `ensure_isolated_db` registry sync | 无每源次数上限                      | **每源**调用：`SourceRegistry().load()` + `sync_to_db(con, tombstone_missing=True)`；11 源全跑时 **≈11 次**全量 YAML→DB upsert                                                           | `tier_a_live_acceptance.py` L132–154 · L175–182（`run_source_live_acceptance`）               | **观察**：重复但本地开销 ≪ 单源 live fetch；无冻结阈值可违     |
| dispatch 重复 migration            | 无                                  | 每源 `_prepare_sandbox` 再次 `apply_migrations`；与 `ensure_isolated_db` 叠加                                                                                                            | `tier_a_live_incremental_dispatch.py` L39–48 · 各 `_run_live_sync` 分支                       | **ponytail 冗余**；idempotent；acceptance opt-in 路径          |
| 默认 `pytest -q` 回归              | INDEX §2「全量 `uv run pytest -q`」 | 新增 **15** 个 harness/dispatch 单测（13 非 network + 2 network 默认 skip）；`isolated_live_data_root` 仅 fixture 请求时实例化；**未**新增无 network 标记的 `@pytest.mark.slow` live e2e | `tests/test_tier_a_live_harness.py`（15 `test_*`）· `tests/test_tier_a_live_dispatch.py`（3） | **无实质回归证据**；全量耗时复验归 A5/A8（`uv run pytest -q`） |
| ResourceGuard / smoke budget       | `performance_limits.md` eco 默认    | 本票 **未改** `test_resource_guard.py` / `production_equivalent_smoke.py`                                                                                                                | gitnexus-audit-summary 变更面                                                                 | **N/A**                                                        |

### 串行验收路径（代码锚点）

```text
run_acceptance (L246-249)
  └─ for sid in sources:                    # 11/11 或 --quick 2
       run_source_live_acceptance
         ├─ ensure_isolated_db             # migrations + registry sync（每源）
         └─ run_tier_a_live_incremental
              ├─ _run_live_sync → _prepare_sandbox  # migrations 再跑 + 真网 fetch
              ├─ DbInspector.inspect()      # 全量 inspect profile
              └─ _clean_row_count
```

共享同一 `data_root` DuckDB；串行避免并发写同一隔离库，符合 ADR-034 隔离语义。墙钟由 **11× vendor RTT** 主导，非本地 registry sync。

### 对抗性扫描（计划外 perf 面）

| 范围                                         | 结论                                  |
| -------------------------------------------- | ------------------------------------- |
| 并行 acceptance / 多 worker                  | 未实现；本票无水平扩展 AC             |
| `DbInspector.inspect` 11× 全 profile         | 本地 SQL/文件探测；无冻结 p95；可接受 |
| `conftest.py` `pytest_configure` 加载 `.env` | 会话级一次；对全套件影响边际          |
| GitNexus 新符号                              | 索引滞后；未阻断静态审读              |

---

## §维度裁决

**SKIP**

**理由：** 本票（M-DATA-03）**未冻结**独立 perf SLO / smoke wall-clock / pytest duration 预算（`EXECUTION_INDEX` 无 perf §2.1；`AUDIT.plan` §2 A6 行为 registry 协调描述，非性能阈值）。所审四项均为 ADR-034 / `plan-spec.md` **显式设计**或 opt-in 验收路径：默认 `pytest -q` 通过 `conftest` 跳过 network；11 源串行 acceptance 仅 `QMD_ALLOW_LIVE_FETCH=1` 下运行；`ensure_isolated_db` 每源 registry sync 为本地重复开销，相对真网 fetch 不构成材料性 perf 风险；新增单测以 mock/契约为主，默认套件不被 live 拖慢。**无 finding。**

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`tier_a_live_acceptance.py` · `tier_a_live_incremental_dispatch.py` · `tests/conftest.py` · `tests/test_tier_a_live_harness.py` · `tests/test_*_incremental_e2e.py` · `pyproject.toml` pytest markers · `docs/ops/performance_limits.md` · `ADR-034` · `plan-spec.md` · `EXECUTION_INDEX.md` §2 · `research/gitnexus-audit-summary.md` · GitNexus `query`/`context`（新符号未索引）。

```

---

**说明：** 当前为 Ask 模式，无法写入 `.trellis/tasks/m-data-03-tier-a-live/research/audit-a6-report.md
```
