# MASTER 计划 — Round 3 Batch 4 `020` Layer 3 Industry Chain Loader

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段 | 值 |
| ---- | -- |
| 任务 slug | `06-23-round3-020-layer3-loader` |
| 分支 | `feature/round3-020-layer3-loader` |
| 前置 | `019` merged；`R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED |
| manifest_protocol_version | `3` |
| analysis_waiver | `false` |
| 原计划 | `research/source-index.md` · `research/original-plan-trace.md` |

### Staged downstream limitations（§16 强制）

1. `BATCH3_STAGED_DOWNSTREAM_GATE.md` — staged-only
2. `R3-B2.75-REQ2-EM` — **DEFERRED**；不得作 live 前提
3. `production_live_pilot_policy.md` — 不解锁生产访问
4. fixture-backed；无 live vendor / production DB writes
5. D-09 — Layer 2–5 不复制 Layer1 全套标准化字段
6. 禁止修改 `snapshot_lineage_contract.yaml`（023A 写权限）

### Failure modes / 回滚

| 场景 | 处理 |
| ---- | ---- |
| contract 校验失败 | `IndustryChainLoadError`；无部分结果 |
| 非 staged mode | 拒绝加载 |
| scope 偏离 | 停止 Execute；回 Plan |
| 回滚 | 删除本分支新增 `layer3_chains/*.py` + tests；无 prod migration |

### 0.1 门控速查

| 项 | 值 |
| -- | -- |
| 怎么测 | §8 RED→GREEN；`tests/test_layer3_loader.py` |
| 怎么验收 | §10 Tier A |
| 什么叫过 | §2 全部 AC + batch3 staged gate 仍绿 |
| prod-path | Tier B：`pytest -q` 全库回归 |
| 6.pre | `research/gitnexus-execute-summary.md` |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail（用户 2026-06-23 追加）

**正式 Execute 全程强制**（非 Audit `ponytail-review`）：

1. **Boot 起** MUST Read `.cursor/rules/ponytail.mdc`（或等价 `/ponytail` skill）；**每个 §8.x 步开始前**重新对照 ladder。
2. **写任何业务代码前**爬 ladder：YAGNI → 复用 `sensor_loader.py` / 现有 util → stdlib → 最小 diff。
3. **禁止**为本任务新增抽象层、未请求 helper、新依赖；有意简化用 `ponytail:` 注释标天花板。
4. **TDD 顺序不变**：RED → karpathy-guidelines → testing-guidelines → **ponytail ladder** → GREEN 实现。
5. 违反 ponytail（过度工程、重复实现、可删未删）→ 停止当前步，删 bloat 后再 GREEN。
6. 每步 GREEN 证据文件须含一行 ponytail self-check：`ponytail: reused <symbol>` 或 `ponytail: no new helper`。

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + ledger pointer 为准。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute SKILL + ponytail（§0.3a）。Phase 0（§0.3 + ledger）→ §8.x（每步 ponytail ladder）→ §10 → Audit。勿 finish-work。
```

---

## 1. 目标

交付 `IndustryChainLoader`：从 staged fixture 加载 chain/anchor/node/edge/cross-chain edge，执行 contract 硬校验，输出 typed `IndustryChainLoadResult`。

### 1.1 目的

为 `021` industry-chain snapshot 提供可审计、可测试的配置加载层。

### 1.2 前置

- `019` Layer2 staged loader merged
- Batch 3 staged gate CLOSED

### 1.3 约束

- staged-only；allowed：`backend/app/layer3_chains/**`、`tests/test_layer3_loader.py`、`tests/fixtures/layer3_*`
- forbidden：layer2/4/5 runtime、datasources/db/ops/validators、lineage contract 写、registry 文件、production DB

### 1.5 停止条件

| # | 事件 | 处理 |
| - | ---- | ---- |
| 1 | Plan 未 freeze / 用户未批准 | 禁止 `task.py start` |
| 2 | 触发 forbidden 路径修改 | 立即停止；revert |
| 3 | RED 非预期全库红 | 停当前 §8 步 |
| 4 | 声称 production-live | 中止；修正 MASTER/AUDIT |
| 5 | 尝试加载非 staged registry 或全量 v1.2 生产路径 | **自定义停损** — 违反 AC-020-5 |
| 6 | `R3-B2.75-REQ2-EM` 被当作 unblock 依据 | 停止；回协调者 |

### 1.6 原计划归并

| 来源 | 内容 |
| ---- | ---- |
| `020_implement_layer3_industry_chain_loader.md` | 五表加载、校验、验收 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4 | Batch 4 边界 |
| `research/worktree-slices.md` | allowed/forbidden |
| 纠偏 | registry 路径见 `source-index.md` §A |

---

## 2. 预期结果（AC）

| ID | 预期结果 | 验证链 |
| -- | -------- | ------ |
| AC-020-1 | 五类 registry 解析为 typed result | §8.2; `test_layer3Loader_loadsStagedFixture_success` |
| AC-020-2 | 唯一性 + 边/节点引用 fail-fast | §8.3–8.5; §5.3 duplicate/edge/cross_chain 用例 |
| AC-020-3 | `event_only` 私有公司非日度价锚 | §8.4; `test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor` |
| AC-020-4 | P0 anchor 须有 `source_keys` | §8.4; `test_layer3Loader_p0Anchor_missingSourceKeys_rejects` |
| AC-020-5 | 仅 `staged_fixture_only` | §8.2; `test_layer3Loader_nonStagedMode_rejects` |
| AC-020-6 | Tier A 门禁 | §10 |

---

## 3. 范围

### 3.1 In scope

- `backend/app/layer3_chains/loader.py`
- `backend/app/layer3_chains/models.py`
- `tests/test_layer3_loader.py`
- `tests/fixtures/layer3_*`（最小 staged 子集）

### 3.2 Out of scope · defer

| 项 | 偿还 |
| -- | ---- |
| `industry_chain_daily_snapshot` | `021` |
| lineage 持久化 | `021`+ |
| `ADV-R3X-LINEAGE-001` 完整 L3/L4 snapshot lineage | `021`+ / Batch 5；registry hygiene 另 slice |
| `layer3_data_dictionary.md`、`references/source_registry.md` 读取 | 非 020 loader 输入（contract 仅五文件） |
| `commodity` vs `public_equity` 语义（模块 doc §8.12.11） | **defer `021`** — 不在 `layer3_loader_contract.yaml` 七条硬规则内 |
| WriteManager DB sync | 可选；非本任务 AC |
| FastAPI / 前端 | Round 4+ |

### 3.3 禁止修改

- `backend/app/layer2_sensors/**` 及其他 layer 包
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/layer3_global_industry_chains/**`（registry 源文件）
- production DB / live fetch

---

## 4. 代码地图

| 路径 | 操作 |
| ---- | ---- |
| `backend/app/layer3_chains/models.py` | 创建 — dataclasses |
| `backend/app/layer3_chains/loader.py` | 创建 — `IndustryChainLoader` |
| `tests/fixtures/layer3_staged_bundle/bundle_manifest.yaml` | 创建 — `loader_mode` + 五文件相对路径 |
| `tests/fixtures/layer3_staged_bundle/` 五数据文件 | 创建 — 对齐 contract `input_files` 最小子集 |
| `tests/test_layer3_loader.py` | 创建 — §5.3 用例 |

---

## 5. 测试契约

### 5.0 规范

1. 注释：`purpose` / `target` / `verifies` / `failure_meaning`（中文）；`verifies` 标注 contract 规则（如 `chain_id unique`）
2. 只 mock 外部 I/O；校验逻辑用真实 fixture 值（`tmp_path` 变异合法 bundle，对齐 019）
3. 每测至少一条业务语义断言
4. 失败路径统一 `pytest.raises(IndustryChainLoadError)` + message 含规则语义（对齐 §0 Failure modes）

### 5.1 测试文件路径

| 路径 | 目标 | 测试目的 | §8 步 |
| ---- | ---- | -------- | ----- |
| `tests/test_layer3_loader.py` | `backend/app/layer3_chains/loader.py` | staged loader + contract 硬规则 | 8.2–8.6 |

### 5.2 成功/失败语义

| 能力 | 成功怎么测 | 失败怎么测 | 场景 |
| ---- | ---------- | ---------- | ---- |
| 五表加载 | fixture 合法 → result 含预期 chain/anchor 计数 | 缺文件/mode 错 → `IndustryChainLoadError` | S1 |
| 图引用 | 边指向存在 node | 悬空 `to_node_id` → 拒绝 | S2 |
| event_only | 私有 event anchor 标记正确 | event_only 当 price anchor → 拒绝 | S3 |
| P0 source | P0 anchor 有 source_keys | 缺 source_keys → 拒绝 | S4 |

### 5.3 用例设计

> contract 七条硬规则 + staged-only + 五表加载；§8 步 RED **仅用本表具名用例**，禁止孤立 `-k` 过滤器。

| 测试文件 | `test_*` 名称 | contract / AC | 断言语义 | §8 |
| -------- | ------------- | ------------- | -------- | --- |
| `tests/test_layer3_loader.py` | `test_layer3Loader_loadsStagedFixture_success` | AC-020-1 | 五类集合非空；`loader_mode==staged_fixture_only` | 8.2 |
| 同上 | `test_layer3Loader_nonStagedMode_rejects` | AC-020-5 | manifest `loader_mode` 非 staged → `IndustryChainLoadError` | 8.2 |
| 同上 | `test_layer3Loader_duplicateChainId_rejects` | chain_id unique | 重复 chain_id 拒绝 | 8.3 |
| 同上 | `test_layer3Loader_duplicateNodeId_rejects` | node_id unique | 重复 node_id 拒绝 | 8.3 |
| 同上 | `test_layer3Loader_duplicateAnchorId_rejects` | anchor_id unique | 重复 anchor_id 拒绝 | 8.3 |
| 同上 | `test_layer3Loader_edgeMissingToNode_rejects` | edge to exists | `to_node_id` 悬空拒绝 | 8.3 |
| 同上 | `test_layer3Loader_edgeMissingFromNode_rejects` | edge from exists | `from_node_id` 悬空拒绝 | 8.3 |
| 同上 | `test_layer3Loader_anchorMissingNode_rejects` | anchor.node_id exists | anchor 指向不存在 node | 8.4 |
| 同上 | `test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor` | event_only | `private_company` + event_only 语义 | 8.4 |
| 同上 | `test_layer3Loader_p0Anchor_missingSourceKeys_rejects` | P0 source_keys | `P0_CORE`/`P0_EVENT` 缺 source_keys | 8.4 |
| 同上 | `test_layer3Loader_crossChainMissingNode_rejects` | cross-chain refs | cross-chain 端点悬空拒绝 | 8.5 |
| 同上 | `test_layer3Loader_missingBundleFile_rejects` | fail-fast | 缺 manifest 或数据文件 → 无部分结果 | 8.3 |
| 同上 | `test_layer3Loader_invalidJson_rejects` | fail-fast | 坏 JSON 拒绝 | 8.3 |

**AUDIT A8 补测（Execute 未列）：** 空 bundle — 见 `AUDIT.plan.md` §2 A8。

### 5.4 四层测试

| 层 | 范围 | 命令 | 通过 |
| -- | ---- | ---- | ---- |
| L1 单元 | loader 校验 | `uv run pytest tests/test_layer3_loader.py -q` | exit 0 |
| L2 集成 | 无 DB 写 | N/A 本任务 | — |
| L3 管道 | batch3 staged gates | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q` | exit 0 |
| L4 E2E | 全量回归 | `uv run pytest -q` | exit 0；**仅 §8.6 执行一次** |

---

## 6. 接口/契约

- **权威：** `specs/contracts/layer3_loader_contract.yaml`
- **模块：** `docs/modules/layer3_industry_shock_anchor.md` §8.5–8.6（§8.12.11 超出 contract 项见 §3.2 defer）
- **模式参考：** `backend/app/layer2_sensors/sensor_loader.py`（`STAGED_REGISTRY_FIXTURE` + `mode` 校验形态）

### 6.1 Staged bundle 协议（冻结 — 对齐 019，消除五文件歧义）

| 项 | 约定 |
| -- | ---- |
| 默认 bundle 常量 | `STAGED_LAYER3_BUNDLE_DIR` → `tests/fixtures/layer3_staged_bundle/`（`loader.py` 内，对齐 `STAGED_REGISTRY_FIXTURE`） |
| mode 落点 | **`bundle_manifest.yaml` 根字段 `loader_mode: staged_fixture_only`**（生产 registry 五文件无 mode 字段） |
| manifest 内容 | `loader_mode` + 五数据文件相对路径（文件名对齐 contract `input_files`） |
| 校验时机 | `load()` 首步读 manifest；`loader_mode != staged_fixture_only` → `IndustryChainLoadError`（对齐 019 L72–75） |
| `bundle_dir` 参数 | 默认 `STAGED_LAYER3_BUNDLE_DIR`；仅接受 staged fixture 目录，**禁止**指向 `specs/layer3_global_industry_chains/` 生产路径 |
| fixture 体量 | 每表 ≥1 条合法记录；总 bundle < 50KB（eco；`GLOBAL_RESOURCE_LIMITS`） |

- **Python API（示意）：**

```python
class IndustryChainLoader:
    def load(self, *, bundle_dir: Path | None = None) -> IndustryChainLoadResult: ...
```

---

## 7. Red Flags

| 风险 | 预防 |
| ---- | ---- |
| 全量 registry 扫描 | fixture 子集 + eco |
| 绕过 staged mode | AC-020-5 |
| event_only 当行情锚 | AC-020-3 |
| 改 layer2/lineage contract | §3.3 + slice |
| 弱断言假绿 | GLOBAL_TESTING_POLICY |
| production-live 声称 | §0 + gate tests |
| 过度工程 / 重复造轮 | §0.3a ponytail ladder；复用 `sensor_loader.py` |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | 按 **§0.3** 读 `implement.jsonl` + `integration-ledger.md`；**§0.3a** Read ponytail；6.pre GitNexus；**创建** `test_layer3_loader.py` 骨架 + `tests/fixtures/layer3_staged_bundle/` 最小合法 manifest+五文件（§6.1）；基线 pytest |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py -q` |
| GREEN 命令 | `uv sync --locked` + `research/execute-evidence/8.0-boot-reads.txt` |
| RED 证据 | `research/execute-evidence/8.0-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.0-boot-reads.txt`, `8.0-green.txt`（ponytail 已读 + self-check 一行） |
| 已执行 | [x] |

### 8.1 Models

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `models.py`：`ChainEntry`, `AnchorEntry`, `NodeEntry`, `EdgeEntry`, `CrossChainEdgeEntry`, `IndustryChainLoadResult` |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py::test_layer3Loader_loadsStagedFixture_success -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `research/execute-evidence/8.1-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.1-green.txt`（含 ponytail self-check） |
| 已执行 | [x] |

### 8.2 Staged loader core

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `IndustryChainLoader` + §6.1 manifest/`loader_mode` + 五文件解析 |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py::test_layer3Loader_loadsStagedFixture_success tests/test_layer3_loader.py::test_layer3Loader_nonStagedMode_rejects -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `research/execute-evidence/8.2-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.2-green.txt`（含 ponytail self-check） |
| 已执行 | [x] |

### 8.3 Node/edge uniqueness + reference validation

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | chain/node/anchor 唯一；edge from/to 存在；缺文件/坏 JSON fail-fast |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py::test_layer3Loader_duplicateChainId_rejects tests/test_layer3_loader.py::test_layer3Loader_duplicateNodeId_rejects tests/test_layer3_loader.py::test_layer3Loader_duplicateAnchorId_rejects tests/test_layer3_loader.py::test_layer3Loader_edgeMissingToNode_rejects tests/test_layer3_loader.py::test_layer3Loader_edgeMissingFromNode_rejects tests/test_layer3_loader.py::test_layer3Loader_missingBundleFile_rejects tests/test_layer3_loader.py::test_layer3Loader_invalidJson_rejects -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `research/execute-evidence/8.3-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.3-green.txt`（含 ponytail self-check） |
| 已执行 | [x] |

### 8.4 Anchor rules

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `event_only`；`P0_CORE`/`P0_EVENT` `source_keys`；`anchor.node_id` 存在 |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py::test_layer3Loader_anchorMissingNode_rejects tests/test_layer3_loader.py::test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor tests/test_layer3_loader.py::test_layer3Loader_p0Anchor_missingSourceKeys_rejects -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `research/execute-evidence/8.4-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.4-green.txt`（含 ponytail self-check） |
| 已执行 | [x] |

### 8.5 Cross-chain edges

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | cross-chain `from/to` 引用校验 |
| RED 命令 | `uv run pytest tests/test_layer3_loader.py::test_layer3Loader_crossChainMissingNode_rejects -q` |
| GREEN 命令 | 同上 exit 0 |
| RED 证据 | `research/execute-evidence/8.5-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.5-green.txt`（含 ponytail self-check） |
| 已执行 | [x] |

### 8.6 Final gates

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | Tier A + batch3 gate + **Tier B 全库 pytest（本任务唯一一次）** |
| GREEN 命令 | 见 §10 |
| RED 证据 | `research/execute-evidence/8.6-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.6-green.txt` |
| 已执行 | [x] |

---

## 9. 四层测试（汇总）

见 §5.4。

---

## 10. Tier 验收

| Tier | 命令 | 通过 |
| ---- | ---- | ---- |
| A | `uv sync --locked` | exit 0 |
| A | `uv run pytest tests/test_layer3_loader.py -q` | exit 0 |
| A | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q` | exit 0 |
| A | `uv run ruff check backend/app/layer3_chains tests/test_layer3_loader.py` | exit 0 |
| A | `uv run python -m compileall backend/app/layer3_chains tests/test_layer3_loader.py` | exit 0 |
| B | `uv run pytest -q` | exit 0；**仅 §8.6 执行** |

**交接：** §8 证据齐 → Audit（非 finish-work）。§8.1–8.5 每步 GREEN 后仅跑当前步 RED 用例 + 既有全绿用例，**不**跑 Tier B。

---

## 11. Execute Skill 冻结

| Skill | 本任务 | 已执行 |
| ----- | ------ | ------ |
| trellis-execute | 必做 | [x] |
| test-driven-development | 必做 | [x] |
| incremental-implementation | 必做 | [x] |
| karpathy-guidelines | 必做（GREEN 前） | [x] |
| testing-guidelines | 必做 | [x] |
| **ponytail**（`.cursor/rules/ponytail.mdc`） | **必做 — Execute 全程**（用户 2026-06-23；≠ Audit A2 ponytail-review） | [x] |
| gitnexus-impact | 必做 | [x] |
| trellis-check | **不用** → Audit A1 | — |
| ponytail-review | **不用** → Audit A2 | — |

路径见 `execute-skill-paths.yaml`。

---

## 12. Audit 交接

- [x] §8 全部步骤已执行
- [x] `validate-execute-handoff` 通过
- [ ] 无 production-live 声称
