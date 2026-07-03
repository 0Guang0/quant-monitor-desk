# Batch B GPT 合并后审查 — Repair 状态

> 对照 GPT post-merge 审查逐项核对 · **结论：P0/P1 已关闭，可进入 Batch C Plan**

---

## 代码修复（本工作区）

| ID   | 问题                                    | 状态                                                 |
| ---- | --------------------------------------- | ---------------------------------------------------- |
| P0-1 | `NOT_PUBLISHED_YET` vs `EMPTY_RESPONSE` | **已修复**                                           |
| P0-2 | `create_adapter` 默认 Stub 伪成功       | **已修复** — `create_test_adapter()` 供测试          |
| P1-1 | FileRegistry 生产必填                   | **已修复**                                           |
| P1-2 | `row_count` 传播                        | **已修复**                                           |
| P1-3 | `schema_hash`                           | **已修复**                                           |
| P1-4 | latency / retry                         | **已修复** — payload 传播 + `BaseDataAdapter` 测耗时 |
| P1-5 | `AdapterNotSupportedError`              | **已修复**                                           |
| P1-6 | payload 大小前置                        | **已修复** — `max_payload_bytes` 10MB                |

## 文档 / 契约同步（本 commit）

| 项                                                                | 状态       |
| ----------------------------------------------------------------- | ---------- |
| `specs/contracts/data_adapter_contract.md` 第 8 态 + 校验规则     | **已更新** |
| `DECISIONS.md` §9 GPT-NOT-PUBLISHED → 已偿还                      | **已更新** |
| `DECISIONS.md` §10 Batch B checkpoint                             | **已新增** |
| `README.md` Round 2 进度                                          | **已更新** |
| `.trellis/spec/backend/datasource-adapters.md` 分层规矩           | **已更新** |
| 测试 `test_cninfoAdapter_unpublished_returnsNotPublishedYet` 命名 | **已更正** |
| `test_payloadRetryCount_propagatesToFetchResultAndFetchLog`       | **已补**   |

## P2 / P3 — 不修复（已文档化）

| ID                    | 处置                      | 阶段                 |
| --------------------- | ------------------------- | -------------------- |
| P2-1 adapter metadata | defer                     | Batch C/D            |
| P2-2 Trellis 归档瘦身 | 建议项                    | 流程                 |
| P2-3 CI 可见性        | 已复核 PR #2 Actions 通过 | —                    |
| P3 上帝类拆分规矩     | spec Design Decision      | Batch C/D 实现时遵守 |
| npm audit CI          | 非 Python 本批范围        | —                    |

---

## 延后台账（项目级汇总）

### Round 2 核心（`DECISIONS.md` §9）

| ID             | 阶段                |
| -------------- | ------------------- |
| GPT-P1-5-DB    | Batch C 前          |
| GPT-staging-DB | Batch C             |
| GPT-P2-2       | Batch D             |
| GPT-init_db    | Batch D             |
| GPT-P3-6       | Batch D             |
| GPT-SEC-CI     | Batch B 并行 sprint |
| A2-shrink      | Info 可选           |

### Batch B 审计延后（`DECISIONS.md` §10）

| ID                                     | 阶段         |
| -------------------------------------- | ------------ |
| B-D2 类型别名统一                      | Batch C      |
| B-D3 Port 凭证/错误消息                | Batch C/D    |
| B-D4 as_of ISO 校验                    | 按需 Batch C |
| B-P2-1 adapter metadata                | Batch C/D    |
| B-P2-2 Trellis 瘦身                    | 流程建议     |
| B-P1-6-full Orchestrator ResourceGuard | Batch D      |

### Round 0/1

| 项                                      | 阶段                   |
| --------------------------------------- | ---------------------- |
| ResourceGuard + ingestion smoke         | Batch D（同 GPT-P3-6） |
| `verify_applied_checksums` dedicated 测 | 已知限制               |

---

## 验收命令

```powershell
pytest tests/test_adapter_skeletons.py tests/test_data_adapter_contract.py -q
pytest -q --cov=backend --cov-fail-under=75
ruff check backend/app/datasources tests/test_adapter_skeletons.py
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
```
