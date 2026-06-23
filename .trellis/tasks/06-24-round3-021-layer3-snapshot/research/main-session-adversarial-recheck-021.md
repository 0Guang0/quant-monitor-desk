# 主会话对抗性复核 — 021 Layer3 Snapshot（2026-06-24）

**基线 commit：** `6d2a7f37`（fix agent 收口）  
**复核者：** 主会话  
**方法：** 对照 `fix-closure.md`、Phase 7 `a1–a8.md`、实现与测试；ponytail 阶梯扫描（中文注释豁免）

---

## 结论

| 维度                             | 判定                                               |
| -------------------------------- | -------------------------------------------------- |
| Phase 7 BLOCKING                 | **已闭合**（G1 等在 `fdf5d4e8` / `6d2a7f37`）      |
| Phase 7 NON-BLOCKING（可 defer） | **合理 defer**（G9、OOF-4/5、UF-2/3、A6 NB-1～3）  |
| fix-closure 与代码一致性         | **经本复核修补后一致**                             |
| Ponytail                         | **合规**（单点数值解析、无多余抽象、天花板已标注） |

---

## 对抗性发现与处置

### 1. BLOCKING 级缺口（已修补）

| ID    | 发现                                                                          | 风险                       | 处置                                                                                                           |
| ----- | ----------------------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| MS-01 | `volume` 使用裸 `float()`，非数值时泄漏 `ValueError`；与 OOF-7 `close` 不对称 | 信任边界不一致             | `_parse_bar_close` 升格为 `_parse_bar_numeric(field=...)` 单点；`test_layer3Snapshot_nonNumericVolume_rejects` |
| MS-02 | `anchor_cfg["instrument_id"]` 直接下标，缺字段时泄漏 `KeyError`               | 畸形 manifest 不可统一捕获 | build 路径显式 guard + `test_layer3Snapshot_missingInstrumentId_rejects`                                       |

### 2. 已核对无缺口（抽检）

- UF-1：`l5_bundle_dir` 须 `relative_to(PROJECT_ROOT)`，负向测有效
- D-2/D-3：bar 必填字段、tz-aware `_parse_ts`，单点 guard
- G6：lineage `source_dataset_ids` 拒绝 agent prose
- G7：同输入 `parameter_hash` + `latest_price` 确定性
- event_only：不读 L5 bar；provenance 取自 manifest 全局（ponytail 注释 + defer G9）
- 测试：24 条均含四元组 docstring；无 mock 内部 helper、断言可观察行为

### 3. 维持 defer（非遗漏）

- G9：event_only 误有价负向价值低
- OOF-4/5：`price_proxy_needs_feed` / `pct_change_1d` — Batch 5+ / 单日 fixture
- UF-2/3：路径 redact、YAML max_bytes — staged 信任边界 + ponytail 注释
- A6：SKIP 维持；ResourceGuard / bar 索引 / manifest memoize 已注释升级路径

### 4. Ponytail 扫描

| 阶梯      | 结果                                                                                                         |
| --------- | ------------------------------------------------------------------------------------------------------------ |
| YAGNI     | 未引入 ResourceGuard stub、索引、缓存                                                                        |
| 复用      | `_parse_bar_numeric` 统一 close/volume；`_bar_for_trade_date` / `_parse_ts` / `_resolve_l5_bundle_root` 单点 |
| 无新依赖  | 仅 stdlib + yaml                                                                                             |
| 最小 diff | MS 修补仅扩展既有 guard + 2 条负向测                                                                         |
| 天花板    | 模块头、event_only、YAML、线性 bar 扫、manifest 重读均有 `ponytail:`                                         |

---

## 验证（本复核后）

| 命令                                                     | 结果             |
| -------------------------------------------------------- | ---------------- |
| `uv run pytest tests/test_layer3_snapshot_builder.py -q` | 24 passed        |
| `uv run pytest -q`                                       | （见主会话终端） |

---

## 残余风险（已登记 Batch 6 — 不阻塞 021）

| Registry ID      | 说明                                                                                                 | 登记位置                                                                                                         |
| ---------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `R3-B6-021-O-01` | `_bar_for_trade_date` 对非 dict `bars[]` 元素 `continue` 跳过；Batch 6 须加 manifest/bar schema 校验 | `AUDIT_DEFERRED_REGISTRY.md` · `UNRESOLVED_ISSUES_REGISTRY.md` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Batch 6 表 |
| `R3-B6-021-O-02` | 确定性测仅比 `parameter_hash` + `latest_price`；Batch 6 须扩展为全 row tuple 断言                    | 同上                                                                                                             |
