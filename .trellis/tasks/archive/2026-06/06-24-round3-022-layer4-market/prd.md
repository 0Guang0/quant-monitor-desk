# Round 3 022 Layer4 market structure — PRD（Plan 2a）

## 问题

Layer 4 需要把各市场内部结构（calendar、breadth、指数/板块快照、规则事件）转为可查询、可审计的结构化快照，供下游 Layer 5 与 Agent 解释使用，且不得输出交易动作语义。

## 用户 / 协调者目标

- 在 **staged-only** 语境下交付可运行 `market_structure.py` 骨架
- 证明 **as_of** 与未来数据边界（对齐 `snapshot_lineage_contract.yaml`）
- 遵守 Wave C **022** worktree allowed/forbidden（MAP §2.2）

## 非目标（本切片）

- FastAPI `/api/layer4/*`、CLI `qm sync-layer4`
- 全量 MarketAdapter 生产抓取（A股/美股/港股/期货/期权各自 live 源）
- WriteManager 生产 DuckDB clean 表写（可选 sandbox defer）
- 关闭 `ADV-R3X-LINEAGE-001` 全量跨层持久化
- 修改 registry 三件套

## 成功标准（→ MASTER §2）

见 `plan-boot.md` AC 草稿 AC-022-1..8；Playbook §8.2 PASS 表逐行满足。

## 约束摘要

- D-09：Layer 2–5 不默认复制 Layer1 全套标准化字段
- eco 默认；禁止全市场全历史扫描
- TDD + ponytail（生产与 `tests/` 同标准）+ 测试五字段 docstring
