# Staging 数据端到端运行手册（R3F-CLI-05）

> **范围：** 用户授权的 **staging** 浸泡测试，用于补齐 vendor fetch 缺口（`R3-AUDIT-DEF-02`）。  
> **默认：** 仅 mock/fixture 或 dry-run — **默认不做 live fetch**。  
> **不在范围：** production-live 就绪、`source_health_snapshot` 写入、QMT/Yahoo/xqshare 自动启用。

---

## 1. 前置条件

| 检查项           | 命令 / 产物                                                  |
| ---------------- | ------------------------------------------------------------ |
| 可编辑安装       | `uv sync --locked`                                           |
| DB + registry    | `uv run qmd-init-db --sync-registry`                         |
| 路由预览（只读） | `uv run qmd-data data route-preview --domain market_bar_1d`  |
| 同步 dry-run     | `uv run qmd-data data sync --domain market_bar_1d --dry-run` |

## 2. 授权的 live staging（仅 opt-in）

Live vendor fetch 需要**显式**运维授权 YAML（见 `production_live_pilot_policy.md`）。  
**B3F-CLI 默认不执行 live fetch。**

存在授权时：

1. 导出所需环境变量（例如宏观试点仅需 `FRED_API_KEY` — 非通用 `qmd data`）。
2. 运行 route-preview，确认 `route_status=READY`。
3. CI 使用 fixture 测试：`uv run pytest tests/test_vendor_fetch_e2e.py -q`。
4. 证据写入 `.audit-sandbox/staging-e2e/` — 禁止变更生产 DB。

## 3. CI 单行命令（无 live）

```powershell
uv sync --locked
uv run qmd-init-db --sync-registry
uv run pytest tests/test_qmd_data_cli.py tests/test_vendor_fetch_e2e.py -q
```

## 4. 失败处理

CLI 失败须打印 `error_code`、`message`、`docs_anchor`，见 `docs/ops/ERROR_CODE_GUIDE.md`。

## 5. 负面保证

- 本手册流程不创建 `source_health_snapshot` 表。
- 未经单独运维审批工作流，禁止 `--no-dry-run` sync。
- Staged 证据 ≠ production-live。

## 6. R3G-03 有限生产 promote（运维 CLI）

> **CLI：** `uv run qmd-data data sandbox-clean-write promote`（非 `qmd`）。  
> **默认：** `--dry-run` — 除非 `--execute --no-dry-run`，否则不变更生产。

| 门禁      | 要求                                                                                                                                              |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 四重锁    | `--approval-file`、`--audit-decision`、`--before-proof`、`--rollback-plan` 路径须与授权 YAML 中 `audit_decision_file` / `rollback_plan_path` 一致 |
| 生产 DB   | `production_db_path` 仅能在 `DATA_ROOT` 或 `.audit-sandbox` 下                                                                                    |
| 执行      | `before_proof` 中 `backup_or_snapshot_pointer` 非空                                                                                               |
| FRED live | 仅当授权设 `live_fetch_authorized: true` 时，才加 `--allow-live-fetch` + `--fred-authorization`                                                   |

Dry-run 验证：

```powershell
uv run pytest tests/test_round3g_limited_production_clean_write.py `
  tests/test_round3g_limited_production_rollback.py `
  tests/test_reference_adoption_guardrails.py -k r3g03 -q --basetemp=.audit-sandbox/pytest
```
