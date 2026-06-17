# GPT 合并后审查 — 问题登记与处置

> 2026-06-17 · 主会话复核 + Repair

## 总体评分（GPT 原评 · 仅记录）

| 维度 | 分 | 复核备注 |
|------|-----|----------|
| Batch B 完成 | 84 | 骨架交付完整 |
| 完成质量 | 76 | P0 语义/默认行为待收紧 |
| 代码质量 | 78 | 结构 OK |
| 架构解耦 | 82 | FetchPort 方向正确 |
| 工程规范 | 72 | CI 可见性待确认 |
| 过度工程 | 70 | 流程层偏重 · P2 文档化 |
| 安全 | 72 | 伪成功风险属实 |
| 性能 | 86 | 轻量 |
| 证据链 | 74 | FileRegistry 生产必填合理 |
| 测试 | 78 | 缺防呆测 |
| 可维护性 | 76 | 归档瘦身 P2 |
| 进入 Batch C | **已放行** | GPT repair + 契约/文档同步后 |

---

## P0 — 必须修复

| ID | 问题 | 复核 | 处置 |
|----|------|------|------|
| **P0-1** | UnpublishedPort → EMPTY_RESPONSE 混淆未发布与空响应 | **属实** — `docs/modules/data_sources.md` 已定义 `NOT_PUBLISHED_YET`，Batch B 临时用 EMPTY 偿还 | **修复** — 扩展 contract + UnpublishedPort |
| **P0-2** | `create_adapter` 默认 StubFetchPort 伪成功 | **属实** | **修复** — 生产 factory 必须显式 fetch_port；测试用 `create_test_adapter` |

---

## P1 — 高优先级

| ID | 问题 | 复核 | 处置 |
|----|------|------|------|
| **P1-1** | FileRegistry 可选导致证据索引缺口 | **部分属实** — 测试可选合理 | **修复** — `create_adapter` 默认 `require_file_registry=True` |
| **P1-2** | 成功 `row_count=1` 固定 | **属实** — skeleton 可默认 1 | **修复** — `FetchPayload.row_count` 可选传播 |
| **P1-3** | 成功无 `schema_hash` | **属实** | **修复** — `FetchPayload.schema_hash` + JSON key fingerprint |
| **P1-4** | fetch_log latency/retry 恒为 None/0 | **部分属实** | **修复** — Payload 传播 + `BaseDataAdapter` 测耗时 |
| **P1-5** | factory KeyError 可读性差 | **属实** | **修复** — `AdapterNotSupportedError` |
| **P1-6** | 无 payload 大小前置检查 | **部分属实** — RawStore 256MB 已有 | **修复** — skeleton `max_payload_bytes` 前置 FAILED（默认 10MB） |

---

## P2 — 可后续优化

| ID | 问题 | 复核 | 处置 |
|----|------|------|------|
| **P2-1** | adapter 过薄缺 metadata | 属实但非阻塞 | **不修复** — Batch C/D 再加 |
| **P2-2** | Trellis 流程体量偏重 | 属实 | **不修复** — 归档瘦身规则写入本表建议 |
| **P2-3** | CI 状态不可见 | 待确认 | **复核** — PR #2 Actions 通过 |

### P2 延后登记

| ID | 内容 | 阶段 |
|----|------|------|
| P2-1 | adapter metadata | Batch C/D |
| P2-2 | Trellis 归档瘦身 | 流程建议 · `DECISIONS.md` §10 B-P2-2 |

---

## P3 / 建议（GPT 未标 P 级）

| 项 | 处置 |
|----|------|
| SkeletonAdapterBase 勿膨胀为上帝类 | **文档** — `.trellis/spec/backend/datasource-adapters.md` §Design Decision |
| 8 项缺失测试清单 | **修复** — 合并入 `test_adapter_skeletons.py` |
| npm audit CI 门禁 | **不修复** — Python 项目 · 非本批范围 |

---

## Repair 验收命令

```powershell
pytest tests/test_adapter_skeletons.py tests/test_data_adapter_contract.py -v
pytest -q --cov=backend --cov-fail-under=75
ruff check backend/app/datasources tests/test_adapter_skeletons.py
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
```

## Repair 执行结果（2026-06-17）

| ID | 状态 |
|----|------|
| P0-1 | **已修复** — `NOT_PUBLISHED_YET` contract |
| P0-2 | **已修复** — `create_adapter` 禁默认 Stub |
| P1-1..P1-6 | **已修复** |
| P2-1..P2-2 | **不修复** — 记录 defer · 见 `DECISIONS.md` §10 |
| P2-3 CI | **已复核** — PR #2 Actions 通过 |
| 契约/进度文档 | **已同步** — `data_adapter_contract.md` · `BATCH_B_REPAIR_STATUS.md` · `README.md` |
