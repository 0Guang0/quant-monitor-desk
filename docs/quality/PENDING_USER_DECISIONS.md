# 用户已拍板决策记录（D-01 至 D-12）

本文件原名保留为 `PENDING_USER_DECISIONS.md`，但状态已经从“待拍板”更新为“已拍板”。执行角色不得再把以下事项作为待确认项反复询问用户；只有当实现中发现与这些决策冲突、需要改变已确认口径时，才需要重新请用户确认。

> 决策来源：用户上传的 `待用户拍板决策点汇总(1).md`。本轮已把 D-01 至 D-12 写入对应的 README、契约、模块文档、运维文档和 implementation task。

## D-01 Python 依赖锁文件选择：已确认

**拍板结果**：采用 `uv.lock` 作为 Python 主锁文件。`requirements.lock` / pip-tools 仅作为“用户不想安装 uv 时的备用方案”，不作为默认实现路径。`poetry.lock` 第一版不采用。

执行规则：

```text
默认命令：uv sync / uv run pytest / uv run ruff check .
CI 与 Claude Code / Codex 默认按 uv.lock 还原 Python 环境。
执行任务不得改成 Poetry 项目结构，除非用户重新拍板。
```

## D-02 API 鉴权默认模式：已确认

**拍板结果**：采用“dev 可关闭、prod 必启”的本地 Bearer token 模式。第一版不做完整 OAuth。

执行规则：

```text
dev 模式：允许关闭 token，但只能绑定 127.0.0.1。
prod 模式：必须启用 token。
prod 模式：没有 QMD_API_TOKEN 直接启动失败。
prod 模式：不允许绑定 0.0.0.0 且关闭鉴权。
```

## D-03 Secret 存储方式：已确认

**拍板结果**：第一版使用 `.env.local`；只提交 `.env.example`。OS keyring 作为后续多人/长期使用增强，不在第一版强制实现；云密钥服务第一版不采用。

执行规则：

```text
仓库只允许提交 .env.example。
.env.local、.env、*.secret、*.key 必须进入 .gitignore。
prod 启动时必须检查必需 secret 是否存在。
日志、报告、Agent 输出不得打印 secret 原文。
CI 必须加入 secret scan。
必须提供 secret 泄露后的 rotate 指南。
```

## D-04 Notification 渠道第一版启用范围：已确认

**拍板结果**：第一版默认启用前端 Notification Center；邮件作为可选渠道；不启用多 webhook。

执行规则：

```text
默认渠道：dashboard / frontend notification center。
可选渠道：email，但必须用户显式配置 SMTP/收件人。
禁止第一版默认启用多 webhook、短信、电话、群机器人。
```

## D-05 Raw / Audit / Report 留存周期：已确认

**拍板结果**：第一版选择低空间策略：raw 1 年、audit 1 年、report 1 年，并提供手动归档按钮/CLI。

执行规则：

```text
raw 文件默认保留 1 年。
audit log 默认保留 1 年。
report snapshot 默认保留 1 年。
删除前必须支持用户手动 archive/export。
secret-like payload 不得保存原文。
```

## D-06 Migration rollback 策略：已确认

**拍板结果**：选择“破坏性变更用备份恢复，非破坏性变更可以无 down SQL”。不要求每个 migration 都写 down SQL；不允许完全不支持恢复。

执行规则：

```text
破坏性 migration 必须先生成备份。
非破坏性 migration 可无 down SQL，但必须写 down_not_supported_reason。
失败时优先 rollback；无法 rollback 时恢复 pre_migration_backup_path。
禁止无备份执行破坏性 schema change。
```

## D-07 过程材料长期入库策略：已确认

**拍板结果**：每轮只保留 MASTER / AUDIT / DECISIONS；细碎 evidence 归档到 zip/artifacts；不全量长期堆在主仓库。

执行规则：

```text
保留：任务卡、审计结论、决策记录、关键执行清单。
细碎 red/green log、截图、临时证据、skill reads 归档到 artifacts zip。
最终设计包和 release zip 不得保留 scratch/tmp/round progress 噪音。
```

## D-08 前端 UI 是否先设计再实现：已确认

**拍板结果**：正式实现前必须提醒用户确认页面信息架构和交互方式。当前文档中的页面布局只作为占位/参考，不允许写死为最终 UI。

执行规则：

```text
前端必须展示哪些内容可以写入契约。
页面布局、颜色、排版、交互方式不得固定死。
开始真正实现 UI 前，Claude Code / Codex 必须提醒用户确认 UI 信息架构。
```

## D-09 Layer 1 标准化字段扩展范围：已确认

**拍板结果**：完整标准化字段仅用于 Layer 1；Layer 2-5 不全量复制 Layer 1 字段，后续按需局部扩展。

执行规则：

```text
Layer 1 保留 raw_value、z_score、delta、percentile、state、解释含义等完整标准化字段。
Layer 2-5 使用各自业务字段，不默认复制 Layer 1 全套标准化字段。
如 Layer 2-5 某个字段确需标准化，必须在对应 layer contract 中按需声明。
```

## D-10 源码/测试结果是否合入最终设计包：已确认

**拍板结果**：设计包保持轻量，只放 docs/specs/tasks；源码在独立 Git repo；实现后用 Git commit + CI 结果做终审。

执行规则：

```text
设计包不内置 backend/frontend/tests 实现源码。
执行角色完成实现后必须提交 Git commit、CI 结果、测试输出和锁文件。
最终实现级审计以源码 repo commit 为准，不以设计包 zip 为准。
```

## D-11 第一版 source_registry 是否启用 QMT：已确认

**拍板结果**：QMT 第一版默认禁用，用户配置并确认本机授权后再启用。

执行规则：

```text
qmt_xtdata enabled_by_default=false。
QMT adapter 不得默认启动或自动尝试连接本机终端。
启用前必须检查本机 QMT 环境、账号授权、路径配置和用户确认。
```

## D-12 Agent 新闻/文本来源是否固定：已确认

**拍板结果**：Agent 只能读取固定 source adapter 与用户手动导入文本；禁止 Agent 自由联网搜索。

执行规则：

```text
允许：固定来源 adapter、人工导入文本、已登记本地文档。
禁止：Agent 自由联网搜索、临时浏览未知网页、把 LLM 输出当事实源。
所有 Agent 解释必须基于 facts_used_json / evidence_ids。
```

## 最终说明

D-01 至 D-12 已全部关闭，不再作为“未决项”。执行角色若遇到新的架构选择，必须新增 D-13+ 决策项并用同样方式说明选择、区别、影响和建议，再交由用户拍板。
