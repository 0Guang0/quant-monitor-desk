# S7 写入热路径 · 静态安全体检

> **范围：** `write_manager.py` · `source_registry.py` · 接缝 `sql_identifiers` · `error_redaction` · `validation_gate`  
> **方法：** GitNexus impact/context + 静态读码（vuln-scan / security-and-hardening）  
> **性质：** 静态候选，**非**执行验证 PoC

## 摘要

| 指标     | 值                                             |
| -------- | ---------------------------------------------- |
| 扫描焦点 | 4 区                                           |
| 源文件   | 2 主文件 + 3 接缝                              |
| **发现** | **0** HIGH / **0** MEDIUM / **0** LOW 可报告项 |
| Triage   | 无需 `/triage`（无 findings 条目）             |

---

## 信任边界（威胁模型简表）

| 边界              | 不可信输入从哪来                                                | 保护在哪                                                               | STRIDE 要点                                       |
| ----------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------- |
| **Registry YAML** | 磁盘 `specs/datasource_registry/*.yaml`（运维/发布产物）        | `yaml.safe_load` + 严格类型解析 + `_validate_bound_source` fail-closed | **T**：篡改 YAML 可改路由，需文件写权限（运维面） |
| **WriteRequest**  | 编排器内部构造（sync/layer/staged_pilot），**非** HTTP 直传表名 | `quote_ident` 蛇形标识符白名单；`ValidationGate` 写前门禁              | **I**：失败路径 `redact_error_message` 落库       |
| **DuckDB SQL**    | 表/列名经 `quote_ident`；审计 INSERT 参数化                     | `_validated_tables` 先于动态 SQL                                       | **I**：SQL 注入需先绕过标识符白名单（当前无路径） |

**资产：** clean 表数据完整性、写入审计链、源路由矩阵可信度。

---

## 分区结论

### 1. WriteManager（写入）

- **SQL 注入：** 动态 SQL 仅拼接 **已引用标识符**（`quote_ident`：`^[a-z][a-z0-9_]{0,62}$`）；`write_audit_log` INSERT 全参数化。**无报告项。**
- **授权：** `DbValidationGate` 要求有效 `validation_report_id`；降级写入需 `source_role` + `quality_flags` 等证据字段。**设计内控，非漏洞。**
- **信息泄露：** `FAILED`/`ERROR` 审计与 sidecar 经 `redact_error_message`；未知异常 bare `raise` 不额外落库。**可接受。**
- **性能（observability）：** `_apply_staging_to_clean` 成功路径 2× `COUNT(*)` — 批写入可接受；**无证据表明需优化**（performance-optimization：先度量再改）。

### 2. SourceRegistry（注册表）

- **反序列化：** `yaml.safe_load`（非 `load`）。**无报告项。**
- **域角色：** S7 `_validate_bound_source` 与重构前守卫等价；错误文案锁定于 `test_source_registry`。**无报告项。**
- **sync_to_db：** 全参数化 UPSERT。**无报告项。**

### 3. GitNexus 爆炸半径（改前参考）

| 符号                     | 风险       | 说明                                |
| ------------------------ | ---------- | ----------------------------------- |
| `_execute_write`         | LOW        | 直接 caller 仅 `write()`            |
| `_validate_bound_source` | CRITICAL\* | \*经 `load()` 扇出；无公开 API 变更 |

---

## 防御纵深观察（非漏洞 · 可选后续）

| 观察                               | 严重度   | 建议                                                                                                |
| ---------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| Registry YAML 无运行时签名校验     | 运维面   | 依赖 CI/发布流程；超出 S7 范围                                                                      |
| `WriteRequest` 表名信任内部调用方  | 设计选择 | 保持编排器为唯一构造点；勿从 CLI 直传表名                                                           |
| 无结构化安全事件日志（仅 DB 审计） | 可观测性 | 按 observability skill：未来在 `write()` 边界加 `event=write_failed` 结构化日志（**未在本票实现**） |

---

## 下一步

- 静态扫描：**无需** `/triage`（0 findings）
- 若需执行验证：见项目 `vuln-pipeline`（本扫描不执行目标代码）
- 功能回归：`uv run pytest tests/test_write_manager*.py tests/test_source_registry.py -q`
