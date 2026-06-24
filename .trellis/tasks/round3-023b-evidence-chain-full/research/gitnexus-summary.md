# GitNexus summary — 023b Layer5 evidence chain (Plan 1b)

## query: layer5 evidence chain builder

**相关执行流：** Layer3 snapshot → Layer4 market snapshot → Layer5 evidence foundation →（本任务）evidence chain assembly。

**关键符号：**

| 符号                           | 文件                                 | 角色                                 |
| ------------------------------ | ------------------------------------ | ------------------------------------ |
| `EvidenceFoundationValidator`  | `foundation.py`                      | 023A 事实/Agent 分界；chain 输入门禁 |
| `Layer5LineageBuilder`         | `lineage.py`                         | lineage envelope；chain 输出须兼容   |
| `IndustryChainSnapshotBuilder` | `layer3_chains/snapshot_builder.py`  | upstream L3 snapshot id 来源         |
| `MarketStructureBuilder`       | `layer4_markets/market_structure.py` | upstream L4 snapshot id 来源         |

## impact 预判（Plan 阶段）

| 拟改符号                             | 方向                   | 风险                  |
| ------------------------------------ | ---------------------- | --------------------- |
| 新增 `EvidenceChainBuilder`          | downstream: tests only | LOW                   |
| 扩展 `layer5_evidence_contract.yaml` | docs/tests             | LOW                   |
| 触及 `staged_evidence.py`            | —                      | **禁止**（forbidden） |

## 结论

改动应限制在 `layer5_evidence/**`；复用 `core/snapshot_lineage.py` 与 023A validator；L3/L4 仅通过 staged fixture snapshot_id 字符串引用，不 import 其 builder 内部状态。
