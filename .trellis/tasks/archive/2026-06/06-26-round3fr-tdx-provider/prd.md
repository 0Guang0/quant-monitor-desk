# PRD — R3FR-03 TDX Provider Refactor

> 薄索引：正文见 `EXECUTION_INDEX.md` + 冻结后将生成的 `frozen/R3FR_03_TDX_PROVIDER_REFACTOR.md`。

## 问题

`TdxPytdxProbeFetchPort` 把 pytdx 连接与 equity daily fetch 写在 probe 邻接模块里，难以让 Round 3G audit 把 TDX 当作 **excluded/disabled provider** 推理，而非松散 probe wrapper。

## 目标

完成 QMD 自有的 disabled/raw-only provider port 形态，覆盖 `security_list`、`cn_equity_daily_bar`、`cn_index_daily_bar` 三操作，带显式 caps 与授权。

## 非目标

- 生产 clean write
- 默认 live / 全市场扫描 / 分钟线
- QMT/xqshare 启用
- 从 EasyXT 复制 auto-login 或 trading 语义

## AC 摘要

| ID        | 结果                                               |
| --------- | -------------------------------------------------- |
| AC-TDX-01 | 缺 `pytdx` → `DISABLED_SOURCE`，不崩溃             |
| AC-TDX-02 | live 须显式 authorization；默认 mocked/disabled    |
| AC-TDX-03 | 拒绝 full-market / minute / 超 cap 请求            |
| AC-TDX-04 | fetch 结果带 raw evidence + content/schema hash    |
| AC-TDX-05 | 无 `参考项目/**` runtime import；guardrails 测试绿 |
| AC-TDX-06 | registry/capability caps 与任务卡一致              |

## 用户批准点

- Plan 冻结后 `task.py start` 方可 Execute
- live manual probe 仍须项目授权 MD + 占位 host 解除（既有 B01-TDX 政策）
