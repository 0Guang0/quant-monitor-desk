# Execute Boot — round2-batch-b-adapters

> Protocol v2 追溯补录 · Execute 已完成后代际对齐

## AC 摘要（MASTER §2）

- AC-1..10：五 adapter + factory；SUCCESS raw + content_hash；PortError 映射；QMT AUTH+SUCCESS；无 WriteManager；FileRegistry 对齐；cninfo EMPTY_RESPONSE；cov ≥75%

## §8 执行顺序

8.0 stub → 8.1 FetchPort/Skeleton → 8.2 Baostock → 8.3 QMT → 8.4 Akshare/Cninfo → 8.5 Yahoo/factory → 8.6 回归

## Red Flags（MASTER §7）

- FileRegistry 与 raw 路径不一致
- SUCCESS 无 content_hash
- 水平切片跨 §8 步（§8.2–8.5 历史 process debt）

## §10 验收命令清单

- pytest -q --cov=backend --cov-fail-under=75
- ruff / compileall / grep WriteManager
- init_db×2 + ci_ingestion_smoke @ data/
- audit-sandbox 独立验证

## Execute 模式

**trellis-implement: inline**（主会话 Execute，用户指令 task.py start）

## Phase 0 complete
