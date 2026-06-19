# 036_create_final_release_manifest 创建最终发布清单

## 1. 任务目标

生成可验证的 MANIFEST、FINAL_AUDIT_REPORT、最终 zip 验收。

## 2. 预期结果

完成后，Claude Code / Codex 应能在不依赖上下文记忆的情况下，依据本任务和输入文件完成对应模块的可运行实现或可验证骨架。

## 3. 输入文件

- `docs/quality/final_package_rules.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `docs/quality/staged_acceptance_policy.md`
## 4. 相关代码 / 输出文件

- `scripts/create_release_manifest.py`
- `MANIFEST.json`
- `FINAL_PACKAGE_MANIFEST.md`
- `FINAL_AUDIT_REPORT.md`

## 5. 现有模式 / 参考

- 遵循 `docs/architecture/03_runtime_flows.md` 中的运行链路。
- 遵循 `docs/architecture/04_data_architecture.md` 中的数据分层。
- 遵循 `docs/quality/final_package_rules.md` 中的最终包规则。
- 任何写入 clean table 的行为都必须经过 `DuckDBWriteManager`。
- 任何重任务都必须先通过 `ResourceGuard`。

## 6. 技术约束

- 后端优先使用 Python、FastAPI、Pydantic、DuckDB、Parquet、Polars Lazy。
- 前端使用 Vite + React + TypeScript；页面布局只是占位，正式实现前必须提醒用户确认。
- 配置与契约使用 YAML / JSON / SQL / Markdown。
- 不允许新增未经用户确认的大型依赖。

## 7. 资源约束

- 默认运行模式为 `eco`。
- 不允许全市场全历史扫描作为默认行为。
- 不允许无分页 API 或 Agent 大查询。
- 如果触发 `RESOURCE_GUARD_PAUSED`，必须停止非核心任务并汇报原因。

## 8. 边界约束

- 不得恢复 `Primary / Shadow / Emergency` 旧口径。
- 不得输出交易动作语义。
- 不得绕过 `WriteManager`。
- 不得把 Agent 文本当作事实来源。
- 不得固定死前端最终页面设计。
- 不得修改与本任务无关的金融语义和 spec。

## 9. 实现步骤

- manifest hash 完整
- 最终自检通过
- 生成 docs_split_final.zip
- 先写或补充最小测试 / smoke test，再实现。
- 运行本任务验收命令。
- 汇报改动文件、测试结果、未完成项、资源保护状态。

## 10. 测试要求

- 只 mock 外部 I/O，例如数据库、HTTP、文件系统、消息队列。
- 纯计算逻辑和条件分支必须使用真实值。
- 每个测试至少包含一个业务语义断言。
- 禁止只用 `assertNotNull` 或 `assertDoesNotThrow` 作为唯一断言。
- 测试命名建议：`functionName_condition_expectedBehavior`。

## 11. 验收命令
本任务为文档/发布规则类任务，不强制运行 full test suite。验收命令：

```bash
uv sync --locked
uv run python scripts/check_doc_links.py
uv run python scripts/check_docs_consistency.py
uv run python scripts/validate_release_allowlist.py
```

若相关脚本尚由本任务创建，则先运行脚本自身单元测试，再在任务完成后运行上述命令。

## 12. 完成标准

- 本任务列出的输出文件已创建或更新。
- 测试命令通过，或明确说明未运行原因和阻塞项。
- 没有生成临时 round report、scratch、tmp 或一次性 self-check 文件。
- 没有引入与现有 docs/specs/contracts 冲突的口径。

## 13. Red Flags

出现以下情况必须停止并修正：

- 为了完成本任务修改了无关模块。
- 跳过测试并声称“看起来没问题”。
- 前端页面布局被当作最终设计写死。
- Agent 能自由 SQL、自由联网或直接写库。
- 大查询未经过 ResourceGuard。
- 测试只验证方法调用，不验证业务结果。

## 14. 输出要求

执行完成后只输出：

1. 改动文件清单。
2. 新增文件清单。
3. 删除文件清单。
4. 测试命令和结果。
5. ResourceGuard 是否触发。
6. 未完成项或需要用户确认的点。

## 15. 审计修复补充要求

`MANIFEST.json` 是本任务输出，不是必需输入。生成时必须：

- 遍历最终包全部正式文件。
- 记录除 MANIFEST.json 以外全部正式文件的 path、size、sha256；MANIFEST.json 不记录自身 sha256。
- 记录生成时间、工具版本和根目录名。
- 与 cleanup allowlist 交叉验证。
- 输出 `FINAL_AUDIT_REPORT.md`，说明未包含源码/测试结果时只能做文档级审计。

### 用户决策补充：D-01

用户已拍板：Python 默认使用 uv.lock；任务实现与 CI 默认使用 uv sync / uv run；pip-tools 仅备用，不采用 Poetry。

### 用户决策补充：D-07

用户已拍板：Trellis/Cursor 每轮只长期保留 MASTER/AUDIT/DECISIONS；细碎 evidence 归档到 artifacts zip。

### 用户决策补充：D-10

用户已拍板：设计包保持 docs/specs/tasks 轻量包；源码与测试结果通过 Git commit + CI 结果终审。


## 16. MANIFEST 自身 hash 策略

`MANIFEST.json` 不得把自身作为普通文件条目写入 sha256。发布脚本必须采用 exclude-self policy：

```text
MANIFEST.json 不出现在 files[] 中；
files[] 只记录其他正式文件；
顶层写 manifest_self_policy: exclude_self_from_file_hashes；
顶层写 file_count_excluding_manifest；
```

必须新增测试：`test_manifestSelfHashPolicy_isVerifiable`、`test_finalAuditReport_isAllowlisted`。
