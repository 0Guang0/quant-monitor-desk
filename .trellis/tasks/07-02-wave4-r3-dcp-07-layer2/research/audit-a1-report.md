# Audit A1 — Spec / trellis-check / Trace Authority

> **维：** A1 (audit-spec)  
> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-07-layer2`  
> **协议：** Plan v4.1（`task.json` · `meta.plan_protocol_version: "4.1"`）  
> **Worktree：** `../quant-monitor-desk-wt-dcp07` · branch `feature/wave4-r3-dcp-07-layer2`  
> **审计日期：** 2026-07-02  
> **模板：** `agents/audit-a1-spec.md` · `agents/audit-finding-schema.md`

---

## 维度证据

### trellis-check 步骤 1–7

| 检查项 | 结果 | 证据 |
| ------ | ---- | ---- |
| **1 变更范围** | PARTIAL | `git status --short`：11 modified + 9 untracked（含 `clean_observation_reader.py`、`test_layer2_vix_clean_e2e.py`、`ADR-032`、整包 `.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/`）；`git diff master...HEAD --name-only` → **空**（分支无 DCP-07 commit） |
| **2 任务工件** | PASS | 已 Read `prd.md` · `AUDIT.plan.md` · `frozen/R3_DCP_07_LAYER2_CROSS_ASSET.md` · `research/00-EXECUTION-ENTRY.md` · `research/to-issues-slices.md` · `research/reference-adoption-dcp07.md` · `research/plan-doubt-review.md` · `research/integration-audit.md` |
| **3 包上下文** | PASS | `uv run python ./.trellis/scripts/get_context.py --mode packages` → `Spec layers: backend` |
| **4 Spec Quality** | PASS | 变更限于 `backend/app/layer2_sensors/**` + tests；读 `clean_observation_reader.py` 与 `sensor_loader.py` 对齐 ADR-032 白名单/fail-closed 模式 |
| **5 项目检查** | PASS | 定向：`uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py tests/test_layer2_sensor_loader.py -q` → **43 passed**；全库：`uv run pytest -q` → **exit 0**（~7m22s）；`uv run python scripts/loop_maintain.py` → `OK: loop maintain` |
| **6 跨层** | SKIP | 单包 `layer2_sensors` + DuckDB 读；未触 API/UI 三层链 |
| **7 manifest** | PARTIAL | `check.jsonl` 2 行 · `implement.jsonl` 8 行；实际 diff 含 `MODULE_COMPLETION_RATING.md`、`待修复清单.md`、`test_catalog.yaml` 等未在 jsonl 登记 |

**DCP-07 核心变更文件（工作区，未 commit）：**

```text
backend/app/layer2_sensors/clean_observation_reader.py   (untracked)
backend/app/layer2_sensors/sensor_loader.py              (modified)
backend/app/layer2_sensors/__init__.py                   (modified)
backend/app/layer2_sensors/observation.py                (modified)
backend/app/layer2_sensors/snapshot_builder.py           (modified)
tests/test_layer2_clean_reader.py                        (untracked)
tests/test_layer2_vix_clean_e2e.py                       (untracked)
tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml (untracked)
docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md    (untracked)
```

### diff vs AUDIT.plan / check manifest

| 类别 | 判定 | 证据 |
| ---- | ---- | ---- |
| AUDIT.plan §0.1 活卡 / ADR-032 / ENTRY | PASS（规格一致） | 见 Trace Authority 表 |
| `implement.jsonl` 点名实现文件 | PASS | 8 行均存在于工作区且 pytest 绿 |
| `check.jsonl` 仅 frozen + INDEX | NOTE | 未含 ADR-032 / 新测路径（A1 manifest 覆盖偏薄，非 scope 泄漏） |
| 分支 commit 追溯 | **FAIL** | `master...HEAD` 无 DCP-07 文件；INDEX §1 全 `[x]` 但无 git 对象追溯 |

### Trace Authority（AUDIT.plan §0.1）

| 条目 | 核对问题 | 结果 | 证据 |
| ---- | -------- | ---- | ---- |
| **原始任务卡** | scope/AC/Red Flags 进入 ENTRY/INDEX 或 explicit defer？ | PARTIAL | scope/约束：`00-EXECUTION-ENTRY.md` §1–§2 ↔ 活卡 §1–§6 ↔ ADR-032 一致；活卡头 **仍写** `🔴 OPEN · Plan 阶段`（`R3_DCP_07_LAYER2_CROSS_ASSET.md` L11）；活卡 §5 AC checkbox **仍为 `[ ]`** |
| **task README / input index** | Plan 入口合规？ | PASS | `EXTERNAL-INDEX.md` §A 8 路径齐；`plan-consolidation.md` §5.1 全勾 |
| **unresolved coverage** | 未闭合项有 registry 或 defer？ | PASS | L3–L5 → `待修复清单.md` §4/§8 + DCP-08/10；`B2.5-O-05` → ADR-032 §4 replay default + S02 ledger 阶段外置 |
| **round map** | batch/out-of-scope 与 ENTRY §2 一致？ | PASS | Wave 4 DCP-07；L3–L5 阶段外置 DCP-08/10 + `R3H-05-GATE`；`R3_DCP_TO_ISSUES_INDEX.md` §6.4 L2 `[x]` |
| **source-index** | manifest 血缘完整？ | PASS | `plan-consolidation.md` §5.1 14 文件机械核对；`context_pack.json` 含 `layer2_sensors` |
| **omission-check** | 地图倒查无遗漏？ | PASS | ENTRY §5.1 所列 `research/*` 均存在（含 `reference-adoption-dcp07.md`） |
| **integration-ledger** | context packing 一致？ | PASS | `integration-audit.md` GAP→S00–S02 与 `to-issues-slices.md` 切片表一致 |
| **7.pre gitnexus-audit-summary** | Boot #15 | **FAIL** | `research/gitnexus-audit-summary.md` **不存在**（仅有 Plan 期 `gitnexus-summary.md`） |

### 活卡 / ENTRY / ADR-032 一致性（AUDIT.plan §2 A1 要点）

| 锚点字段 | ADR-032 | ENTRY §2 | 代码/测 | 判定 |
| -------- | ------- | -------- | ------- | ---- |
| P0 asset | `L2-VIX` | ADR-032 行 | `P0_CLEAN_REPLAY_ASSET_IDS` · e2e `asset_id == "L2-VIX"` | PASS |
| instrument | `FRED:VIXCLS` | — | `resolve_clean_db_key` → `VIXCLS` | PASS |
| clean 表 | `axis_observation` / `indicator_id=VIXCLS` | ADR-028 | `clean_observation_reader.py` L129–140 SQL | PASS |
| registry mode | `production_clean_replay` P0 only | to-issues S00 | `sensor_loader.py` L79–86 · L213–214 | PASS |
| 非 staged | 禁止 fixture 冒充 | ENTRY §2 参考铁律 | e2e L110 `staged_fixture not in source`；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` | PASS |
| replay 默认 | tmp_path 种子；无 live FRED | ENTRY §2 数据约束 | `bootstrap_layer1_clean_db` + `seed_macro_series` | PASS |
| double-count | `display_only` 旁证 | plan-doubt Q3 | e2e L128 `LAYER1_AXIS_INPUT_DISPLAY_ONLY` | PASS |

### DOUBT 对抗搜索

| 疑点 | 搜索范围 | 结论 |
| ---- | -------- | ---- |
| plan-doubt-review Q1–Q5 是否进入 ENTRY/ADR | `plan-doubt-review.md` · ENTRY · ADR-032 · S02 ledger | Q1→ADR-032；Q2/Q4/Q5→阶段外置或 replay；Q3→S00 白名单 |
| 活卡 §6 非目标泄漏 | `rg "live.*FRED\|L3.*e2e" backend/app/layer2_sensors` · 新测 | 无 live 网；无 L3 路径 |
| EasyXT fallback | `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` · `test_layer2_clean_reader.py` | fail-closed guard 存在 |
| 参考项目 runtime | `reference-adoption-dcp07.md` §0 + `rg "参考项目" backend/app/layer2_sensors` | 无 import |
| INDEX 声称完成 vs git | `EXECUTION_INDEX.md` §1 `[x]` · `git log` · `git diff master...HEAD` | INDEX 全勾但 **零 commit** |

### GitNexus

| 动作 | 结果 |
| ---- | ---- |
| `query(repo=quant-monitor-desk, "Layer2CleanObservationReader VIXCLS clean read cross asset")` | 返回 `Layer2RollEventWriter` / `IndustryChainLoader` 等邻域流；**未命中** clean reader 主路径 |
| `context(repo=quant-monitor-desk, name=Layer2CleanObservationReader)` | **Symbol not found**（新文件未索引） |
| `context(repo=quant-monitor-desk, name=CrossAssetRegistryLoader)` | found；incoming 仅 `test_layer2_sensor_loader.py` + `__init__.py`（**未含** `test_layer2_vix_clean_e2e.py`） |

**索引说明：** worktree 新/改文件未 commit + 未 `analyze`；A1 以源码 + pytest 验证 ADR-032 绑定，不以 GitNexus 自述为 PASS。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P2-001 | P2 | Execute 完成声明与 git 追溯断裂 | `EXECUTION_INDEX.md` §1 全 `[x]` · `git diff master...HEAD` 空 · `git log -1` = DCP-06 | DCP-07 实现全在工作区，分支 `feature/wave4-r3-dcp-07-layer2` 无专属 commit | 主会话/merge 协调：`git add` DCP-07 允许路径并 commit（含 ADR-032、layer2 实现、测、台账）；禁止 INDEX `[x]` 领先于 commit | `git diff master...HEAD --name-only` 含 `clean_observation_reader.py` 等；`git log -1` message 含 DCP-07 |
| A1-P2-002 | P2 | 活卡状态/AC 与 Execute 台账漂移 | `R3_DCP_07_LAYER2_CROSS_ASSET.md` L11 `Plan 阶段` · §5 全 `[ ]` · `R3_DCP_TO_ISSUES_INDEX.md` §6.4 `[x]` | 活卡未随 Execute/S02 关账同步 | 更新活卡：状态 → Execute/Audit；§5 AC 勾选与 INDEX/to-issues 对齐 | 活卡 §5 与 §6.4 勾选状态一致；头状态非「Plan 阶段」 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A1-P2-003 | P2 | 缺 7.pre `gitnexus-audit-summary.md` | `agents/audit-boot-v4.1.md` Boot #15 · `research/` 目录 listing | 主会话未在派发 A1–A8 前产出 Audit 版 GitNexus 摘要 | 补写 `research/gitnexus-audit-summary.md`：`query`/`context`/`impact` 于 `Layer2CleanObservationReader`、`CrossAssetRegistryLoader`；注明 index stale 与 re-analyze 步骤 | 文件存在；含 DCP-07 新符号查询记录 |
| A1-P3-001 | P3 | GitNexus 未索引 Layer2 clean reader | MCP `context(Layer2CleanObservationReader)` → not found · `query` 无 clean reader 流 | `clean_observation_reader.py` untracked + 未 `node .gitnexus/run.cjs analyze` | commit 后跑 `node .gitnexus/run.cjs analyze`；复验 `context` 返回 defs/callers | `context({name:"Layer2CleanObservationReader"})` status=found |

已对抗搜索：`backend/app/layer2_sensors/**` EasyXT/参考项目 import · live FRED fetch · L3–L5 e2e 泄漏 · `staged_fixture` 冒充 clean · ENTRY §2 不在范围项 — 除上表外未发现额外 scope 泄漏；**活卡/ENTRY/ADR-032 技术绑定在代码层成立**。

---

## A1 checklist 关账

- [x] trellis-check 1–7 有证据（上表）
- [ ] diff vs audit/check manifest — **PARTIAL**（jsonl 薄；核心 implement 行匹配；**commit 追溯 FAIL**）
- [ ] Trace Authority — **PARTIAL**（规格继承 OK；活卡状态/AC 漂移；7.pre 缺失）
- [ ] 无 Plan omission — **FAIL**（git 追溯 · 7.pre · 活卡同步）
- [x] GitNexus ≥1 query + context；已说明索引未覆盖新符号
