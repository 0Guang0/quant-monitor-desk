# 代码智能工具 setup（已验证 · 2026-06-17）

> Round 0/1 Audit 7.pre 与 A1–A8 必读

## 根因：此前 GitNexus 失败

1. **沙箱默认无网络** — `npx` 无法下载 gitnexus 包  
2. **未建索引** — 从未在本仓库运行 `gitnexus analyze`  
3. **MCP 未配置** — `~/.cursor/mcp.json` 不存在  

## 一键恢复

```bash
# 仓库根目录
cd quant-monitor-desk

# GitNexus：建索引（需网络）
npx gitnexus analyze
npx gitnexus setup          # 写入 ~/.cursor/mcp.json + skills

# CodeGraph：建索引 + MCP
npx -y @colbymchenry/codegraph init
npx -y @colbymchenry/codegraph install -y --target cursor

# 验证
npx gitnexus status
npx -y @colbymchenry/codegraph status
```

## MCP 配置（`C:\Users\Guang\.cursor\mcp.json`）

- **gitnexus** — `gitnexus mcp`（全局已索引仓库）  
- **codegraph** — `codegraph serve --mcp --path ${workspaceFolder}`  

修改 MCP 后需 **重启 Cursor**。

## CLI 查询（Audit 必用 · 两工具各 ≥1 次）

| 用途 | GitNexus | CodeGraph |
|------|----------|-----------|
| 概念搜索 | `npx gitnexus query "WriteManager audit"` | `npx -y @colbymchenry/codegraph explore WriteManager` |
| 符号 360° | `npx gitnexus context WriteManager` | `npx -y @colbymchenry/codegraph node apply_migrations` |
| Round 0 脚手架 | `npx gitnexus context health` | `npx -y @colbymchenry/codegraph node health` |

## 索引目录（已 gitignore）

- `.gitnexus/` — GitNexus 图数据库  
- `.codegraph/` — CodeGraph SQLite  

## Audit 污染隔离

- Execute 验收库：`data/`  
- Audit 写库/CLI：**`.audit-sandbox/data`** 或 `.audit-sandbox/round0/`  

详见 [complex-task-planning-protocol.md](./complex-task-planning-protocol.md) §2.10。
