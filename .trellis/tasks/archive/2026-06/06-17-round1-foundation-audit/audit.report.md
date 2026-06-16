# Audit Report — 06-17-round1-foundation-audit

> **状态：** Phase 7 Audit 完成（A1–A8 + A9）· 待 Phase 9 Finish

## 1. 元信息

| 字段 | 值 |
|------|-----|
| GitNexus 刷新 | 2026-06-17 · CLI query/context + MCP |
| CodeGraph 刷新 | 2026-06-17 · CLI explore/node + MCP |
| 摘要文件 | research/gitnexus-audit-summary.md |
| Execute DATA_ROOT | `data/`（只读索引） |
| Audit sandbox | `.audit-sandbox/data` |

## 2. 维度验证汇总（7.0 · 待填）

| 维 | 验证命令/检查 | 环境 | 隔离 | 结果 | 证据 |
|----|---------------|------|------|------|------|
| A1 | trellis-check + DECISIONS | local | 无写 | **PASS** | §3.1 |
| A2 | ponytail-review db/core/storage | — | — | **PASS** | §3.2 |
| A3 | SQL/路径注入 rg | local | 无写 | **PASS** | §3.3 |
| A4 | code-review-and-quality：migrate connection write_manager raw_store resource_guard | — | — | **PASS** | §3.4 |
| A5 | AC-1..8 追溯 | local / sandbox | 无写 data/ | **PASS** | §3.5 · 62/62 pytest · A7 只读引用 |
| A6 | N/A | — | — | N/A | §3.6 |
| A7 | init_db ×2 @ .audit-sandbox/data | audit-sandbox | 独立 | **PASS** | §3.7 |
| A8 | pytest -k checksum/own_transaction | audit-sandbox | tmp | **PASS** | §3.8 · 2+15 green |

### Execute §10 证据索引（只读）

| Tier | Execute 证据摘要 |
|------|-------------------|
| A | pytest 93/93；ruff；compileall |
| B | init_db @ data/ 幂等 |
| C | test_foundation_smoke 1 passed |

## 3. 分维度详情

### 3.1 A1 — audit-spec（spec 合规 · 2026-06-17）

**结论：PASS**

#### trellis-check（对照 check.jsonl + DECISIONS.md）

| check.jsonl 条目 | 状态 |
|------------------|------|
| MASTER.plan.md §2 AC-1..8 | 与 implement.jsonl 模块/测试一一对应 |
| DECISIONS.md §1–9 | 实现与决策一致（见下表） |
| write_manager.py / migrate.py | 存在；契约符合 DECISIONS §2/§3/§9 |
| test_write_manager.py / test_schema_migration.py | 存在；`-k own_transaction` / `-k checksum` 用例在位 |

**DECISIONS 对照：**

| 决策 | 实现证据 | 判定 |
|------|----------|------|
| §1 `backend/app/*` 路径 | db/core/storage 均在 `backend/app/` 下 | ✅ |
| §2 stub ValidationGate + staging→clean + audit | `WriteManager.gate = gate or StubValidationGate()`；`_execute_write` 调 `gate.assert_can_write` | ✅ |
| §2 write_mode 仅 append_only / upsert_by_pk | `SUPPORTED_MODES = ("append_only", "upsert_by_pk")` | ✅ |
| §3 五表 foundation + migration 机制 | `001_foundation.sql` 含 schema_version/file_registry/write_audit_log/resource_guard_log/stg_foundation_smoke | ✅ |
| §5 duckdb + psutil；无 polars/pandas | `pyproject.toml` 含 duckdb、psutil；`backend/app/` 无 polars/pandas import | ✅ |
| §9 stub-pass-/stub-fail- 前缀规则 | `validation_gate.py:StubValidationGate.assert_can_write` | ✅ |

#### GitNexus（mandatory）

**`npx gitnexus query "WriteManager ValidationGate migrate chain"`** — 命中 `migrate.py`、`MigrationChecksumError`、`test_schema_migration.py`、`DECISIONS.md`、`test_write_manager.py`。

**`npx gitnexus context WriteManager`** — incoming imports：`test_write_manager.py`、`test_raw_store.py`、`test_foundation_smoke.py`、`file_registry.py`（均在 implement.jsonl）。outgoing methods：`write` → `_execute_write` → `_write_audit`；`__init__` 默认 `StubValidationGate`。

#### CodeGraph（mandatory）

**`npx -y @colbymchenry/codegraph explore WriteManager`** — 65 symbols；链 `write → _execute_write → gate.assert_can_write → staging→clean → _write_audit`；blast radius 含 file_registry + 三测试文件。

**`npx -y @colbymchenry/codegraph node apply_migrations`** — Called by ← `init_db.main` + 13 测试 caller；Calls → `verify_applied_checksums`、`applied_versions`、`_file_checksum`。

**完整链（双工具一致）：**

```text
init_db.main → ConnectionManager.writer → apply_migrations
WriteManager.write → StubValidationGate.assert_can_write → _execute_write → _write_audit
RawStore/FileRegistry → WriteManager.write(own_transaction=False)
```

#### Ghost 依赖

**无。** WriteManager 仅 import `duckdb`、`sql_identifiers`、`validation_gate`；init_db 仅 import `config`、`connection`、`migrate`——均列于 implement.jsonl，无未文档化外部包。

#### Spec 偏离

**无阻塞偏离。** `002_registry_hardening.sql` 为 DECISIONS §3 允许的增量 migration（非整库 schema.sql）。`_execute_write` / `_write_audit` 无直接单测属 A8 测试缺口范畴，非 spec 契约偏离。

（A2–A8 待其他 agent 填写 §3.2–§3.8）

### 3.2 A2 · 过度工程

**范围：** Round 1 产出 — `backend/app/db/`、`core/resource_guard.py`、`storage/`（含 migrate / connection / write_manager / validation_gate / raw_store / file_registry）。

**工具：** GitNexus `query`（WriteManager / migrate / raw_store）；`context(WriteManager)`（4 importers · 9 methods）；CodeGraph `explore "WriteManager validation gate migrate"`（45 symbols · write→gate→audit 链）。

**ponytail-review：**

```
write_manager.py:L49-53: yagni: _validate_request re-quotes identifiers already validated in _validated_tables (L55-59, called L180). Drop _validate_request and L260 call.
raw_store.py:L10-11: yagni: _EXT_MAP maps json→json, csv→csv, parquet→parquet. frozenset({"json","csv","parquet"}) + ext=file_type.
```

**net:** -9 lines possible.

**结论：** 整体 Lean；StubValidationGate、ConnectionManager 文件锁、ResourceGuard 阈值链均为 DECISIONS/AC 要求，非 speculative 层。上两项为可选 shrink，不入 §4.3（非必删 bloat）。

### 3.3 A3 安全（audit-security · 2026-06-17）

**验证类型：** static · AUDIT.plan §2 A3

| 检查项 | 命令/方法 | 结果 |
|--------|-----------|------|
| 密钥扫描 | `rg -i "password\|secret\|api_key" backend/app/` | **0 match** |
| 硬编码密钥 | `rg` sk-/AKIA/ghp_/PRIVATE KEY 全库 | **0 match** |

**SQL 注入面：**

| 组件 | 动态 SQL 用法 | 缓解 | 测试 |
|------|---------------|------|------|
| `quote_ident` | 标识符 allowlist `^[a-z][a-z0-9_]{0,62}$` + 双引号转义 | `ValueError` 拒绝对注入 payload | `test_quoteIdent_injectionAttempt_raises` 等 5 项 |
| `WriteManager` | f-string 拼表/列名 | 全部经 `_validate_request` / `_validated_tables` → `quote_ident`；`write_mode` 枚举校验；audit INSERT 参数化 | `test_write_manager.py` |
| `apply_migrations` | `con.execute(sql_text)` 整文件 | SQL 仅来自 repo 内 `migrations/*.sql`；`verify_applied_checksums` 防篡改；`schema_version` INSERT 参数化 | `test_applyMigrations_modifiedFile_raisesChecksumError` 等 |
| `FileRegistry` | `DELETE FROM stg_file_registry` | 表名为模块常量；VALUES 参数化 | `test_raw_store.py` register 系列 |
| `ConnectionManager` | `SET temp_directory = '{path}'` | `temp_path` 来自 `DATA_ROOT/cache/duckdb_tmp`（非用户输入）；`_escape_sql_string` 转义单引号 | 间接 via connection tests |

**路径注入面（RawStore）：**

| 控制 | 实现 |
|------|------|
| 路径段 | `_safe_segment`：`^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$` |
| 文件名 | `{sha256}.{ext}`，`ext` 来自 `_EXT_MAP` 白名单 |
| 逃逸检测 | `dest_path.resolve()` + `is_relative_to(data_root)` |
| 大小限制 | `MAX_RAW_FILE_BYTES` 256 MiB |

**GitNexus：**

- `query("SQL injection migrate apply_migrations security")` → `proc_2_write`（Write→quote_ident）、`proc_5_main`（init_db→apply_migrations→checksum）。
- `context(quote_ident)` → callers：`_validate_request`、`_validated_tables`、5 个 injection 单测；process `Write → Quote_ident`。
- `context(apply_migrations)` → 13 test callers + `init_db.main`；outgoing：`verify_applied_checksums`、`_file_checksum`。
- `context(RawStore)` → importers：`file_registry`、`test_raw_store`、`test_foundation_smoke`。

**CodeGraph：**

- `node quote_ident` → callers 含 WriteManager + injection 单测。
- `node apply_migrations` → init_db + 13 tests；calls checksum/verify 链。
- `node RawStore` → `test_save_pathTraversal_raises` 等路径安全测试在 caller 链中。

**残余风险（P2 信息项，非阻塞）：**

- `apply_migrations(migrations_dir=...)` 参数可注入自定义目录——仅测试/fixture 使用，生产路径固定 `MIGRATIONS_DIR`。
- Round 1 无外部 HTTP 写入口；WriteManager/RawStore 均为进程内 API，威胁模型为本地可信调用方。

**结论：** 无 P0/P1。标识符 allowlist、迁移 checksum、RawStore 路径校验均已落地并有单测覆盖。

### 3.4 A4 · 代码质量

**范围：** `backend/app/db/migrate.py` · `connection.py` · `write_manager.py` · `backend/app/storage/raw_store.py` · `backend/app/core/resource_guard.py`

**工具：**

| 工具 | 查询 | 结论 |
|------|------|------|
| GitNexus | `query "WriteManager migrate connection raw_store resource_guard"` | 命中 migrate · WriteManager · resource_guard test 链 |
| GitNexus | `context WriteManager` | 4 个 consumer：`file_registry` · `test_write_manager` · `test_raw_store` · `test_foundation_smoke` |
| CodeGraph | `explore "WriteManager apply_migrations connection"` | 87 symbols / 15 files；`init_db → writer → apply_migrations` · `WriteManager.write → gate → audit` 链一致 |
| CodeGraph | `node apply_migrations` | 13 test callers + `init_db` main |

**五轴评审：**

| 轴 | 模块 | 结果 | 证据 |
|----|------|------|------|
| 正确性 | migrate | PASS | 逐文件事务 + ROLLBACK；checksum 校验防篡改；幂等（`applied_versions` skip）；`test_schema_migration` 覆盖 fresh/idempotent/checksum/missing/bad-sql |
| 正确性 | connection | PASS | 文件锁 + stale-PID 回收 + corrupt-lock 拒绝；writer/reader 分离；pragma 按 profile 设 memory/threads/temp；`test_duckdb_connection` 10 项 |
| 正确性 | write_manager | PASS | staging→ValidationGate→clean→audit 完整路径；`quote_ident` 防注入；`own_transaction=False` 嵌套事务不 rollback 外层；upsert `rows_inserted`/`rows_updated` 语义经 4 个 upsert 测试验证 |
| 正确性 | raw_store | PASS | segment 正则 + `is_relative_to` 防路径逃逸；256MB 上限；`test_raw_store` 覆盖 layout/hash/oversized/traversal |
| 正确性 | resource_guard | PASS | `evaluate()` 纯函数 + 最严重信号胜出；`load_thresholds()` 合并 contract；WARN/PAUSE/HARD_STOP 写 guard log |
| 可读性 | 全部 | PASS | 模块边界清晰（db/core/storage）；dataclass 请求/结果；私有方法按职责拆分 |
| 架构 | 全部 | PASS | 依赖方向正确：storage→db，core 读 config；WriteManager 可注入 gate；无循环依赖 |
| 安全 | migrate + write_manager | PASS | migration INSERT 参数化；动态 SQL 仅经 `quote_ident` 后的标识符；`test_write_invalidIdentifier_raisesBeforeWrite` 验证注入拒绝 |
| 安全 | connection | PASS | `_escape_sql_string` 用于 temp_directory pragma 路径 |
| 安全 | raw_store | PASS | `_safe_segment` 拒绝 `..` 等非法段 |
| 性能 | 全部 | N/A | foundation 无 perf SLA（A6 SKIP）；ResourceGuard 仅阈值读数 |

**可选建议（非阻塞）：**

- **Consider:** `WriteManager.__init__(conn_manager, gate=None)` 与 `_write_audit(con, ...)` 缺少类型注解；不影响运行，后续可加 `TYPE_CHECKING` 导入。
- **FYI:** CodeGraph 标注 `_execute_write` / `_write_audit` 无直接单测，经 `write()` 集成路径覆盖（`test_write_manager` 13 项 + smoke）；可接受。

**阻塞项：** 无

**结论：** **PASS**

### 3.5 A5 · 完成情况

**方法：** MASTER §2 AC ↔ §8/§9/§10；Execute §10 证据只读索引。**抽检：** `pytest` Round 1 AC 套件 62/62 exit 0（2026-06-17 A5）。**§10 B init_db：** 未写 `data/`；引用 7.pre A7 @ `.audit-sandbox/data`（首次 applied `[001_foundation, 002_registry_hardening]`，第二次 `none (up to date)`）。

**GitNexus：** `query "WriteManager staging clean write audit"` → migrate/init_db 链 + test_schema_migration / test_write_manager / test_foundation_smoke；`context WriteManager` → imports test_write_manager, test_raw_store, test_foundation_smoke, file_registry。

**CodeGraph：** `node apply_migrations` → init_db main + 13 test callers（含 checksum/idempotent）；WriteManager 链见 §3.1 explore。

| AC# | 预期结果 | §8 实现 | §9 测试层 | §10 Execute | 分数 | 备注 |
|-----|----------|---------|-----------|-------------|------|------|
| AC-1 | 5 foundation 表 + schema_version | 005 migrate | 单元 · test_schema_migration（7） | Tier A 93/93 | **5** | FOUNDATION_TABLES ⊂ SHOW TABLES |
| AC-2 | migration 幂等 + checksum | 005 migrate.py | 单元 · idempotent + checksum 用例 | Tier B init_db×2 幂等 | **5** | A7 sandbox 已验；CG apply_migrations callers |
| AC-3 | ResourceGuard 判定/落库 | 006 resource_guard | 单元 · test_resource_guard（16） | Tier A | **5** | ok/warn/hard + guard_log |
| AC-4 | ConnectionManager 锁 + reader CM | 007 connection | 单元 · test_duckdb_connection（10） | Tier A | **5** | writer lock / reader context |
| AC-5 | WriteManager + audit | 008 write_manager | 单元 · test_write_manager（15） | Tier A | **5** | GN WriteManager 四向 import；staging→audit |
| AC-6 | RawStore hardening | 009 raw_store | 单元 · test_raw_store（13） | Tier A | **5** | exists/hash/registry 路径 |
| AC-7 | foundation smoke E2E | 010 smoke | smoke · test_foundation_smoke（1） | Tier C 1 passed | **5** | CG caller test_foundation_endToEnd |
| AC-8 | stub ValidationGate 契约 | DECISIONS §9 | 单元 · test_write_manager stub-pass/fail/real | Tier A | **5** | 与 DECISIONS §9 三规则一致 |

**A5 结论：** AC-1..8 均可追溯；最低分 **5** ≥ 4 → **PASS**（未触发条件 cli-sandbox 抽检 — Execute §10 B 与 7.pre A7 一致）。

### 3.6 A6 · 性能

**SKIP** — foundation 无 perf SLA（ResourceGuard 仅阈值读数）（AUDIT.plan §2 A6）。

### 3.7 A7 · 运维

**环境：** `QMD_DATA_ROOT=.audit-sandbox/data` · 沙箱 DB 先清空后双跑 · **未写 `data/`**

| 步骤 | 命令 | 退出码 | 输出摘要 |
|------|------|--------|----------|
| init_db #1 | `QMD_DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` | 0 | `init_db: applied ['001_foundation', '002_registry_hardening']` |
| init_db #2 | 同上 | 0 | `init_db: applied none (up to date)` |

**GitNexus（init_db → migrate 链）：**

- `context(init_db.main)` → outgoing: `ConnectionManager.writer` → `apply_migrations`
- `context(apply_migrations)` → incoming 含 `init_db.main`；outgoing: `verify_applied_checksums` → `applied_versions` → `_file_checksum`；process `proc_5_main` / `proc_10_main`

**CodeGraph：** 本 session MCP 未索引；7.pre CLI `node apply_migrations` → 13 test callers + `init_db.main`；`explore WriteManager` 与 migrate 链一致（见 `research/gitnexus-audit-summary.md`）。

**幂等判定：** 第二次 `applied` 为空（`none (up to date)`），符合 §2 预期。**PASS**

### 3.8 A8 · 测试缺口

**AUDIT.plan 字面命令（失败 · exit 5 · 0 collected）：**

```text
pytest tests/test_schema_migration.py -k checksum tests/test_write_manager.py -k own_transaction \
  --basetemp=.audit-sandbox/pytest
```

原因：双 `-k` 互相覆盖；且 `-k own_transaction` 不匹配 `test_write_ownTransactionFalse_…`（camelCase）。

**实际执行（按 fallback · 2026-06-17 · A8 子 agent）：**

```text
pytest tests/test_schema_migration.py -k checksum -q --basetemp=.audit-sandbox/pytest   # 2 passed
pytest tests/test_write_manager.py -q --basetemp=.audit-sandbox/pytest                  # 15 passed（-k own_transaction 空 → 全套件）
```

| 补测/Red Flag | 结果 | 证据 |
|---------------|------|------|
| checksum 迁移完整性 | **PASS** | 2 passed：`modifiedFile` · `missingAppliedFile` · `MigrationChecksumError` |
| WriteManager 全路径 | **PASS** | 15 passed · 含 `ownTransactionFalse` 外 txn 不回滚 outer BEGIN |
| Red Flag `:memory:` 代 prod | **未违规** | `:memory:` 仅 `test_schema_migration` Tier-A 单测（5 处）；checksum 用 `tmp_path`+文件 DuckDB；WriteManager 用 `tmp_path/t.duckdb` |
| Red Flag stub 弱断言 | **未触发** | `StubValidationGate` 为设计内 stub；断言覆盖 status/rows/audit/rollback |
| Red Flag tautological 唯一断言 | **未触发** | 无 assertNotNull-only / assert True |
| GitNexus query | **命中** | `apply_migrations`→`_file_checksum` · `WriteManager.write`→`_execute_write` 链；test_schema_migration / test_write_manager 在 definitions |
| CodeGraph | **缺口标注** | `_execute_write` / `_write_audit` ⚠️ 无直接单测；经 `write()` 集成覆盖（GitNexus incoming: test_write_manager · test_raw_store · smoke） |

**观察（非阻塞 · 不入 §4.3）：**

- `_execute_write` 私有方法无独立单测 — 符合 GLOBAL_TESTING_POLICY §3「不应断言 private 调用」；行为已由 15 个 `write()` 集成测覆盖。
- AUDIT.plan `-k own_transaction` 与测试命名不一致 — 建议 A9/REPAIR 改 `-k ownTransaction` 或重命名测试函数。

**结论：** 补测全绿；Red Flags 未触发 prod-path 违规 → 不入 §4.3。

## 4. 风险与结论（A9 · 主会话 · 2026-06-17）

### 4.1 跨维汇总

- A1–A5、A7–A8：**PASS**；A6：**SKIP**
- §4.3：**无**（A8 观察项：AUDIT `-k own_transaction` 与测试名 `ownTransaction` 不一致 — 文档修正，非代码缺陷）
- stub ValidationGate / Round 2 替换：DECISIONS 已知范围，非 Audit 阻塞

### 4.2 结论

- [x] **PASS**
- [ ] **PASS_WITH_FIXES**
- [ ] **FAIL**

### 4.3 修复项

（无）

## 5. Repair 复验

**N/A** — PASS 无 §4.3。
