# Audit A5 — AC 完成度 / 台账四 ID / nightly 分层

| 字段     | 值                                                          |
| -------- | ----------------------------------------------------------- |
| 维度     | A5（audit-completion）                                      |
| 任务     | `07-02-wave4-r3-dcp-09-backfill-ci`                         |
| 协议     | `plan_protocol_version: 4.1`                                |
| 工作目录 | `quant-monitor-desk-wt-dcp09` · `feature/wave4-r3-dcp-09-backfill-ci` |
| 审计日期 | 2026-07-02                                                  |
| 权威     | 代码 + 独立 pytest/脚本（不信文档 `[x]` / `sNN-green.txt` 自述） |

---

## 维度证据

### GitNexus 追溯（必用）

| 查询 / context | 结论 |
| -------------- | ---- |
| `query("nightly CI run-network wave3 live acceptance findings gate")` | 命中 `capture_phase3_raw_evidence` → `run_live_pilot_raw_only`（`live_pilot_phase3.py`）；batch275 network 测锚定 phase3 live fetch 链 |
| `context(capture_phase3_raw_evidence)` | 上游 `capture_task_phase3_raw_evidence`；下游 `run_live_pilot_raw_only`、mutation_proof；参与 proc_71–72 等 phase3 流程 |
| `query("wave3_isolated_production_acceptance nightly workflow")` | 关联 `production_gate.main`、live pilot phase3 证据链；脚本符号未入索引（`_build_steps` / `_count_severity_gate_violations` 为 DCP-09 新增，索引滞后） |

### INDEX §2.1 最弱 2 行 — 独立复验

| 原 §2.1 行 | 台账 ID | 独立复跑命令 | exit | 与实现/AC 一致？ |
| ---------- | ------- | ------------ | ---: | ---------------- |
| S04 · nightly `pytest --run-network` batch275 子集绿 | `ACC-LIVE-NETWORK-CI-001` | `QMD_DATA_ROOT=.audit-sandbox/audit-a5-network QMD_ALLOW_LIVE_FETCH=1 uv run pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` | **1** | **否** — S04/to-issues AC 要求 node **绿**；`capture_phase3_raw_evidence` 非 macro 路 fetch `status=FAILED`（assert SUCCESS @ L870） |
| S05 · live acceptance `--fail-on-severity HIGH,CRITICAL` | `ACC-LIVE-ACCEPT-NIGHTLY-001` | `QMD_DATA_ROOT=.audit-sandbox/audit-a5-live-accept QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL` | **1** | **部分** — 门禁逻辑与 nightly.yml 接线一致；`fred_api_key_present: false`，8× step HIGH + `SEVERITY-GATE` CRITICAL（证据 `.audit-sandbox/wave3-live-acceptance-20260702T095719Z/live_acceptance_evidence.json`）。单元测 `test_wave3_live_acceptance_findings_gate*` exit 0 |

### 静态 / 契约 pytest（A5 切片测）

```text
uv run pytest -q tests/test_wave3_isolated_acceptance_quick_profile.py \
  tests/test_nightly_ci_manifest.py \
  tests/test_wave3_live_acceptance_findings_gate.py \
  tests/test_r3_dcp09_registry_closure.py -v
→ 5 passed in 0.15s
```

### PR 仍 skip network（AUDIT.plan §2 A5）

| 检查 | 证据 |
| ---- | ---- |
| `.github/workflows/ci.yml` 无 `--run-network` / `-m network` | `pytest -q --cov=backend --cov-fail-under=85` only |
| `docs/ops/nightly_ci.md` 声明 PR 不跑 network | L3 与 ci.yml 一致 |

### 台账四 ID 关账核对

| 台账 ID | 切片 | 关账条件（INDEX §2.1） | 登记 | 实现锚点 | 审计分 |
| ------- | ---- | ---------------------- | ---- | -------- | -----: |
| `WAVE3-ACC-OPT-01` | S03 | `--quick` 跳过 `pytest_full`；quick <5min | `待修复清单.md` §4 **✅ CLOSED @ R3-DCP-09** | `wave3_isolated_production_acceptance.py` `_build_steps(quick=True)` L67–82；`test_wave3_isolated_acceptance_quick_profile` | **4** |
| `ACC-LIVE-NETWORK-CI-001` | S04 | nightly `--run-network` batch275 子集**绿** | §4 **✅ CLOSED** | `.github/workflows/nightly.yml` L24–30；`test_nightly_ci_manifest`（静态） | **2** |
| `ACC-LIVE-ACCEPT-NIGHTLY-001` | S05 | live acceptance `--fail-on-severity HIGH,CRITICAL` | §4 **✅ CLOSED** | `nightly.yml` L31–37；`wave3_live_production_acceptance.py` L101–126,429+；`test_wave3_live_acceptance_findings_gate` | **4** |
| `LIVE-NETWORK-GATE-001` | S04 | nightly workflow 接 `--run-network` | `待修复清单.md` §8 **✅ CLOSED** | 同 nightly.yml + `docs/ops/nightly_ci.md` | **4** |

**登记缺口：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 R3-DCP-09 行仅列三台账（`WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001`），**未列** `LIVE-NETWORK-GATE-001`。`test_r3_dcp09_registry_closure` 只断言四 ID 出现于 `待修复清单.md`，未逐 ID 断言 roadmap CLOSED 行。

### AC 评分表（1–5 rubric · A5 范围）

| # | 范围 | 分 | 追溯链 | 缺口 |
| - | ---- | -: | ------ | ---- |
| 1 | **S03 / WAVE3-ACC-OPT-01** quick 分层 | **4** | ENTRY §3 · to-issues S03 → `_build_steps` 条件省略 `pytest_full` → `test_wave3_isolated_acceptance_quick_profile` | AC「quick <5min」无计时断言或 CI 预算测 |
| 2 | **S04 / ACC-LIVE-NETWORK-CI-001** network 子集绿 | **2** | manifest 链完整（workflow + doc + 静态测）；**运行时** batch275 live node 独立复验 **FAIL** | 关账条件与 S04 AC 要求「pytest node 绿」未满足 |
| 3 | **S04 / LIVE-NETWORK-GATE-001** nightly 接 network | **4** | `nightly.yml` `workflow_dispatch` + `--run-network`；`nightly_ci.md` 双轨文档 | 依赖 #2 运行时绿，接线本身完整 |
| 4 | **S05 / ACC-LIVE-ACCEPT-NIGHTLY-001** findings 门禁 | **4** | `--fail-on-severity` CLI → `_count_severity_gate_violations`（EXPECTED_DEFER 跳过）→ 2 单元测绿；nightly 第二步接线 | 全脚本在审计环境 exit 1（缺 `FRED_API_KEY` 等）；门禁**行为**符合设计，非 wiring 缺口 |
| 5 | **PR CI 不跑 network** | **5** | `ci.yml` 无 network flag；to-issues L13；ENTRY §2 | — |
| 6 | **S06 四 ID registry 关账** | **3** | `待修复清单.md` §4/§8 四 ID CLOSED；`test_r3_dcp09_registry_closure` | roadmap 缺 `LIVE-NETWORK-GATE-001`；registry 测未覆盖 roadmap 四 ID 齐套 |

### Execute 证据 vs 独立复验

| 文档声称 | 独立复验 |
| -------- | -------- |
| `s04-green.txt`：`GREEN s04 nightly workflow manifest` | manifest 静态测绿；**network pytest 独立复验 exit 1** |
| `s05-green.txt`：`GREEN s05 live acceptance findings gate` | 单元测绿；全脚本 audit 环境 exit 1（环境/依赖项，见 §2.1 表） |
| frozen §9.5–9.6 `[x]` | 接线与契约测存在；#2 AC 运行时未闭环 |

### diff 范围（计划内执行偏差）

工作树含 DCP-09 预期文件：`nightly.yml`、`wave3_*_acceptance.py --quick/--fail-on-severity`、四台账 registry 测、ADR-030 等。未见 A5 范围外 silent 扩 scope（backfill S00–S02 属同票 ENTRY，非 A5 评分主体）。

---

## §维度裁决

**FAIL**

**理由：** §计划内问题含 P1 finding — `ACC-LIVE-NETWORK-CI-001` / S04 AC 要求 batch275 network 子集 pytest **绿**，独立复验 exit 1，与台账「子集绿」关账条件不一致。静态 manifest 与 PR skip 分层达标，不足以抵消运行时 AC 缺口。

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| -- | - | ---- | ---- | ---- | -------- | ---- |
| A5-P1-001 | P1 | batch275 network 子集独立复验 FAIL，与 S04 AC「绿」不符 | `to-issues-slices.md` S04-CI-NIGHTLY AC；INDEX §2.1 `ACC-LIVE-NETWORK-CI-001`；`test_batch275_live_pilot_gate.py` L870 | `capture_phase3_raw_evidence` 非 DISABLED 路 live fetch 返回 `FAILED`；Execute `s04-green.txt` 仅 manifest 绿，未绑定运行时 pytest | Repair：根因修 live fetch（或 documented env gate + nightly secret 矩阵）；复验 network node exit 0；更新关账证据 | `QMD_ALLOW_LIVE_FETCH=1 uv run pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` exit 0 |
| A5-P2-001 | P2 | Execute S04 证据未证明 network pytest 绿 | `research/execute-evidence/s04-green.txt`；frozen §9.5 | 证据文件仅「manifest」自述，与 A5 独立复验不一致（执行偏差） | Repair 补 `s04-green.txt` 或 evidence_index 附 network pytest 输出；禁止仅 manifest 关 ACC-LIVE-NETWORK-CI-001 | 同 A5-P1-001 命令 + 证据落盘 |
| A5-P2-002 | P2 | WAVE3-ACC-OPT-01「quick <5min」无实测 | `to-issues-slices.md` S03 AC；INDEX §2.1 | `test_wave3_isolated_acceptance_quick_profile` 只断言步骤名，未测 elapsed | 增加 quick profile 预算测（或 CI timeout 文档化 + smoke 计时上限） | `uv run python scripts/wave3_isolated_production_acceptance.py --quick` 计时 <300s 或新增 pytest 断言 |
| A5-P3-001 | P3 | roadmap R3-DCP-09 行缺 LIVE-NETWORK-GATE-001 | S06 AC；`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 L328 | S06 要求四 ID 齐套登记，roadmap 仅三 ID | 补 roadmap 行 `LIVE-NETWORK-GATE-001` ✅ | `test_r3_dcp09_registry_closure` 扩展断言 roadmap 四 ID |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| -- | - | ---- | ---- | ---- | -------- | ---- |
| A5-P2-003 | P2 | registry 关账测未覆盖 roadmap 四 ID | `tests/test_r3_dcp09_registry_closure.py` | 仅扫 `待修复清单.md` + 泛化 `R3-DCP-09`/`✅ CLOSED` | 逐 ID assert CLOSED 文案；roadmap 四 ID 齐套 | `uv run pytest tests/test_r3_dcp09_registry_closure.py -q` |

已对抗搜索：`nightly.yml` · `nightly_ci.md` · `ci.yml` · `wave3_isolated_production_acceptance.py` · `wave3_live_production_acceptance.py` · `待修复清单.md` §4/§8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · `test_nightly_ci_manifest.py` · `test_batch275_live_pilot_gate.py` · execute-evidence s04/s05 · GitNexus `capture_phase3_raw_evidence` 调用链。

---

## pytest / 脚本 exit codes（摘要）

```text
A5 切片静态测（4 modules）                    → 0
INDEX §2.1 行1 network batch275（独立）       → 1
INDEX §2.1 行2 live acceptance + severity gate → 1（fred_api_key_present: false）
```
