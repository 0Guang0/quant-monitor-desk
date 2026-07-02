# Audit A3 — Security（R3-DCP-10）

> **维：** A3 · **任务：** `07-02-wave4-r3-dcp-10-evidence` · **plan_protocol_version:** 4.1  
> **模板：** `agents/security-auditor.md` · **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp10` · **基线：** `master`

---

## 维度证据

### 1. 审计范围（Trace Authority + diff）

| 类别 | 路径 | A3 相关性 |
| --- | --- | --- |
| 活卡 / frozen | `frozen/R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` | 边界：无 evidence_chain DB · 无 live 真网 AC |
| ADR-031 | `docs/decisions/ADR-031-dcp10-layer5-evidence-provenance-binding.md` | provenance 映射 · 无新 migration |
| ENTRY §2 | `research/00-EXECUTION-ENTRY.md` | 金路径 raw→clean→Layer5 · WriteManager only · 禁止 EasyXT fallback |
| AUDIT.plan §2 A3 | `AUDIT.plan.md` | **无参考 runtime** · **WriteManager 金路径** |
| 实现（Execute） | `evidence_bundle.py` · `layer5_evidence/provenance.py` · `test_layer5_provenance_bridge.py` · `test_layer5_mootdx_bar_clean_e2e.py` | 本票安全触面 |
| 契约 | `docs/modules/layer5_security_evidence.md` | 不绕过 WriteManager · 不把 Agent 文本当事实 |

**`git diff master` 生产触面（相对 master 有 diff）：**

- `backend/app/datasources/normalizers/evidence_bundle.py` — 扩展 `bundle_layer5_provenance`（`source_dataset_ids` + `clean_table` 参数）

**Execute 全量触面（分支内已存在、Plan/INDEX 登记）：**

- `backend/app/layer5_evidence/provenance.py`（新建桥接）
- `tests/test_layer5_provenance_bridge.py` · `tests/test_layer5_mootdx_bar_clean_e2e.py`

相对 `master` 其余 DCP-10 文件无 diff（已在共同基线或同内容）；A3 对 **Execute 登记触面 + diff** 做静态审查，不以 diff 大小缩减威胁面。

---

### 2. GitNexus（必用）

| 调用 | 结果 | 审计用途 |
| --- | --- | --- |
| `query(repo=quant-monitor-desk, "layer5 provenance bundle_layer5_provenance…")` | 命中 `EvidenceFoundationValidator` · `_validate_provenance_traceable` · `Layer5LineageBuilder` · `IncrementalJobRunner.run` | 确认 DCP-10 落在既有 Layer5 校验链 + sync 写路径，非孤立 helper |
| `query(repo=quant-monitor-desk, "EvidenceFoundationValidator provenance staged")` | 同上 + `IncrementalJobRunner.run` → `Redact_error_message` / `_is_allowed` | 对抗：staging/跑数路径仍经 gate |
| `context(repo=quant-monitor-desk, "_validate_provenance_traceable")` | 唯一入边：`EvidenceFoundationValidator._validate_kind_provenance` | fail-closed 校验为 Layer5 事实类必经 |
| `impact(bundle_layer5_provenance)` | **Symbol not found**（索引未收录新/小 symbol） | 与 Plan `gitnexus-summary.md` §1b 一致；已用手工 caller trace 补证 |

**索引备注：** `build_source_provenance_from_bundle` / `bundle_layer5_provenance` 未入 GitNexus 图；不影响本维结论——caller 链已通过 `rg` + 读码 + 上表 query 独立复验。

---

### 3. 静态基线 `rg`（DCP-10 触面）

**命令与范围：** `backend/app/layer5_evidence/**` · `backend/app/datasources/normalizers/evidence_bundle.py` · `tests/test_layer5_provenance_bridge.py` · `tests/test_layer5_mootdx_bar_clean_e2e.py`

| 模式 | 结果 |
| --- | --- |
| `https?://\|api_key\|secret\|token\|password\|Bearer\|JWT` | **0 命中**（生产触面） |
| `f\".*SELECT\|execute(f` | **0 命中** |
| `subprocess\|os.system\|eval(\|exec(` | **0 命中** |
| `参考项目\|import.*easyxt` | **0 命中** |
| `writer(\|apply_migrations\|INSERT \|UPDATE \|DELETE ` in `provenance.py` / `evidence_bundle.py` | **0 命中**（桥接层无 DB 写） |

全仓基线（`backend/` 非 test）存在既有 `f"...SELECT {table}"` 模式（表名来自内部常量/quote_ident），**不在本票 diff/触面**；未引入新 SQL 拼接面。

---

### 4. AUDIT.plan §2 A3 要点对照

#### 4.1 无参考 runtime

| 检查 | 证据 | 结论 |
| --- | --- | --- |
| 生产代码无 `参考项目/**` import | `rg` 0 命中；`provenance.py` / `evidence_bundle.py` 仅 QMD 仓内 import | **满足** |
| EasyXT forbidden 未渗入 Layer5 桥接 | 桥接仅读 bundle dict → `SourceProvenance`；无 fallback/换源逻辑 | **满足** |
| Execute 参考读证 | `execute-reference-read-evidence.md` 声明 digital-oracle/EasyXT **树不在 worktree**，仅纪律对齐 | **满足** |

#### 4.2 WriteManager 金路径

| 路径 | 写库方式 | 证据 |
| --- | --- | --- |
| `layer5_evidence/provenance.py` | **无写** | 纯映射；`rg writer(` 0 命中 |
| `bundle_layer5_provenance` | **无写** | 纯 dict → tuple 构造 |
| S02 e2e `test_layer5_mootdx_bar_clean_e2e.py` | `ConnectionManager.writer()` + `DataSyncOrchestrator.run_incremental` | `incremental_mootdx_support.bootstrap_db` L23–24 `cm.writer()`；`runners.py` L282 `WriteRequest` 经 `_write_clean` |
| mootdx fetch | `use_mock=True` | `incremental_mootdx_support` L43；不经 live gate（ADR-027 对齐） |
| ADR-031「无 evidence_chain DB」 | 无 migration / 无 Layer5 表 INSERT | 实现与 ADR 一致 |

e2e 测试内 `seed_watermark_row` 使用 `con.execute(INSERT…)` 属于 **tmp_path 测试 bootstrap**（`AUDIT.plan` A7 tmp_path 隔离范畴），生产增量写仍经 orchestrator → WriteRequest。

#### 4.3 信任边界与 fail-closed

| 边界 | 行为 | 锚点 |
| --- | --- | --- |
| bundle 读入 | `read_cn_market_evidence_bundle` 缺 `source_fetch_id` / `content_hash` → `CnMarketEvidenceError` | `cn_market.py` L147–150 |
| Layer5 桥接 | `build_source_provenance_from_bundle` 缺 fetch_id 或 content_hash → `ValueError` | `provenance.py` L19–22 |
| 单测负向 | `test_layer5Provenance_missingFetchId_raises` | `test_layer5_provenance_bridge.py` L84–101 |
| Foundation 校验 | `_validate_provenance_traceable` 要求 fetch 或 hash；`source_dataset_ids` 拒 agent 文本模式 | `foundation.py` L104–114 |
| `clean_table` 参数 | 默认常量 `security_bar_1d`；仅写入 `source_dataset_ids` 字符串，**不进 SQL** | `evidence_bundle.py` L102–117 |

**旁路说明（计划外已搜）：** 遗留 `cn_market_bundle_layer5_provenance` 仍直调 `bundle_layer5_provenance` 且无 bridge 双字段校验；但 **读路径** `read_cn_market_evidence_bundle` 已 fail-closed，且 DCP-10 金路径强制 `build_source_provenance_from_bundle`。属既有 wrapper 模式，本票未扩大写面或引入新 runtime 耦合。

---

### 5. DOUBT 三类隐蔽威胁

| 类 | 搜索范围 | 结论 |
| --- | --- | --- |
| **1. 硬编码 URL 变体** | DCP-10 触面 + `mootdx_port`（e2e 依赖） | **无发现** — 触面 0 URL；mootdx 默认 mock replay |
| **2. JWT / API key 模式** | DCP-10 触面 `rg` | **无发现** — 0 命中；密钥仍仅 env 读取（全仓既有 port，非本票新增） |
| **3. SQL 拼接** | DCP-10 触面 | **无发现** — 桥接/helper 无 SQL；e2e 读 clean 用参数化 `?`（`test_layer5_mootdx_bar_clean_e2e.py` L70–76） |

---

### 6. 独立复验（不以文档自述为 PASS）

```bash
uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q
# 结果：4 passed（exit 0）
```

---

### 7. 威胁面摘要（§3.3）

| 威胁 | 发现 | P | 证据 |
| --- | --- | --- | --- |
| 参考 runtime 耦合 | 无 | — | `rg 参考项目` 触面 0；ENTRY §2 禁止 EasyXT |
| 未授权写库 / 绕过 WriteManager | 无 | — | 桥接无写；e2e → `WriteRequest` |
| 明文密钥进 repo | 无 | — | 触面 `rg` 0 |
| SQL 注入新面 | 无 | — | 触面无 `execute(f` |
| 无 provenance 冒充事实 | 无（本票收紧） | — | bridge fail-closed + foundation 校验 + 单测 |
| 未授权 live 源 | 无 | — | e2e `use_mock=True` |

---

## §维度裁决

**PASS**

依据：`§计划内问题` 与 `§计划外发现` 均为占位行；上表 checklist 与 DOUBT 三类均已执行且有可复现证据。

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

已对抗搜索：DCP-10 Execute 触面（`evidence_bundle.py` · `layer5_evidence/provenance.py` · S01/S02 测试）+ `cn_market.read_cn_market_evidence_bundle` 读路径 + `mootdx_port` e2e 依赖 + GitNexus `query`×2 / `context`×1；全仓 SQL/密钥/参考项目基线对照；计划未写的 mutation/bypass（legacy `cn_market_bundle_layer5_provenance` 直调、`clean_table` 元数据注入）已逐项排除或判定为既有模式且本票未扩大攻击面。
