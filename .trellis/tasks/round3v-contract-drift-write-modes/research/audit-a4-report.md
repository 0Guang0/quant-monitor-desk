# A4 Code Review — B3V-OPS Contract Drift & Write Modes

| 字段 | 值 |
| ---- | -- |
| 维度 | A4 — Code Quality |
| 模型 | composer-2.5 |
| 审查提交 | `e81e430e` (`fix(b3v-ops): close contract drift audit findings with zero OPEN`) |
| 工作树 | `quant-monitor-desk-wt-b3v-ops` |
| 权威 | `AUDIT.plan.md` · `B02_01_contract_drift_and_write_modes.md` · `agents/code-reviewer.md` |
| 日期 | 2026-06-28 |

## 判定

**PASS — 0 BLOCKING**

变更聚焦契约 SSOT 与漂移门控，生产逻辑最小化；`WriteManager` 未改；B3V 任务域 pytest 子集全绿。存在若干 NON-BLOCKING 质量缺口（见 DOUBT 与计划外发现），不构成合并阻塞。

---

## 审查范围（生产 diff）

| 文件 | 变更性质 |
| ---- | -------- |
| `backend/app/ops/db_inspector.py` | 硬编码 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` → YAML SSOT loader |
| `specs/contracts/write_contract.yaml` | 新增 `implemented_modes` / `reserved_modes` |
| `tests/test_contract_drift_ops_write.py` | 新增 5 条漂移/parity/早拒测 |
| `tests/test_catalog.yaml` | 登记新测试模块 |

其余 50+ 文件为 Trellis 任务工件与证据链，不在 A4 生产代码质量主审范围。

---

## Code review checklist

| 项 | 结果 | 证据 |
| -- | ---- | ---- |
| 无 P0 逻辑/安全阻塞 | ✅ | 只读 inspect 路径未引入 mutation；reserved write 早拒 + 行数不变测 |
| 错误处理可观测 | ⚠️ NON-BLOCKING | import 时空 YAML fail-open（见 DOUBT-01） |
| 风格与邻近模块一致 | ✅ | ponytail：删重复常量、最小 loader；`quote_ident` 校验表名 |
| 测试 purpose 中文五字段 | ✅ | `test_contract_drift_ops_write.py` 全 5 测合规 |
| 判定基于 diff + pytest | ✅ | 任务域 `test_contract_drift_ops_write` + `test_ops_db_inspector` 35 passed / 1 skipped |

---

## 分轴评估

### Logic correctness — PASS

- `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` 由 `ops_db_inspect_contract.yaml` 在模块加载时物化，与删除前硬编码元组语义等价（顺序、条目、rule 规范化 `rule: …` 格式保留）。
- `_key_tables_from_contract` 对每个表名调用 `quote_ident`，在契约层拦截非法 SQL 标识符，优于纯字符串信任。
- `_deferred_mapping_from_contract` 对畸形条目 `raise ValueError`，比旧版静默跳过更安全。
- `write_contract.yaml` 分栏与 `WriteManager.SUPPORTED_MODES` / `UNSUPPORTED_MODES` 当前完全一致；parity 测双向锁定。

### Error handling & resource cleanup — NON-BLOCKING 缺口

- **DOUBT-01**（`db_inspector.py:20-21,51-55`）：`_load_ops_inspect_contract()` 在 import 时同步读盘。缺失文件 → `FileNotFoundError` 阻断整个模块导入（可接受 fail-closed）；**空文件或 `{}`** → `KEY_TABLES=()` 静默降级，inspect 仍可运行但 key_tables 为空，漂移测仅在 CI 跑、不在 import 路径守卫。建议在 loader 对空 `key_tables` 显式 `raise ValueError` 或启动自检。
- import 路径无 try/except 包装，错误信息直接冒泡——对 ops CLI 可接受，但运维排障依赖堆栈而非结构化 `connection_error` 风格。

### Naming & module boundaries — PASS

- loader 函数以 `_` 前缀，模块级常量 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` 保持对外 API 稳定；`layer1_evidence`、`test_ops_db_inspector` 等既有导入无需改动。
- `FUTURE_PHASE_KEY_TABLES`、`REQUIRED_TOP_LEVEL_FIELDS` 仍为硬编码——任务卡 VR-OPS-001 仅要求 key_tables + deferred mapping SSOT，边界合理（见计划外 AA-B3V-ADV-01）。

### Duplication / 过度抽象 — PASS

- 未引入新抽象层或 registry loader 框架；`_deferred_mapping_from_contract` 在测试与 runtime 共用，避免 duplicate 规范化逻辑——符合 ponytail。
- Write 路径维持「YAML 契约 + `WriteManager` 类常量」双 SSOT，由 parity 测闭合，非本 commit 引入的架构债（AA-B3V-ADV-03 accepted）。

### Readability — PASS

- 删除 ~60 行内联常量，契约意图集中到 YAML；loader 约 30 行，可读性优于原硬编码块。

### Security（局部）— PASS

- `db_inspector` diff 无 `writer()` / `INSERT` / 网络调用；路径由 `Path(__file__).resolve().parents[3]` 锚定仓库根，无用户可控路径穿越。
- reserved mode 测验证 `ValueError` 且目标表 `COUNT` 不变，符合 VR-WRITE-001 早拒语义。

### Performance — PASS（A6 SKIP 对齐）

- 模块 import 一次 YAML 读取，对 CLI 冷启动可忽略；无 DuckDB 热路径变更。

### Test review — PASS（任务域）

| 测试 | purpose 合规 | 行为强度 |
| ---- | ------------ | -------- |
| `test_opsInspect_keyTables_matchContract` | ✅ | 全量 tuple 相等，非 tautological |
| `test_opsInspect_deferredMapping_matchContract` | ✅ | 复用 runtime 规范化函数，测真实漂移 |
| `test_writeContract_implementedModes_matchWriteManager` | ✅ | 锁定 SUPPORTED_MODES |
| `test_writeContract_reservedModes_matchUnsupportedModes` | ✅ | 锁定 UNSUPPORTED_MODES（repair A1-F01） |
| `test_writeManager_reservedModes_rejectWithoutWrite` | ✅ | 每 reserved 模式：异常文案 + 无写副作用 |

**缺口（NON-BLOCKING）：** 无测断言 `write_request.fields.write_mode` enum == `implemented_modes ∪ reserved_modes`（AA-B3V-ADV-02）；当前三者手动一致。

**A8 命令复跑（本审）：**

```text
uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py -q
→ 35 passed, 1 skipped, exit 0
```

全量含 `test_write_manager.py` 时本环境出现 1 例与 `stg_foundation_smoke` 相关的既有用例失败，**不在 e81e430e diff 内**，不记为 A4 BLOCKING。

---

## DOUBT（对抗性 · 必填）

| ID | 级别 | 位置 | 发现 | 建议 |
| -- | ---- | ---- | ---- | ---- |
| DOUBT-01 | NON-BLOCKING | `db_inspector.py:20-21,24-27,51-55` | 空/缺失 YAML 时 `or {}` + `raw.get("key_tables") or ()` 导致 **fail-open**（`KEY_TABLES=()`），而非 import 即死 | loader 对空 `key_tables` 显式 `raise ValueError("ops_db_inspect_contract: key_tables required")` |
| DOUBT-02 | NON-BLOCKING | `db_inspector.py:36-48` | `deferred_item_mapping` 依赖 YAML dict 插入序；Python 3.7+ 保序且现有测锁定，但若未来 YAML merge/锚点重排可能静默顺序漂移 | 可选：按 `item_id` 排序物化，或测中加 order-independent 集合断言 |
| DOUBT-03 | NON-BLOCKING | `tests/test_contract_drift_ops_write.py`（缺失） | 无 `implemented ∪ reserved == write_mode enum` hygiene 测 | 未来切片加 1 条元组并集测（AA-B3V-ADV-02 wont-fix 范围外增强） |

**搜索范围：** `db_inspector.py` loader 全路径、`write_contract.yaml` 三分栏、`WriteManager.write` 早拒分支、`test_contract_drift_ops_write.py` 全文件、`test_ops_db_inspector.py` deferred 相关用例。未发现 P0 逻辑洞或 mutation 回归。

---

## 计划外发现

> 已对抗搜索：契约 enum 并集、WriteManager bypass、db_inspector mutation、import 容错边界、`FUTURE_PHASE_KEY_TABLES` 硬编码、test_catalog 格式。

| ID | 级别 | 发现 | 阻塞? | 处置 |
| -- | ---- | ---- | ----- | ---- |
| AA-B3V-ADV-01 | INFO | `FUTURE_PHASE_KEY_TABLES` 仍硬编码 | 否 | wont-fix — 非 VR-OPS SSOT 范围 |
| AA-B3V-ADV-02 | INFO | 无 write_mode enum 并集测 | 否 | wont-fix — MASTER 未列；当前一致 |
| AA-B3V-ADV-03 | INFO | Write 双 SSOT（YAML + 类常量） | 否 | accepted — parity 测闭合 |
| AA-B3V-A4-01 | INFO | import 时空契约 fail-open（= DOUBT-01） | 否 | 建议 follow-up hygiene，非本批 BLOCKING |

**显式声明：** 对抗性搜索未发现新的 BLOCKING OPEN。

---

## §3.4 发现汇总

| 轴 | 发现 | 阻塞? | 证据 |
| -- | ---- | ----- | ---- |
| 正确性 | YAML SSOT loader 与旧硬编码语义等价；parity 测全绿 | 否 | `db_inspector.py:15-55`；`test_contract_drift_ops_write.py` |
| 错误处理 | 空 YAML → 空 `KEY_TABLES` fail-open | 否 | `db_inspector.py:20-21,24-27` |
| 可维护性 | 删重复常量、测试复用 `_deferred_mapping_from_contract` | 否 | diff `db_inspector.py` |
| 安全 | 只读路径无 mutation；表名 `quote_ident` 校验 | 否 | `AUDIT.plan.md` A3 约束对齐 |
| 测试 | 5 条漂移测 purpose 合规；reserved 早拒+无副作用 | 否 | `test_contract_drift_ops_write.py:31-123` |
| 文档/契约 | `write_contract.yaml` 分栏与 runtime 一致 | 否 | `write_contract.yaml:3-9` |
| 技术债 | `REQUIRED_TOP_LEVEL_FIELDS` 未 YAML 化 | 否 | 任务卡 scope 外 |
| 性能 | import 一次 YAML I/O | 否 | A6 SKIP |

---

## 与任务卡 AC 对照

| AC | 状态 | A4 备注 |
| -- | ---- | ------- |
| VR-OPS-001 — YAML SSOT + 漂移测 | ✅ CLOSED | loader + 2 条 inspect 漂移测 |
| VR-WRITE-001 — implemented/reserved 分栏 + parity | ✅ CLOSED | YAML 分栏 + 3 条 write 测 |
| 禁止实现 reserved runtime | ✅ | `WriteManager` 未改 diff |
| 禁止 production DB 写 | ✅ | 测试仅用 tmp_path fixture |

---

## 最终判定

**PASS — 0 BLOCKING**

- 生产 diff 小而准：契约 SSOT + 漂移门控，符合 B3V-OPS 目标与 ponytail/karpathy 惯例。
- NON-BLOCKING：import 时空 YAML fail-open（DOUBT-01）、write_mode enum 并集 hygiene 测缺失（AA-B3V-ADV-02）。
- registry 三件套 defer 由 merge coordinator 处理，不在 A4 代码质量阻塞范围。

*审计员：Audit-A4 · composer-2.5 · 只读 · 未修改生产代码*
