# Frontend Security, Session, Cache, Pagination, and Error Boundary Policy

## 1. 目的

修复 QM-AUD-018：前端必须有 CSP、会话边界、错误边界、缓存和分页策略，同时不写死最终 UI 设计。

## 2. 安全基线

- 默认 Content-Security-Policy：禁止 inline script，禁止任意外部域。
- API token 不得写入 localStorage；本地版优先使用内存态或安全 cookie。
- 前端不得拼接 SQL 或自由 query。
- 所有富文本/新闻/公告摘要必须按纯文本渲染，禁止直接注入 HTML。

## 3. 分页与缓存

- 所有列表请求必须分页。
- 默认 `page_size=200`，绝对上限 `<=1000`；唯一权威是 `specs/contracts/api_security_contract.yaml`。
- 缓存必须带 source_used、as_of_timestamp、data_freshness。
- stale 数据必须显示 FreshnessLabel，不能静默当作最新。

## 4. 错误边界

每个主页面必须有 ErrorBoundary：

- 显示错误摘要。
- 提供重试按钮。
- 不泄露 token、本机绝对路径、secret。
- 记录前端 error event。

## 5. UI 决策边界

页面布局、视觉风格、交互方式只是占位。正式实现前必须提醒用户亲自确认，不得把当前文档中的页面结构当作最终设计。


## API 安全与分页权威口径

`specs/contracts/api_security_contract.yaml` 是唯一机器契约。第一版采用本地 Bearer token：dev 可关闭但只能绑定 loopback；prod 必须启用 `QMD_API_TOKEN`，且单个本地 token 在第一版视为 `admin`。`viewer` 与 `agent_readonly` 角色保留为第二阶段能力，不得在第一版伪实现半套 RBAC。

分页统一口径：默认 `page_size=200`，绝对上限 `1000`，Agent tool 最大行数 `1000`，full-history 查询必须 admin。实现必须补 `test_pageSizeContract_matchesDocs`。
