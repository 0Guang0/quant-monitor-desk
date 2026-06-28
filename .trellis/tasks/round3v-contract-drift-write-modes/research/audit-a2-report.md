# A2 Ponytail Audit — B3V-OPS Contract Drift & Write Modes

> **Task:** `round3v-contract-drift-write-modes` · Playbook `B3V-OPS` / `B3V-C01`  
> **Agent:** audit-ponytail (A2) · **只读**  
> **Worktree:** `quant-monitor-desk-wt-b3v-ops`  
> **审阅提交:** `master` @ `e81e430e` — `fix(b3v-ops): close contract drift audit findings with zero OPEN`  
> **Authority:** `agents/audit-a2-ponytail.md` + `agents/audit-adversarial-authority.md` + `AUDIT.plan.md`  
> **Skills:** ponytail ladder（`ponytail-review` skill 文件不在 worktree；按 `.cursor/rules/ponytail.mdc` + MASTER §0.3a 内联应用）  
> **AC 对照:** `B02_01_contract_drift_and_write_modes.md` · MASTER §2 / §9

---

## Verdict: **PASS**

生产路径 `db_inspector.py` **净减 19 行**（删硬编码常量、YAML SSOT loader），符合 MASTER §0.3a「优先 YAML loader 删重复常量」。`write_contract.yaml` +7 行与 `test_contract_drift_ops_write.py` +123 行为任务卡 explicit AC（漂移/parity/reserved 早拒），非计划外框架。**阻塞项 0**；下列均为可选收缩（建议级）。

---

## git diff --stat（A2 checklist）

**范围：** `e81e430e` 生产/契约/测试 diff（不含 `.trellis/tasks/**` 任务元数据）

| 文件 | Δ 行 |
|------|------|
| `backend/app/ops/db_inspector.py` | +41 / −64，**net −19** |
| `specs/contracts/write_contract.yaml` | +7 |
| `tests/test_catalog.yaml` | +14 |
| `tests/test_contract_drift_ops_write.py` | +123（新文件） |
| **合计** | **+185 / −64，net +121** |

**MASTER §8 / §9 触及文件：** `ops_db_inspect_contract.yaml`（只读 SSOT，本 commit 无 diff）、`db_inspector.py`、`write_contract.yaml`、`test_contract_drift_ops_write.py`、`test_ops_db_inspector.py`（回归，无 diff）、`test_write_manager.py`（回归，无 diff）— 与 diff 一致，无计划外生产路径。

---

## DOUBT（≥20 行可简化？）

| 攻击 | 和解 |
|------|------|
| 「`db_inspector` loader +28 行 helper 是否新抽象膨胀？」 | 替换 ~64 行重复 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` 字面量；**净减 19 行**；`_deferred_mapping_from_contract` 被 runtime + 漂移测双消费（非单调用 wrapper） |
| 「新测 +123 行是否 setup 膨胀？」 | **部分成立** — `_write_setup` / `_write_req`（L75–100）与 `test_write_manager.py` `_setup` / `_req` 结构重复 ~26 行，可复用（见 A2-02） |
| 「`_load_ops_inspect_contract` 是否多余一层？」 | 2 行单行 wrapper，可内联至 L51；未达 ≥20 行阈值 |
| 「reserved 行为测是否与 `test_write_unsupportedMode_raises` 重复？」 | 任务卡 §6 要求 **全部** reserved 模式无写副作用；现有测契约驱动 + 逐模式 COUNT 断言，purpose 不同，**不可删** |

**DOUBT 结论：** 至少 **1 处** ≥20 行可简化（测试 setup 重复）；**生产代码无** ≥20 行且无 AC 依据的整块可删。

---

## §3.2 候选删改表

| 候选删改（file:line） | ponytail 梯级 | 是否阻塞 |
|----------------------|---------------|----------|
| `tests/test_contract_drift_ops_write.py:75-100` — `_write_setup` + `_write_req` 与 `tests/test_write_manager.py:25-64` 重复（migration + staging INSERT + `WriteRequest` 字段块） | 梯级 2（复用既有 `_setup` + `_empty_clean_table` + `_req`，或抽到 `tests/db_helpers.py`） | 建议 |
| `tests/test_contract_drift_ops_write.py:27-28` — `_load_yaml` 与 `db_inspector._load_ops_inspect_contract` 同型 | 梯级 2（测试可读 `db_inspector` 私有 loader 或共享 1 行 helper） | 建议（<20 行，附 A2-02） |
| `backend/app/ops/db_inspector.py:20-21` — `_load_ops_inspect_contract` 仅包装 `read_text` + `safe_load` | 梯级 5（内联至 L51 `_contract = yaml.safe_load(...)`） | 建议（<20 行） |
| `tests/test_contract_drift_ops_write.py:53-72` — `implementedModes` / `reservedModes` 两条 parity 测结构相同 | 梯级 5（`@pytest.mark.parametrize` 合并，估 −8 行，未达 20） | 建议 |
| `tests/test_contract_drift_ops_write.py:115-123` — 循环内重复 `COUNT(*)` 断言块 | 梯级 2（`pytest.raises` 外只断言一次 before/after；与 A4-O 重叠） | 建议（与 A4 交叉） |
| `backend/app/ops/db_inspector.py:58` — `FUTURE_PHASE_KEY_TABLES` 硬编码 frozenset | 梯级 2（YAML `key_tables` 末两项可派生） | **wont-fix** — 非 VR-OPS SSOT 范围（见计划外 PO-01） |
| `specs/contracts/write_contract.yaml:3-9` — `implemented_modes` / `reserved_modes` +7 行 | 梯级 1（B02-WRITE-01 explicit AC） | **不算** |
| `tests/test_contract_drift_ops_write.py` 五字段 docstring 块 | 梯级 1（MASTER §0.3b / 项目测试纪律） | **不算** |
| `backend/app/ops/db_inspector.py:31-48` — `_deferred_mapping_from_contract` | 梯级 2（测试 import 同一规范化函数，避免测内重复 18 行） | **不算**（DRY 合规） |

---

## 计划外发现（对抗性搜索）

已读：`backend/app/ops/db_inspector.py`（全文件）、`tests/test_contract_drift_ops_write.py`、`tests/test_write_manager.py`（setup 对照）、`specs/contracts/write_contract.yaml`、`specs/contracts/ops_db_inspect_contract.yaml`、`B02_01` §4 forbidden、`MASTER.plan.md` §0 Batch 边界。

| ID | 发现 | 与 MASTER 关系 | 阻塞 |
|----|------|----------------|------|
| PO-01 | `FUTURE_PHASE_KEY_TABLES`（`db_inspector.py:58`）仍为硬编码，未从 YAML 加载 | VR-OPS scope 仅 key_tables + deferred；Batch 5 前瞻清单 | 非阻塞（INFO / wont-fix） |
| PO-02 | Write 路径双 SSOT（YAML + `WriteManager` 类常量）非 loader 统一 | Plan 既定；parity 测为 closure gate | accepted（非 bloat） |
| PO-03 | 无计划外新模块、新依赖、factory/registry 框架 | — | 无 |
| — | live fetch / prod DB 写 / `WriteManager.write` 改动 / registry 三件套编辑 | forbidden 未触及 | 无新发现 |

**计划外 bloat：** 未发现计划外抽象层或仅单调用 wrapper factory。

---

## 与 A4 交叉引用

| A2 项 | A4 可能接续 |
|-------|-------------|
| `test_contract_drift_ops_write.py:115-123` 循环内重复 COUNT 断言 | 脆弱重复断言 / 可提取单次 before-after（A4 可读性） |
| 测试 import `_deferred_mapping_from_contract` 私有符号 | A4 已 CLOSED 为 DRY；A2 同意，非泄漏风险 |
| import-time YAML load（`db_inspector.py:51-55`）无 FileNotFound 容错 | A4 INFO — 契约缺失应 fail-fast；非 A2 删码项 |
| `write_request.write_mode` enum 与 `implemented ∪ reserved` 无 union 测 | A4/A5 hygiene（`adversarial-audit-report` AA-B3V-ADV-02） |

---

## 做得好的地方（ponytail 合规）

- **梯级 1 / YAGNI：** 未实现 reserved 写模式；未改 `WriteManager.write`；无新依赖。
- **梯级 2：** 删除 ~64 行硬编码表清单，改读既有 `ops_db_inspect_contract.yaml`；漂移测 import 同一 `_deferred_mapping_from_contract` 避免双份规范化逻辑。
- **梯级 3：** `yaml.safe_load` + `Path.read_text`（stdlib + 已装 PyYAML）。
- **梯级 7：** `_key_tables_from_contract` L26–27 用 `quote_ident` fail-fast，等价于标注 loader 天花板（坏表名 import 即炸）。
- **删多于增：** 生产文件 net −19 行，符合「最短可用 diff」。

---

## §4.3 / 阻塞队列（A2 贡献）

| ID | Priority | Blocks finish-work? |
|----|----------|---------------------|
| — | — | **No** |

全部 A2 项为 P3 可选收缩或它维（PO-01/02 → 设计接受或 INFO）。**§4.3 count (A2): 0**

---

## 建议收缩（Audit 不应用）

1. **A2-02：** `test_contract_drift_ops_write.py` 复用 `test_write_manager._setup` / `_req`（或 `conftest` / `db_helpers` 共享夹具），估 −20~26 LOC setup。
2. **A2-03：** 内联 `_load_ops_inspect_contract`（−2 LOC）；测试侧删 `_load_yaml` 改读模块 loader（−2 LOC）。
3. **A2-04：** reserved 行为测在 `pytest.raises` 循环外做一次 COUNT 前后对比（−6~8 LOC，purpose 不变）。

**估 optional shrink：** ~28–36 LOC（主要为测试 setup），占 net +121 的 ~24%；生产路径已净减，收缩价值在测试 DRY。

---

## Verification（A2 维度）

| Check | Result |
|-------|--------|
| `git diff --stat` | 已记录（上表） |
| 每候选 file:line + 梯级 | 已列 §3.2 |
| A4 交叉 | 已列 |
| 阻塞 vs 建议 | 阻塞 **0** / 建议 **5** |
| Build / pytest | **未跑**（A2 只读；A8 负责 `AUDIT.plan.md` §1 子集） |

---

*A2 only · model: composer-2.5 · 审 `master` e81e430e · 未执行 A1/A3–A8 · 未改代码*
