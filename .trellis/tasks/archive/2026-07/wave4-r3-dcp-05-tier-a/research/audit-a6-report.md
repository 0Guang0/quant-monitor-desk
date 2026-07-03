# Audit A6 — Registry/Docs（wave4-r3-dcp-05-tier-a）

> **维：** A6 registry 三件套（AUDIT.plan §2 主会话覆写；非 performance SKIP）  
> **协议：** plan_protocol_version 4.1  
> **日期：** 2026-07-02  
> **焦点：** S13 · `source_registry.yaml` + `source_capabilities.yaml` + `incremental_source_registry.py` · ops 文档 · `loop_maintain` · ACC-EASTMONEY-TAXONOMY-001

---

## 维度证据

### Boot / 范围

| 项                              | 证据                                                                                     |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| AUDIT.plan §2 A6                | registry 三件套（主会话）                                                                |
| S13 AC（`to-issues-slices.md`） | capabilities/registry 行 · ACC-EASTMONEY 文档 · `test_catalog.yaml` · `loop_maintain` 绿 |
| 活卡 §2                         | 承接 `ACC-EASTMONEY-TAXONOMY-001`（**文档/registry**，不关 `R3-B2.75-REQ2-EM`）          |

### 11 source_id 三件套 vs ADR-028 矩阵

| source_id                   | ADR-028 canonical_domain | clean_table            | py/yaml 对齐 |
| --------------------------- | ------------------------ | ---------------------- | ------------ |
| baostock … deribit（11 源） | 见 ADR-028 L17–29        | 见 slices ADR028_CLEAN | **OK**       |

- `TIER_A_INCREMENTAL_BY_SOURCE` = 11 行；`frozenset(rows) == TIER_A_SOURCES` drift guard 存在
- `uv run pytest tests/test_tierA_incremental_registry.py -q` → **22 passed, exit 0**

### DCP-05 notes 抽检

- **11/11** Tier A 在 `source_registry.yaml` notes 含 `DCP-05 incremental CLI --source-id <id> (ADR-028)`
- **11/11** Tier A 在 `source_capabilities.yaml` notes 含 `DCP-05: qmd data sync --source-id <id> -> <clean_table> clean (ADR-028)`
- **不对称：** registry 侧未写 clean 表目标（capabilities 已写）→ 见 A6-P3-001

### S13 文档

| 工件                                                   | 裁决                                                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------- |
| `docs/ops/data_sync_quick_reference.md`                | Tier A 表 + CLI 示例 + **§ACC-EASTMONEY-TAXONOMY-001**（不关 REQ2-EM） |
| `docs/architecture/06_deployment_and_local_ops.md` L16 | Tier A 11 源 CLI 指针                                                  |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                   | `R3-B2.75-REQ2-EM` 仍为 **DEFERRED**                                   |

### `loop_maintain`

```text
uv run python scripts/loop_maintain.py → exit 0
```

### GitNexus

`context(resolve_tier_a_incremental)` → Symbol not found（索引 stale，与 `gitnexus-audit-summary.md` 一致）

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                          | 锚点                                                                                                                      | 根因                                                                              | 修复方案                                                                                             | 验证                                                              |
| --------- | --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A6-P2-001 | P2  | ACC-EASTMONEY registry 半交付 | 活卡 §2 · `source_registry.yaml` eastmoney · `source_capabilities.yaml` eastmoney · `data_sync_quick_reference.md` L29–34 | ops 已写 ACC 节，但 eastmoney 两行 notes 无 `ACC-EASTMONEY-TAXONOMY-001` 交叉引用 | 在 eastmoney `notes` 追加 ACC 指针（validation-only；产品 bar 见 baostock/mootdx；**不关** REQ2-EM） | `rg ACC-EASTMONEY specs/datasource_registry/` 命中 eastmoney 两行 |

---

## 计划外发现

| ID        | P   | 标题                                    | 锚点                                                       | 根因                                                       | 修复方案                                                     | 验证                                          |
| --------- | --- | --------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------- |
| A6-P3-001 | P3  | registry/capabilities DCP-05 注释不对称 | `source_registry.yaml` 11 行 vs `source_capabilities.yaml` | registry 仅写 CLI 路由，capabilities 含 `-> <clean_table>` | registry 11 行 notes 对齐 capabilities 模板（补 clean 表名） | 逐源 diff 两文件 DCP-05 子串含相同 clean 表名 |

已对抗搜索：`specs/datasource_registry/**` · `incremental_source_registry.py` · ADR-028 · ops 文档 · `loop_maintain` 实跑。
