# GitNexus + CodeGraph Audit 摘要 — Round 0（7.pre · 2026-06-17）

> **7.pre 产出** · 双工具 CLI 已验证 · 派发 A1–A8 前

## 工具状态

| 工具 | 命令 | 结果 |
|------|------|------|
| GitNexus | `npx gitnexus status` | ✅ up-to-date · 2136 nodes · commit 7848873 |
| GitNexus | `npx gitnexus query "FastAPI health scaffold project structure"` | ✅ 命中 main.py, test_global_execution_rules, test_project_scaffold, test_backend_smoke |
| GitNexus | `npx gitnexus context health` | ✅ health → calls get_resource_profile |
| CodeGraph | `npx @colbymchenry/codegraph status` | ✅ 881 nodes · 106 files |
| CodeGraph | `npx @colbymchenry/codegraph explore "FastAPI health scaffold"` | ✅ main.py health + config.get_resource_profile 链 |
| CodeGraph | `npx @colbymchenry/codegraph node health` | ✅ GET /health route · calls get_resource_profile |

MCP：`~/.cursor/mcp.json` 含 **gitnexus** + **codegraph**（`codegraph serve --mcp`）。

## 相对 Execute 的增量（Audit 视角）

| 关注点 | GitNexus | CodeGraph |
|--------|----------|-----------|
| 入口 | `Function:backend/app/main.py:health` | `health` L17 · blast radius 1 caller |
| 配置 | config.py 在 query 结果中 | `get_resource_profile` eco 默认 |
| 测试链 | test_backend_smoke → health | test_backend_smoke 覆盖 app import |
| Round 0 边界 | 无 db/ 写入路径 | layer1-5 空包占位 |

## 关键调用链

```text
GET /health → health() → get_resource_profile()  [GitNexus context + CodeGraph node]

test_global_execution_rules → GLOBAL_*.md 存在性
test_project_scaffold → backend/ frontend/ specs/ docs/ 目录
test_backend_smoke → FastAPI TestClient /health
```

## 各维度 agent 提示

| 维 | GitNexus | CodeGraph |
|----|----------|-----------|
| A1 | query scaffold + check.jsonl vs implement.jsonl | explore main/config · files 结构 |
| A2 | — | explore layer 占位包是否 bloat |
| A3 | — | node health · 无密钥 rg 已扫 |
| A5 | AC-1..5 ↔ 上表 test 文件 | node 追溯 test_* |
| A7 | — | compileall ×2 exit 0（已跑） |
| A8 | — | pytest basetemp round0 全绿（已跑） |

## 7.pre 完成

主会话已运行 **GitNexus + CodeGraph** CLI；维度 agent 须读本文件 + 各至少 1 次 query/explore，结论写入 audit.report §3.x。
