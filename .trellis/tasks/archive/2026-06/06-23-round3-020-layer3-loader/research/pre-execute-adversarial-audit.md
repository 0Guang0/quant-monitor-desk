# 020 Pre-Execute 对抗性审计

**Result:** WARN

**审计范围：** `MASTER.plan.md`、`AUDIT.plan.md`、`implement.jsonl`、`research/*`；对照 `layer3_loader_contract.yaml`、`layer3_industry_shock_anchor.md` §8.5–8.6 / §8.12、`020_implement_layer3_industry_chain_loader.md`、`sensor_loader.py`、`test_batch3_staged_downstream_gate.py`。  
**审计日期：** 2026-06-23 · **模式：** Plan-only（未跑 Execute / 未改 `layer3_chains/` 业务代码）

---

## 测试覆盖矩阵（contract rule → §5.3 用例 → 缺口）

权威：`specs/contracts/layer3_loader_contract.yaml` `hard_validation_rules`（7 条）

| #   | Contract 硬规则                               | MASTER §5.3 命名用例                                     | §8 步                                | 缺口 / 备注                                                                                                                                                            |
| --- | --------------------------------------------- | -------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `chain_id` must be unique                     | **无**                                                   | §8.3 文案提及 node 唯一，未列 chain  | **缺口** — AC-020-2 声称覆盖「唯一性」，但 §5.3 无 `duplicate chain_id` 用例；AUDIT A8 仅 Audit 补测，Execute RED 无锚点                                               |
| 2   | `node_id` must be unique                      | **无**                                                   | §8.3「node*id 唯一」无对应 `test*\*` | **缺口** — 同 #1                                                                                                                                                       |
| 3   | edge `from_node_id` / `to_node_id` must exist | `test_layer3Loader_edgeMissingNode_rejects`              | §8.3                                 | **部分** — 名称暗示仅 `to_node`；`layer3_industry_shock_anchor.md` §8.12.11 还要求「edge 起点不存在」阻断；缺 `from_node` 悬空用例                                     |
| 4   | `anchor_id` must be unique                    | **无**                                                   | —                                    | **缺口**                                                                                                                                                               |
| 5   | `anchor.node_id` must exist                   | **无**（§8.4 实现说明有，§5.3 无）                       | §8.4                                 | **缺口** — 与 edge 引用不同路径，需独立 fixture                                                                                                                        |
| 6   | `event_only` 私有公司不得当日度价锚           | `test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor` | §8.4                                 | **覆盖** — 建议断言 `event_only=true` + `instrument_type=private_company` 组合（对齐 §8.12.11「private_company event_only=false 阻断」的反面）                         |
| 7   | `P0_CORE` / `P0_EVENT` 须有 `source_keys`     | `test_layer3Loader_p0Anchor_missingSourceKeys_rejects`   | §8.4                                 | **覆盖** — 建议 §5.3 注明须分别或参数化覆盖两档 priority                                                                                                               |
| —   | staged-only（AC-020-5，非 contract 条目）     | `test_layer3Loader_nonStagedMode_rejects`                | §8.2                                 | **覆盖** — 见下文「staged mode 机制未定义」                                                                                                                            |
| —   | 五表成功加载（AC-020-1）                      | `test_layer3Loader_loadsStagedFixture_success`           | §8.2                                 | **部分** — 仅「非空 chains/anchors」；未断言 nodes/edges/cross_chain 计数或抽样字段                                                                                    |
| —   | cross-chain 引用校验                          | **§5.3 未列任何 `cross_chain` 用例**                     | §8.5                                 | **严重缺口** — §8.5 RED 为 `pytest … -k cross_chain`，与 §5.3 表矛盾；当前 `tests/test_layer3_loader.py` 仅 1 行占位，`-k cross_chain` 会 0 selected                   |
| —   | 缺文件 / 坏 JSON                              | **无**（§5.2 S1 语义提及）                               | —                                    | **缺口** — AUDIT A8 要求 Audit 补；Execute 若 fail-fast「无部分结果」（§0 Failure modes）应在 §5.3 至少有 1 条                                                         |
| —   | 空 bundle                                     | **无**                                                   | —                                    | **缺口** — 仅 AUDIT A8                                                                                                                                                 |
| —   | `commodity` 标为 `public_equity`              | **无**                                                   | —                                    | **文档漂移** — `layer3_industry_shock_anchor.md` §8.12.11 要求 loader 阻断；**不在** `layer3_loader_contract.yaml`；MASTER 未声明 defer → Execute 可能漏实现或超 scope |

### §5.3 vs §8 步覆盖小结

| §8 步 | §5.3 是否可 RED     | 判定                                         |
| ----- | ------------------- | -------------------------------------------- |
| 8.2   | 2/2 有命名          | OK（mode 机制另见分歧点）                    |
| 8.3   | 1/3+ 规则有命名     | **不足**                                     |
| 8.4   | 2/3 规则有命名      | **不足**（缺 anchor.node_id）                |
| 8.5   | **0**               | **BLOCK 级计划缺陷**（RED 命令无对应用例名） |
| 8.6   | 依赖上表全集 + Tier | 前置未齐                                     |

### AUDIT A8 对照

- A8 正确识别：重复 `chain_id`、空 bundle、坏 JSON 为 Audit 补边界。
- **问题：** A8 写「新测绿或 **§4.3**」— `AUDIT.plan.md` 无 §4.3（仅 §4 DoD），**死引用**，Execute/Audit 均无法解析 fallback。
- A8 **未**要求 Audit 补：重复 `node_id`/`anchor_id`、cross-chain 悬空、`anchor.node_id` 悬空、缺文件（仅坏 JSON/空 bundle）。
- `integration-audit.md` 声称「contract hard rules → §8.3–8.5 **PASS**」— **与矩阵矛盾**，对抗性审阅应标为过度乐观。

### `test_batch3_staged_downstream_gate.py`

- **无 020 / layer3 专用断言**；仅文档 token 检查 + 019/handoff 门禁。
- MASTER §10 Tier A 依赖此文件「仍绿」合理（不回归 staged 文档口径），但 **不能** 证明 020 loader 已接入 Batch3 gate 叙事；与 AC-020-5 的验证链是间接的。

---

## 契约/文档漂移

| 项                       | 权威                                                                                                                  | MASTER / Plan                                                                      | 漂移                                                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Registry 路径            | `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/`                                             | `source-index.md` §A 已纠偏                                                        | **已处理** — 模块 doc §8.5 仍写 `specs/layer3_global_industry_chains_v1_2/` 旧路径                                     |
| Loader 输入文件数        | contract **5** 文件                                                                                                   | MASTER §3.1 五文件                                                                 | **一致**                                                                                                               |
| Loader 输入文件数        | `layer3_industry_shock_anchor.md` §8.12.1 **7** 项（含 `layer3_data_dictionary.md`、`references/source_registry.md`） | MASTER 未读这两份                                                                  | **有意收窄或遗漏** — Execute 应在 §3.2 defer 显式写「data_dictionary / source_registry 本任务不读」                    |
| 硬校验规则集             | contract 7 条                                                                                                         | §2 AC-020-2「唯一性 + 边/节点引用」                                                | AC 宽于 §5.3 实测表                                                                                                    |
| 模块验收表               | §8.12.11 6 行 loader 测试                                                                                             | MASTER §5.3 5 用例                                                                 | **commodity/public_equity**、**edge 起点** 未进 plan                                                                   |
| 错误类型                 | §0 `IndustryChainLoadError`                                                                                           | 019 用 `CrossAssetRegistryLoadError`                                               | **可接受** — 但 §5/§8 未要求测试 `pytest.raises(IndustryChainLoadError)`，019 用 `Exception`+match；Execute 可能不一致 |
| API 签名                 | §6 `load(*, bundle_dir: Path \| None = None)`                                                                         | 019 `load(*, registry_path: Path \| None = None)` + `STAGED_REGISTRY_FIXTURE` 常量 | **未规定** 默认 bundle 常量名/路径（`tests/fixtures/layer3_staged_bundle/` 仅 §4 地图）                                |
| `staged_fixture_only`    | 019 单文件 YAML 根字段 `mode`                                                                                         | MASTER §8.2 要求 mode，五文件 bundle **无 mode 落点**                              | **严重未定义** — 生产 `layer3_global_industry_chain_registry.yaml` 无 `mode` 字段                                      |
| Lineage                  | 任务卡 §15 全套 lineage 字段                                                                                          | MASTER §3.2 defer `021`；禁止写 `snapshot_lineage_contract.yaml`                   | **一致** — 但见 ADV-R3X                                                                                                |
| `ADV-R3X-LINEAGE-001`    | `R3X_residual_open_items_closure.md` defer Batch 4/5                                                                  | MASTER §0 列 REQ2-EM，**未**列 LINEAGE-001                                         | **应显式 defer**，避免 Execute 误做 lineage 持久化                                                                     |
| `contract_coverage.yaml` | `layer3_loader_contract.yaml` **waiver**「not yet implemented」                                                       | 020 完成后应移除 waiver                                                            | **Execute 后** 协调者事项；Plan 未写                                                                                   |
| 测试占位                 | `test_catalog.yaml` 已登记 `test_layer3_loader.py`                                                                    | 文件存在但 **无测试体**                                                            | Boot §8.0 RED「全文件」将失败 — 符合 TDD，但 §8.1 应用例级 RED 需先写测试骨架                                          |

---

## 执行者分歧点（按严重度）

### P0 — 不修订易导致 Execute 卡死或假绿

1. **§8.5 cross-chain RED 与 §5.3 脱节**
   - §8.5：`pytest … -k cross_chain`
   - §5.3：**零** `cross_chain` 用例名
   - **修复建议：** 在 §5.3 增加至少 `test_layer3Loader_crossChainMissingNode_rejects`（及可选 success 路径在 loadsStaged 中断言 cross_chain 非空）。

2. **`staged_fixture_only` 在五文件 bundle 中的表达未定义**
   - 019：单 YAML `mode: staged_fixture_only`
   - Layer3：五文件 + `bundle_dir`；生产 registry 无 `mode`
   - **分歧：** bundle 根 manifest？仅 chain YAML？环境变量？`IndustryChainLoader` 构造参数？
   - **修复建议：** §6 或 §8.2 冻结一种（推荐：`tests/fixtures/layer3_staged_bundle/bundle_manifest.yaml` 含 `mode` + 五文件相对路径，或 chain registry 顶层 `loader_mode`，与 fixture 文档一并写入 §4 代码地图）。

3. **§5.3 未覆盖 contract 四条唯一性/引用规则中的三条**
   - 缺：duplicate `chain_id` / `node_id` / `anchor_id`；`anchor.node_id` 悬空
   - **修复建议：** 扩展 §5.3 表（可 `tmp_path` 变异 fixture，对齐 019 `test_crossAssetRegistryLoader_rejectsDuplicateInstrumentId` 模式）；或 §5.3 明确「§8.3–8.5 每步 RED 前须新增对应用例名」并列出最小集合。

### P1 — 实现分叉 / 验收争议

4. **§8.3 仅 `edgeMissingNode`，未区分 from/to** — 与模块 doc §8.12.11「edge 起点不存在」不对齐。

5. **`original-plan-trace.md` 与 MASTER 测试名不一致** — `test_layer3Loader_*_rejectsInvalidRef` vs `edgeMissingNode_rejects`；Execute 以 §5.3 为准，trace 应同步避免 AC 追溯歧义。

6. **Tier B 触发时机未写死** — §10 列 `uv run pytest -q` 为 Tier B；§8.6 写「Tier A + batch3 gate + 全量 pytest」；§0.1 写 prod-path=Tier B。**分歧：** 每步后跑还是仅 8.6？**建议：** §8.6 明确「Tier B 仅本步一次」；中间步仅 L1+L3。

7. **§8.1 Models 步 RED 依赖 `loadsStagedFixture_success`** — 需先具备测试文件 + fixture 骨架 + import；vertical-slices 将 MODELS 与 LOADER 拆开，但 §8.1 未说明「测试/fixture 在 8.0 还是 8.1 写入」。**建议：** §8.0 增加「创建 `test_layer3_loader.py` 骨架 + `layer3_staged_bundle/` 最小合法 fixture」。

8. **`IndustryChainLoadError` vs `pytest.raises(Exception)`** — 019 多用 `Exception`+match；MASTER §0 命名了专用异常；**建议 §5.0** 要求 `IndustryChainLoadError` 且 message 含规则语义。

9. **vertical-slices SLICE-ANCHOR 仅依赖 SLICE-LOADER，不依赖 SLICE-GRAPH** — 与 §8 顺序（8.3 graph → 8.4 anchor）不一致；`anchor.node_id` 校验属图引用，**建议** slice 表注明 8.4 依赖 8.3 或合并。

### P2 — 文档/审计卫生

10. **AUDIT A8「§4.3」死引用** — 改为 `MASTER §5.3` 或新增 `AUDIT.plan.md` §4.3「Execute 未覆盖边界由 A8 补测」。

11. **`integration-audit.md` PASS 与对抗矩阵冲突** — Plan freeze 后应降为 WARN 或附「已知 §5.3 缺口」。

12. **任务卡 §11 `ruff check .` vs MASTER Tier A `ruff check backend/app/layer3_chains tests/test_layer3_loader.py`** — 范围不一致；以 MASTER 为准，任务卡追溯时注明。

---

## ponytail 计划编码评审（Execute 门控是否充分）

### 已写清且合理

- §0.3a：Boot 必读、每 §8.x 步前对照 ladder、禁止新抽象/未请求 helper、`ponytail:` 天花板注释。
- §11 Skill 表：ponytail **Execute 全程** vs Audit A2 `ponytail-review` 分离。
- §0.3a 第 4 点：**「TDD 顺序不变：RED → karpathy → testing-guidelines → ponytail ladder → GREEN」** — **不与 TDD 冲突**；ponytail 在 GREEN 实现前作为约束，符合 lazy senior 意图。
- §7 Red Flags 吸收「过度工程」。
- `implement.jsonl` 第 4 条路由到 `ponytail.mdc`。

### 不足（Execute 门控证据）

| 缺口                                                        | 风险                         | 建议修订                                                                                                  |
| ----------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| 仅 §8.0 GREEN 要求 `8.0-green.txt`「ponytail 已读确认一行」 | 后续步无 ponytail 可审计痕迹 | §8.x GREEN 证据模板增加：`ponytail: reused <symbol> from sensor_loader` 或 `ponytail: no new helper` 一行 |
| 无「删 bloat」量化标准                                      | A2 与 Execute 扯皮           | §0.3a 增：每步 GREEN 前 self-check「是否可复制 019 的 `_assert_*` 形态而非新 Validator 类」               |
| 未要求对比 019 测试/fixture 行数量级                        | 可能过度 fixture             | §8.2 增：fixture 最小子集（如每表 ≥1 条、共 <N KB），引用 GLOBAL_RESOURCE_LIMITS eco                      |
| Audit A2 覆盖实现后 ponytail，Execute §0.3a 无失败即停损    | 过度工程可能到 Audit 才删    | 可接受若 A2 必做；建议在 §12 交接加「A2 FAIL → 回 Execute 删 bloat」                                      |

**结论：** ponytail **要求足够明确**，与 TDD/karpathy **无顺序冲突**；**验收证据偏弱**（主要靠 Audit A2，Execute 侧仅 Boot 一行确认）。

---

## 架构与范围

| 检查项                                                        | 判定                                                                                                                   |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Batch3 staged gate（文档级）                                  | **一致** — MASTER §0/§10；gate 测试不覆盖 020 代码                                                                     |
| D-09（L2–5 不复制 L1 全套标准化字段）                         | **一致** — 任务卡 §15 用户决策 + MASTER defer lineage 写                                                               |
| 023A `snapshot_lineage_contract.yaml` 只读                    | **一致** — §3.3 forbidden                                                                                              |
| 禁止改 `specs/layer3_global_industry_chains/**` 生产 registry | **一致** — fixture 在 `tests/fixtures/`                                                                                |
| `R3-B2.75-REQ2-EM` DEFERRED                                   | **已写** — §0                                                                                                          |
| `ADV-R3X-LINEAGE-001` L3/L4 完整 snapshot lineage             | **未在 MASTER defer 表显式列出** — 应在 §3.2 增一行「完整 L3 snapshot lineage → `021`/Batch 5；registry 仅登记 defer」 |
| 与 019 `sensor_loader` 模式                                   | **意图对齐**，但五文件 + mode 机制需冻结（见 P0）                                                                      |
| GitNexus impact                                               | **LOW**（`gitnexus-summary.md`）— 与新建 loader 一致                                                                   |

---

## 建议修订 MASTER §x（具体条款，不直接改 MASTER）

1. **§5.3** — 扩充用例表（最小集）：
   - `test_layer3Loader_duplicateChainId_rejects`
   - `test_layer3Loader_duplicateNodeId_rejects`
   - `test_layer3Loader_duplicateAnchorId_rejects`
   - `test_layer3Loader_anchorMissingNode_rejects`
   - `test_layer3Loader_edgeMissingFromNode_rejects`（或合并为参数化 `edgeMissingEndpoint_rejects`）
   - `test_layer3Loader_crossChainMissingNode_rejects`
   - `test_layer3Loader_missingBundleFile_rejects`
   - `test_layer3Loader_invalidJson_rejects`
   - 在 `loadsStagedFixture_success` 断言语义中写明：五类集合非空 + `mode==staged_fixture_only`（字段名随 manifest 冻结）

2. **§6 或 §8.2** — 冻结 staged bundle 协议：
   - 默认路径常量名（如 `STAGED_LAYER3_BUNDLE_DIR`）
   - `staged_fixture_only` 存放位置与校验时机
   - 五文件名与 contract `input_files` 一致

3. **§8.5** — RED/GREEN 命令改为显式用例名（与 §5.3 同步），删除孤立的 `-k cross_chain` 直至 §5.3 有对应行。

4. **§8.0** — 增加交付物：`test_layer3_loader.py` 测试骨架 + `tests/fixtures/layer3_staged_bundle/` 最小合法五文件（供 8.1 RED）。

5. **§3.2 defer 表** — 增加：
   - `ADV-R3X-LINEAGE-001` 完整 L3 snapshot lineage → `021`+
   - `layer3_data_dictionary.md` / `source_registry.md` 读取 → 非 020 loader 输入（若有意收窄）
   - `commodity` vs `public_equity` 语义校验 → defer 至 contract 修订或 021 quality checker（二选一写死）

6. **§5.0** — 断言 `IndustryChainLoadError`；测试注释四元组（已有）+ 每条对应 contract rule ID。

7. **§8.6 / §10** — 写明：**Tier B（全库 pytest）仅在 §8.6 执行一次**；§8.1–8.5 仅 L1 + 当前步用例。

8. **§0.3a** — 每步 GREEN 证据文件增加 ponytail self-check 一行（复用点或删 bloat 说明）。

9. **AUDIT.plan.md §2 A8** — 将「§4.3」改为「MASTER §5.3 缺口清单」；A8 补测范围与 §5.3 扩充后取补集，避免重复劳动。

10. **research/integration-audit.md** — contract→§8.3–8.5 行改为 WARN 并指向本文件。

---

## Review Summary（五维简评）

| 维度         | 评估                                                             |
| ------------ | ---------------------------------------------------------------- |
| Correctness  | AC 与 contract 声明宽于 §5.3 实测；§8.5 无法按 Plan RED          |
| Readability  | MASTER 结构清晰；但 §5.3/§8/vertical-slices 三处测试名不一致     |
| Architecture | staged-only + 019 模式方向正确；bundle/mode 未冻结是最大架构歧义 |
| Security     | staged-only + forbidden 路径充分；无 DB 写；fixture 边界测不足   |
| Performance  | eco + 最小 fixture 已提；缺 fixture 体量上限数字                 |

### What's Done Well

- §0 staged limitations、forbidden 列表、D-09、023A 写权限边界清楚。
- AC-020-1..6 与任务卡、source-index 映射完整。
- §0.3a ponytail 与 TDD 顺序并列写清，避免 Execute 误以为二选一。
- AUDIT A8 已预见 duplicate chain / 坏 JSON / 空 bundle（虽 Execute 表未吸收）。
- `sensor_loader.py` 作为唯一 wiring 参考在 implement.jsonl 与 §6 双重锚定。

### Verification Story

- **Tests reviewed:** 是 — `test_layer3_loader.py` 仅占位；§5.3 表为唯一 Execute 测试契约。
- **Build verified:** 否 — Plan-only 审计。
- **Security checked:** 是（静态）— scope/forbidden/staged-only；无额外攻击面。

---

**是否建议用户批准 Execute：** **可批准**（2026-06-23 协调者已按 Top3 修订 MASTER §5.3/§6.1/§8/§3.2）。修订前为暂缓。

**修订状态：** 见 `plan.freeze.md` Post-freeze §2；对抗性发现已落 MASTER，非仅 `research/` 建议。

**Top 3 必须修 Plan 项：**

1. **§5.3 + §8.5 对齐** — 补齐 cross-chain 及 contract 唯一性/anchor.node_id 命名用例；删除无锚点的 `-k cross_chain` RED。
2. **§6/§8.2 冻结五文件 bundle 的 `staged_fixture_only` 机制与默认路径常量** — 否则 020 无法无歧义复刻 019。
3. **§3.2 显式 defer `ADV-R3X-LINEAGE-001` + 裁定 `layer3_industry_shock_anchor.md` §8.12.11 中超出 contract 的规则（implement / defer / 扩 contract）** — 避免 Execute 与 Audit A1 对「commodity/public_equity」各说各话。
