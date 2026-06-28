# A3 Security Audit — R3H-06 Clean Schema

| 字段     | 值                                                                                             |
| -------- | ---------------------------------------------------------------------------------------------- |
| 维度     | A3 Security                                                                                    |
| 任务     | `06-29-round3h-r3h06-clean-schema`                                                             |
| 分支     | `feature/round3h-r3h06-clean-schema`                                                           |
| HEAD     | `ed0981c1`                                                                                     |
| 审计日期 | 2026-06-29                                                                                     |
| 模式     | 只读 · 静态 + pytest 证据（不 commit）                                                         |
| 模板     | `agents/security-auditor.md` + `agents/audit-adversarial-authority.md` + `AUDIT.plan.md` §1 A3 |

---

## Summary

| 等级          | 数量 |
| ------------- | ---- |
| Critical (P0) | 0    |
| High (P1)     | 0    |
| Medium (P2)   | 2    |
| Low (P3)      | 3    |
| Info          | 2    |

**Verdict: PASS** — promote 信任边界、主库 denylist、cninfo 非 bar 写入、approval 四件套 fail-closed 均有代码与 pytest 证据。无 BLOCKING 项；P2/P3 为纵深防御与后续 Wave hardening，不阻塞本卡 CLOSED。

---

## A3 覆写通过条件（AUDIT.plan §1）

| 条件                    | 结果     | 证据                                                                                                          |
| ----------------------- | -------- | ------------------------------------------------------------------------------------------------------------- |
| cninfo 无 bar 形写入    | **PASS** | `test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty` + `_production_clean_write` 后验 `security_bar_1d` 行数 |
| 禁止主库 mutation proof | **PASS** | `_assert_production_db_allowed` 三路径 denylist；dry_run `key_table_row_counts` 对比                          |
| fail-closed             | **PASS** | A3 点名子集 5/5；全套件 65/65（见 Pytest 节）                                                                 |

---

## 威胁表（STRIDE × 信任边界）

| 信任边界                                     | 威胁 (STRIDE)                     | 控制 / 缓解                                                                                                       | 证据                                                                                                                         | 残余风险                                               |
| -------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Approval YAML → `validate_approval_contract` | 篡改四件套绕过写库 (T)            | approval/audit 字段逐项对齐；`no_agent_triggered_write` / `no_cap_expansion` 硬拒；cap 契约                       | `approval_contract.py:206-271`；`test_ApprovalContract_*`                                                                    | 低 — 缺 execute 层 domain↔target 对抗测（O-04）        |
| `production_db_path`                         | 写主库 `quant_monitor.duckdb` (E) | `_assert_production_db_allowed` 三路径 denylist；`_assert_within_data_root`；`validation_only` 源限 pilot/sandbox | `limited_production_entry.py:128-182`；`test_PromoteRunner_refusesCanonicalProductionDbPath`                                 | 低 — `resolve()` 后仍命中 canonical 集合               |
| Promote execute → WriteManager               | 绕过 WM/ValidationGate (T)        | 必经 `DbValidationGate` + `WriteManager.write`；dry_run 禁 mutation + key_table 对比                              | `limited_production_entry.py:517-604,738-745`                                                                                | 低                                                     |
| `target_table` 用户输入                      | SQL 注入 (T)                      | `quote_ident` snake_case allowlist                                                                                | `sql_identifiers.py:14-18`；`approval_contract.py:96-102`；`test_ApprovalContract_invalidTargetTableSql_blocks`              | 极低                                                   |
| `domain` → clean 表                          | cninfo 写 bar / 域错表 (T)        | `resolve_clean_write_target` SSOT；execute 校验 `target_table == router`；metadata 域后验 `security_bar_1d` 行数  | `clean_write_targets.py:24-47`；`limited_production_entry.py:540-603`；`test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty` | 低                                                     |
| Migration 013/014                            | DDL 注入 (T)                      | 静态 SQL 文件 + checksum 校验；非运行时拼接                                                                       | `migrate.py`；`013_clean_domain_tables.sql`                                                                                  | 无 — 无用户可控 DDL                                    |
| `pdf_file_id` / `announcement_url`           | 指针滥用 / 未来 SSRF (T/I)        | 列仅存 VARCHAR；无 DB FK；当前不抓取 URL                                                                          | `013_clean_domain_tables.sql`；`rehearsal_loader.py:301-305`                                                                 | 中低 — pilot 内可挂任意指针（F-02）                    |
| 主库 mutation proof                          | 旁路写库未检测 (I)                | `build_production_mutation_proof` + KEY_TABLES；`security_bar_1d` 已入契约                                        | `mutation_proof.py:79-141`；`ops_db_inspect_contract.yaml:184-185`                                                           | 中低 — `cn_announcement_clean` 未入 KEY_TABLES（F-01） |
| Rehearsal sandbox DB                         | 误写 canonical 主库 (E)           | `assert_sandbox_db_allowed` 同三路径 denylist                                                                     | `rehearsal_runner.py:85-97`                                                                                                  | 低                                                     |
| Ops CLI                                      | 未授权写主库 (E)                  | `db-inspect` 契约禁 `--write`/`--migrate`；只读 open                                                              | `ops_db_inspect_contract.yaml`                                                                                               | 无本卡新增面                                           |
| 密钥 / token                                 | 泄露进 repo (I)                   | diff 区无新增明文密钥；env 读取既有 port                                                                          | `rg` 基线扫描 backend（排除 test）                                                                                           | 无本卡回归                                             |

---

## Findings

### [P2] F-01 — `cn_announcement_clean` 未纳入主库 mutation proof KEY_TABLES

- **等级:** NON-BLOCKING (P2)
- **BLOCKING:** 否
- **Location:** `specs/contracts/ops_db_inspect_contract.yaml:164-185`；`backend/app/ops/mutation_proof.py:32-37`
- **Description:** R3H-06 将 `security_bar_1d` 加入 `key_tables`，但 `cn_announcement_clean` 未加入。若存在 **plan 未覆盖的旁路写库**（非 promote 路径）写入主库 disclosure 表，`build_production_mutation_proof` / rehearsal 后验可能 **漏检行数变化**。
- **Impact:** 主库 disclosure 域静默污染；与任务卡「禁止主库 mutation」的 **证明完备性** 缺口，非 promote 路径已证明可写主库。
- **Proof of concept:** 假设未来某 CLI 直接 `INSERT INTO cn_announcement_clean` 于 `quant_monitor.duckdb`；rehearsal `key_table_row_counts` 对比不包含该表 → `proof_status` 仍可能 VERIFIED（若其它 key 表不变）。
- **Recommendation:** 将 `cn_announcement_clean` 加入 `ops_db_inspect_contract.yaml` `key_tables`；扩展 `test_ops_db_inspector` / mutation proof 回归。

---

### [P2] F-02 — `file_registry` 指针列无存在性 / 归属校验

- **等级:** NON-BLOCKING (P2)
- **BLOCKING:** 否
- **Location:** `backend/app/ops/sandbox_clean_write/rehearsal_loader.py:301-305`；`013_clean_domain_tables.sql`
- **Description:** `pdf_file_id` / `extracted_text_file_id` 在 promote 路径可写入任意 VARCHAR，不校验 `file_registry` 是否存在、类型是否为 `pdf`/`text`、hash 是否匹配。
- **Impact:** pilot 库内 **指针投毒** — 未来抓取/展示管道若信任 clean 指针，可能读到错误文件或越权路径（依赖 `file_registry.local_path` 治理）。
- **Proof of concept:** 构造 approval 允许 execute，staging 行设 `pdf_file_id='../../etc/passwd'`（或另一 tenant 的 file_id）；当前无校验即 upsert。
- **Recommendation:** Wave 3 前在 `populate_disclosure_from_bundle` 或 WriteManager 前增加可选校验：`SELECT 1 FROM file_registry WHERE file_id=? AND file_type IN (...)`；失败 fail-closed。

---

### [P3] F-03 — `announcement_url` 无 scheme 白名单

- **等级:** NON-BLOCKING (P3)
- **BLOCKING:** 否
- **Location:** `cn_announcement_clean.announcement_url` DDL；`DisclosureStagingRow.announcement_url`
- **Description:** URL 列无 `http(s)://` 限制或长度 cap。
- **Impact:** 当前仅存储；若未来 MCP/爬虫 **服务端 fetch** 该列 → SSRF 面。
- **Recommendation:** 入库前 `urllib.parse` 校验 scheme in `{http,https}`；内网 IP/localhost denylist。

---

### [P3] F-04 — `rehearsal_runner` COUNT 查询未 `quote_ident`

- **等级:** NON-BLOCKING (P3)
- **BLOCKING:** 否
- **Location:** `backend/app/ops/sandbox_clean_write/rehearsal_runner.py:287`
- **Description:** `con.execute(f"SELECT COUNT(*) FROM {target_table}")` 未引用 `quote_ident`。
- **Impact:** 当前 `target_table` 仅来自内部常量 / `resolve_clean_write_target` 硬编码表名，**不可利用**；属纵深防御缺口。
- **Recommendation:** 与 `limited_production_entry._quoted_table` 一致，统一 `quote_ident`。

---

### [P3] F-05 — domain↔target_table 不一致仅在 execute 拒绝，缺对抗测试

- **等级:** NON-BLOCKING (P3)
- **BLOCKING:** 否
- **Location:** `limited_production_entry.py:541-545`；`approval_contract.py:206-271`
- **Description:** 四件套可同时声明 `domain=cn_announcements` + `target_table=security_bar_1d`（字段内部自洽），`validate_approval_contract` 通过，直到 `_production_clean_write` 才抛错。
- **Impact:** 无安全绕过（execute fail-closed），但 **审计/运维误配** 仅在最后一刻失败，错误码非专用。
- **Recommendation:** 在 `validate_approval_contract` 或 `validate_r3g03_source_caps` 增加 `target_table == resolve_clean_write_target(domain).target_table`；补 `test_PromoteRunner_domainTargetMismatch_blocks`。

---

### [Info] F-06 — GitNexus 索引滞后于 R3H-06 新符号

- **等级:** Info
- **BLOCKING:** 否
- **Description:** `impact(_assert_production_db_allowed)`、`impact(resolve_clean_write_target)` 返回 **symbol not found**；索引未收录 `clean_write_targets.py` 新模块。
- **Recommendation:** 合并前运行 `node .gitnexus/run.cjs analyze` 刷新索引。

---

### [Info] F-07 — R3G-01 rehearsal bar 路径仍 `append_only` → `security_bar_smoke_clean`

- **等级:** Info（计划内 ponytail）
- **BLOCKING:** 否
- **Location:** `rehearsal_runner.py:237-241`
- **Description:** sandbox rehearsal 与 R3G-03 promote（`upsert_by_pk` → `security_bar_1d`）刻意分离；rehearsal 不写正式 clean 表。
- **Impact:** 无生产面；仅 sandbox 叠行风险，与 mass rehearsal 文档一致。

---

## 计划外发现

> 对抗性搜索：AUDIT.plan / frozen 卡 / 静态读 `limited_production_entry` + `approval_contract` + `clean_write_targets` + `rg` 基线 + GitNexus impact。

| ID   | 发现                                                                                  | 等级 | BLOCKING |
| ---- | ------------------------------------------------------------------------------------- | ---- | -------- |
| O-01 | `cn_announcement_clean` 未进 KEY_TABLES，主库 mutation proof 不完备                   | P2   | 否       |
| O-02 | `pdf_file_id` 无 `file_registry` 校验，指针可投毒                                     | P2   | 否       |
| O-03 | approval 阶段不校验 domain↔target_table，仅 execute 拒绝                              | P3   | 否       |
| O-04 | 无 execute 层 domain/target 错配专项 pytest                                           | P3   | 否       |
| O-05 | `announcement_url` 未来 SSRF 预留面                                                   | P3   | 否       |
| O-06 | GitNexus 未索引 R3H-06 新符号                                                         | Info | 否       |
| O-07 | 复用同一 `--basetemp` 目录时遗留 `.write.lock` 可导致 cninfo 测环境失败（非安全回归） | Info | 否       |

**DOUBT 三类扫描：**

| 类                      | 范围                | 结果                                                                       |
| ----------------------- | ------------------- | -------------------------------------------------------------------------- |
| 硬编码 URL              | `backend/` 非 test  | 仅既有 fetch port / 文档示例；本 diff 无新增                               |
| JWT/API key             | 同上                | 无新增明文；FRED 仍 `api_key_env`                                          |
| SQL 拼接                | promote 路径 + diff | `target_table` 已 `quote_ident`；`rehearsal_runner:287` 为内部常量（F-04） |
| `market_bar_clean` 残留 | `backend/`          | **零匹配** — 旧单表路由已清除                                              |

---

## 全部发现项汇总

| ID          | 标题                              | 等级 | BLOCKING | 文件锚点                               |
| ----------- | --------------------------------- | ---- | -------- | -------------------------------------- |
| F-01        | disclosure 表未入 KEY_TABLES      | P2   | 否       | `ops_db_inspect_contract.yaml:164-185` |
| F-02        | file_registry 指针无校验          | P2   | 否       | `rehearsal_loader.py:301-305`          |
| F-03        | announcement_url 无 scheme 限制   | P3   | 否       | `013_clean_domain_tables.sql`          |
| F-04        | rehearsal_runner 未 quote_ident   | P3   | 否       | `rehearsal_runner.py:287`              |
| F-05        | domain/target 错配缺契约层校验+测 | P3   | 否       | `limited_production_entry.py:541-545`  |
| F-06        | GitNexus 索引滞后                 | Info | 否       | GitNexus impact                        |
| F-07        | R3G-01 append_only smoke 表       | Info | 否       | `rehearsal_runner.py:237-241`          |
| O-01 … O-07 | 见计划外表                        | —    | 否       | —                                      |

---

## 静态命令证据

```text
# SQL 拼接基线（promote 相关已 quote_ident）
rg 'execute\(f' backend/app/ops/sandbox_clean_write/
→ limited_production_entry 使用 _quoted_table；rehearsal_runner:287 例外（F-04）

# market_bar_clean 清除门禁
rg market_bar_clean backend/
→ 零匹配（PASS）

# 密钥扫描
rg -i 'api[_-]?key|secret|token|password' backend/ --glob '!*test*'
→ 仅既有 env/port 读取；无本卡新增泄露
```

---

## Pytest fail-closed 证据

**环境说明：** 复用 `.audit-sandbox/pytest` 下同一 `test_cninfo_no_bar_promote_lea0` 目录时，遗留 `*.write.lock` 会导致 `WriteLockError`（前次异常退出残留，**非安全回归**）。使用独立 `--basetemp` 后全绿。

```bash
# 全套件（A8 同命令，独立 basetemp）
uv run pytest tests/test_r3h06_clean_schema.py \
  tests/test_round3g_limited_production_clean_write.py \
  tests/test_migration_coverage.py \
  -q --basetemp=.audit-sandbox/pytest-r3h06-a3
# → 65 passed

# A3 点名 fail-closed 子集
uv run pytest \
  tests/test_r3h06_clean_schema.py::test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty \
  tests/test_round3g_limited_production_clean_write.py::test_PromoteRunner_refusesCanonicalProductionDbPath \
  tests/test_round3g_limited_production_clean_write.py::test_ApprovalContract_invalidTargetTableSql_blocks \
  tests/test_round3g_limited_production_clean_write.py::test_PromoteRunner_productionDbOutsideDataRoot_blocks \
  tests/test_round3g_limited_production_clean_write.py::test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim \
  -v --basetemp=.audit-sandbox/pytest-r3h06-a3-sub
# → 5 passed
```

| 用例                                                                  | 证明的不变量                                                       |
| --------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty`                 | cninfo promote 不写 `security_bar_1d`；`cn_announcement_clean > 0` |
| `test_PromoteRunner_refusesCanonicalProductionDbPath`                 | 主库 `quant_monitor.duckdb` 路径硬拒                               |
| `test_ApprovalContract_invalidTargetTableSql_blocks`                  | 恶意 `target_table` SQL 注入 fail-closed                           |
| `test_PromoteRunner_productionDbOutsideDataRoot_blocks`               | DATA_ROOT 外路径拒绝                                               |
| `test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim` | dry_run 不可声称 mutation                                          |

---

## GitNexus

| 调用                                              | 结果                                   |
| ------------------------------------------------- | -------------------------------------- |
| `impact(_assert_production_db_allowed, upstream)` | **symbol not found**（索引滞后，F-06） |
| `impact(resolve_clean_write_target, upstream)`    | **symbol not found**                   |

---

## Positive Observations

- **三域路由 SSOT：** `clean_write_targets.py` 将 bar/disclosure/macro 硬编码为 `upsert_by_pk` + 正确 PK，消除 `market_bar_clean` 单表偏离。
- **主库 denylist 双层：** `limited_production_entry` 与 `rehearsal_runner` 均拒绝 canonical `quant_monitor.duckdb`（含 `DATA_ROOT` 与 `PROJECT_ROOT` 双解析）。
- **四件套 quadruple-lock：** approval/audit 字段对齐 + cap + rollback + `no_agent_triggered_write`。
- **cninfo 形写入后验：** execute 后强制 `security_bar_1d` 行数不变（`limited_production_entry.py:595-603`）。
- **identifier 卫生：** `quote_ident` snake_case allowlist 阻断 approval YAML 注入面。
- **dry_run 双保险：** `_production_clean_write` 在 `dry_run=True` 时跳过写库；`run_limited_production_entry` 另对比 `key_table_row_counts`（738-745）。

---

## Recommendations（后续 Wave，非本卡阻塞）

1. KEY_TABLES 补 `cn_announcement_clean` + mutation proof 测试。
2. disclosure promote 增加 `file_registry` 指针校验（可 feature-flag）。
3. `validate_approval_contract` 增加 domain↔target_table 静态一致性检查 + 对抗测。
4. 合并前 `gitnexus analyze` 刷新索引。
5. Wave 3 live fetch 前为 `announcement_url` 加 scheme/SSRF 护栏。
6. CI/audit 使用独立 `--basetemp` 或测试 teardown 清理 `.write.lock`，避免环境假红。

---

## Verdict

| 项                      | 结论                                           |
| ----------------------- | ---------------------------------------------- |
| **A3 AUDIT.plan §1**    | **PASS**                                       |
| cninfo 无 bar 形写入    | ✅ `test_cninfo_no_bar_promote` + 运行时后验   |
| 禁止主库 mutation proof | ✅ canonical denylist + dry_run key_table 对比 |
| approval 绕过           | ✅ 四件套 + cap + audit 对齐；无 P0/P1         |
| fail-closed             | ✅ pytest 5/5 点名 + 全套件 65/65              |
| BLOCKING OPEN           | **0**                                          |

**总裁决：PASS** — 可进入 A8 合并门禁；F-01/F-02 建议记入 Wave 3 hardening backlog，不作为 R3H-06 BLOCKING。
