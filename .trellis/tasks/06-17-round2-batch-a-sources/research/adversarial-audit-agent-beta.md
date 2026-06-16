# Adversarial Audit — Round 2 Batch A (Agent Beta)

> **视角：** 安全、数据完整性、下游批次耦合（与 Agent Alpha 互补）  
> **工件：** `MASTER.plan.md` v1.2 · 2026-06-17  
> **方法：** doubt-driven-development · GitNexus MCP · CodeGraph CLI · 源码交叉核对  
> **Cross-model：** 跳过（非交互子 agent 上下文；按 skill 要求已声明）

---

## 1. Verdict

### **BLOCK**

计划 v1.2 在 TDD 步骤与接口草图上已可执行，但 **验收 Tier C / Audit A7 使用了错误的环境变量名**，**003 与 `test_schema_contract` 对齐缺失**，**FetchLogWriter 写路径绕过 ConnectionManager 单写锁**，且 **§6 未定义 §8.6 承诺的 `DomainRoleBinding`**。上述任一项可在 Execute 阶段产生「全绿但无效」或 Batch B/C/D 集成债务。在修订 §0.1、§6、§8.0、§8.1、§10 并补充 P0 测试/契约前，**不应进入 Execute**。

---

## 2. Doubt-driven CLAIM / CONTRACT 挑战

### DC-1：003 列类型与 schema 契约一致

| | |
|---|---|
| **CLAIM** | migration 003 的 `source_registry` / `fetch_log` 列与权威 schema 一致，且会被 `test_schema_contract` 模式捕获 drift。 |
| **CONTRACT** | Round 1 `tests/test_schema_contract.py`：`mig_cols ⊆ contract_cols`；DECISIONS §3：`source_registry` 列以 `specs/schema/schema.sql` 为准，`fetch_log` 以 `data_sources.md` §5.6 为准。 |
| **挑战结果** | **CONTRACT 未被 MASTER 引用。** `schema.sql` 含 `source_registry`（L13–33）但 **无 `fetch_log`**；`test_schema_contract.py` 仅覆盖 `FOUNDATION_TABLES`（001/002），§8.1 **未要求**扩展 003。Execute 可造出与 `schema.sql` 或 module doc 不一致的 003 而 Tier A 仍全绿。 |

### DC-2：Adapter 禁止 WriteManager

| | |
|---|---|
| **CLAIM** | `rg "WriteManager" backend/app/datasources/` 无匹配即可证明 Adapter 不写 clean、不绕过写门禁。 |
| **CONTRACT** | GLOBAL_EXECUTION_RULES / `write_manager.md`：clean 表写入必须经 WriteManager + ConnectionManager.writer()；Adapter 仅写 raw/staging 证据 + fetch_log。 |
| **挑战结果** | **静态 rg 不足以证明边界。** FetchLogWriter 计划为 **直接 `INSERT INTO fetch_log`**，不经 WriteManager（audit 表？module doc 未归类）。更致命：§8.0 `migrated_con()` 与 §8.4 测试均 **`duckdb.connect` 裸连**，不经 `ConnectionManager.writer()`，与 Round 1 `FileRegistry` 路径（`file_registry.py:65–96` 同事务 + WriteManager）**并发语义不一致**。GitNexus `impact(reader)` 含 21 个 d=1 调用方，但 Batch A 写 fetch_log **不在图中**——Execute 后仍无法被 GitNexus 检测「绕过 writer 锁」的 import 路径，只能检测字面 import。 |

### DC-3：§8.0 conftest 不破坏 Round 0/1

| | |
|---|---|
| **CLAIM** | §8.0 扩展 `conftest.py` 且「不删 Round 0/1 fixture」，Batch A 与 105 项基线共存。 |
| **CONTRACT** | `tests/conftest.py` 今日仅 `PROJECT_ROOT`（L1–7）；`pyproject.toml` `pythonpath = ["."]`；§8.0 Step 3 `pytest --collect-only` 无 import 错误。 |
| **挑战结果** | **Step 1 在模块存在前 import 未实现符号。** §8.0 Step 1 立即 `from backend.app.datasources.fetch_result import ...` 与 `source_registry`，而 §8.0 表将 `backend/app/datasources/*.py` 与 Step 1 **并列**，Step 3 才 collect-only——顺序矛盾。当前仓库仅 `datasources/__init__.py`（1 行 docstring），**现在运行 Step 3 必 FAIL**。§8.0 未规定最小 stub 文件顺序，Implementer 会卡在 RED 之前。 |

### DC-4（附加）：Tier C 隔离 prod-path

| | |
|---|---|
| **CLAIM** | `$env:DATA_ROOT='data'; pytest -q` 验证 prod-path 下 Batch A 与 Round 1 共存。 |
| **CONTRACT** | `backend/app/config.py:18`：`DATA_ROOT = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")`。 |
| **挑战结果** | **`DATA_ROOT` 环境变量不被读取。** Tier C 命令对路径 **零效果**；与 AUDIT.plan A7 `DATA_ROOT=.audit-sandbox/data` 同样错误（Round 1 audit 已用 `QMD_DATA_ROOT`）。这是验收 theater。 |

---

## 3. GitNexus vs CodeGraph 交叉验证

| 查询 / 命令 | GitNexus | CodeGraph | 对 MASTER 的含义 |
|-------------|----------|-----------|------------------|
| `query("FetchLog source registry adapter fetch log writer")` | **0 条 ingestion 流程**；最高相关为 `init_db.main` → `ConnectionManager.writer`、`WriteManager._write_audit` | `explore "source registry fetch adapter"` → **109 symbols，主要为 Trellis `CLIAdapter`、`.trellis/scripts`**，无 `FetchLogWriter` / `SourceRegistry` | Batch A 代码 **尚不存在**；两工具均 **无法** 预验证将新增的 adapter 流程；Execute 6.pre 必须 re-index |
| `impact(reader, connection.py)` | 默认 **0** upstream；`includeTests:true` → **21 d=1**，全为 Round 1 测试 + `FileRegistry._lookup` | `callers reader` → **20 callers**，全在 `tests/test_*` | 计划让 fetch_log **不走 reader/writer**；与现有读路径 **无 GitNexus 边** → 并发回归盲区 |
| `impact(FileRegistry)` | **0** upstream（不含 tests） | explore 命中 `backend/app/storage/file_registry.py` | Batch B raw→registry 耦合 **未在 Batch A 计划中预连**；`fetch_log.raw_file_paths` 与 `file_registry.local_path` **无 FK/一致性测试** |
| `context(apply_migrations)` | **15 d=1 callers**：`test_schema_migration`×6、`init_db.main`、smoke/raw_store/resource_guard/write_manager 等 | `affected backend/app/db/migrations/` → **No test files affected**（003 未建） | 003 将影响 **47 symbols HIGH**（含 `init_db` 7 processes）；§8.1 Step 5 改 `test_appliedVersions_afterMigration_containsFoundation` **硬编码 003 名**——漏改即 HIGH 回归 |
| `gitnexus://.../processes` | 18 条流程，**无 ingestion** | — | Execute 后需 `analyze` 才能 impact 新符号 |

**结论：** 两工具 **一致确认** ingestion 层为空白；GitNexus 对 **写锁绕过** 与 CodeGraph 对 **migration 测试覆盖** 给出互补告警。计划依赖的「Execute 时再 query」**不能** 替代 Plan 阶段 P0 契约缺口。

---

## 4. Findings（P0–P3）

### P0-1 — Tier C / Audit 使用错误环境变量 `DATA_ROOT`

**证据：** `MASTER.plan.md` §10 Tier C L606、L640：`$env:DATA_ROOT='data'`；`AUDIT.plan.md` A7 L46：`DATA_ROOT=.audit-sandbox/data`。实际配置：`backend/app/config.py:18` 仅读 **`QMD_DATA_ROOT`**。Round 1 audit 正确用法见 `06-17-round1-foundation-audit/research/gitnexus-audit-summary.md`（`QMD_DATA_ROOT=.audit-sandbox/data`）。

**影响：** Execute 勾选 Tier C 可能 **未验证任何 prod-path 行为**；Audit A7 可能 **污染真实 `data/`** 或未隔离。

**需改：** §0.1、§10 Tier C、DECISIONS §7 L89、AUDIT.plan A7 → 统一 `QMD_DATA_ROOT`。

---

### P0-2 — `test_schema_contract` 未扩展至 003；`fetch_log` 双权威无测试桥

**证据：** `tests/test_schema_contract.py` L12–19 `FOUNDATION_TABLES` 无 `source_registry`/`fetch_log`；`specs/schema/schema.sql` 仅含 `source_registry`（L13–33），**无 `fetch_log`**；DECISIONS §3 L52–55 分裂权威；MASTER §8.1 只改 `test_schema_migration.py`，**未提** contract 测试。

**影响：** 003 列类型 drift（如 `allowed_domain` JSON 存 TEXT vs VARCHAR、TIMESTAMP 精度）**不会在 CI 捕获**；Batch B sync 解析 `json.loads(row[2])`（§8.2 L462）可能静默失败。

**需改：** §8.1 增 Step：扩展 `test_schema_contract.py`（`source_registry` ⊆ `schema.sql`；`fetch_log` ⊆ `data_sources.md` §5.6 或先将 §5.6 同步进 `schema.sql`）。

---

### P0-3 — FetchLogWriter / sync_to_db 绕过 ConnectionManager 单写锁

**证据：** `connection.py:157–168` writer 带文件锁；`init_db.py:14–15` 生产路径用 `cm.writer()`；MASTER §8.0 `migrated_con` L322–326、`§8.4` FetchLogWriter 测试 **裸 `duckdb.connect`**；§6.4/§6.5 未要求 writer 上下文。`write_manager.md` 声明「只有 WriteManager 持有 rw 连接」——fetch_log 直接 INSERT **扩大 rw 连接面**。

**影响：** Batch D 并发 fetch + WriteManager clean 写入可能出现 **DuckDB 锁冲突/半提交 fetch_log**；ResourceGuard 在 writer 路径上的假设被削弱。

**需改：** §6.4–§6.5 明确：生产 `fetch()` / `sync_to_db()` 的 `con` **必须**来自 `ConnectionManager.writer()`；测试增 **至少 1 项** writer 锁下写 fetch_log 集成测（或文档化 fetch_log 为「审计表例外」并写入 DECISIONS）。

---

### P0-4 — §8.0 bootstrap 顺序矛盾：conftest import 早于模块创建

**证据：** MASTER §8.0 Step 1 L291–293 import `FetchRequest`/`SourceRegistry`；同节表 L280 创建 `datasources/*.py` 与 Step 1 **无先后**；仓库现状 `backend/app/datasources/__init__.py` 仅 1 行；Step 3 L368 `pytest --collect-only`。

**影响：** 严格按 §8.0 顺序 **Step 3 在 Step 1 后立即失败**；与「TDD 先 conftest」冲突。

**需改：** §8.0 拆为 Step 0a 空 stub / Step 0b conftest / Step 0c fixtures；或 Step 1 禁止 import 直至 §8.2/8.3 首文件存在。

---

### P1-1 — `DomainRoleBinding` 在 §8.6 承诺给 Batch D，§6 未定义

**证据：** MASTER §8.6 L619：`Batch D | job_id 参数、DomainRoleBinding`；§6.1–§6.3 **无** `DomainRoleBinding` dataclass/API；`source_registry.yaml` L110–127 为嵌套 YAML，非导出类型。

**影响：** Batch D Orchestrator 将对 **未冻结类型** 做集成；role 解析逻辑仅在 `SourceRegistry` 内部，**无稳定 getter 契约**（如 `get_domain_roles()` 返回形状未在 §6 列字段）。

**需改：** §6.2 增加 `DomainRoleBinding`（primary_source_id, validation_source_id, fallback_policy）及 `get_domain_roles(domain) -> DomainRoleBinding`；§8.2 增 round-trip 测试。

---

### P1-2 — FetchResult 契约不完整；`NOT_PUBLISHED_YET` 文档/plan 分裂

**证据：** MASTER §6.3 L187–189：`FetchResult` 仅 `...`；§8.3 `CONTRACT_STATUSES` 7 态与 `data_adapter_contract.md` L23 一致；`data_sources.md` L387 另列 **`NOT_PUBLISHED_YET`**（第 8 态）。§6.4 `error_type` 映射引用 `_ERROR_TYPE_MAP` **未在 §6 或 §8 给出完整表**。

**影响：** Batch C Validator 依赖 status/error_type 枚举；Adapter 实现者 **自行补全** 导致 silent 不兼容。

**需改：** §6.3 展开 FetchResult 全字段（对齐 contract md）；§6.4 贴 `_ERROR_TYPE_MAP`；明确 NOT_PUBLISHED_YET 属 Batch B+ 或纳入 8 态。

---

### P1-3 — `staging_table` / `raw_file_paths` 仅 Pydantic 字符串，无 DB/文件系统完整性

**证据：** §3.2 豁免真实 raw 文件；§8.4 FakeAdapter L568 `staging_table="stg_test"`、`raw_file_paths=["/tmp/x"]`；**无**断言 staging 表存在于 DuckDB；Batch C §8.6 依赖 `staging_table` 字段。

**影响：** SUCCESS 路径可携带 **指向不存在对象的证据**，ValidationGate（Batch C）将在 **假阳性 SUCCESS** 上浪费周期。

**需改：** §8.4 增负向测：SUCCESS 且 `staging_table` 非空时，**至少文档化** Batch B 前不校验；或 Batch A 测 `staging_table is None` 的 EMPTY 路径与 SUCCESS 路径字段 **互斥规则**。

---

### P1-4 — `sync_to_db` UPSERT 语义未指定；DELETE+INSERT 数据完整性风险

**证据：** §6.2 L161–162：「DELETE+INSERT 或 DuckDB INSERT OR REPLACE」**二选一未冻结**；§8.2 幂等测只验行数，**不验** `updated_at` 单调、并发两次 sync 中间态。

**影响：** DELETE+INSERT 窗口内 Batch D 读 `source_registry` 可能 **空窗**；与 DECISIONS §4 Primary 必须 enabled **竞态**。

**需改：** §6.2 冻结一种 UPSERT；§8.2 测 `updated_at` 变化（§6.1 注释 L141 已承诺）。

---

### P2-1 — WriteManager 守门仅 `rg backend/app/datasources/`

**证据：** MASTER §8.5 L597；AUDIT A3 L42 同口径。GitNexus 无法沿 **动态 import** 检测；若有人 `from backend.app.db.write_manager import WriteManager` 放在 `datasources/_internal.py` 子包，rg 路径可能漏。

**影响：** 低概率人为绕过；Audit 维度 A3 **过度信任** 单一路径 rg。

**需改：** §8.5 / AUDIT A3 改为 `rg -i "WriteManager|write_manager" backend/app/datasources/` + import-linter 或 CI grep `INSERT INTO` clean 表名（若存在清单）。

---

### P2-2 — DECISIONS §8 与 MASTER §8.5 测试计数冲突

**证据：** DECISIONS §8 L98：`93 + Batch A`；MASTER §8.5 L609：「不硬编码 93」（P2-9）；git status 显示 Round 0/1 已 **105/105**（§0.1 L20）。

**影响：** Checkpoint 文档 **三处基数不一致**；Execute 完成判定模糊。

**需改：** DECISIONS §8 →「全绿 pytest -q，不硬编码计数」；引用 §0.1 commit 基线。

---

### P2-3 — §8.1 迁移测试重复且分散

**证据：** §8.1 Step 1 在 `test_source_registry.py` 写 `includesIngestionTables`；Step 5 **强制**在 `test_schema_migration.py` 写同名语义测试；`test_schema_migration.py` L52–55 当前断言仅至 `002_registry_hardening`。

**影响：** 重复维护；Implementer 可能只改一处 → **部分 GREEN**。

**需改：** §8.1 明确 **canonical 位置**（建议仅 `test_schema_migration.py` + contract 测试），删除重复 Step 1 或改为 import 共享 helper。

---

### P3-1 — ResourceGuard / DATA_ROOT 与 FakeAdapter 路径无交叉验证

**证据：** `resource_guard.py:250` 用 `DATA_ROOT` 算 disk/project size；FakeAdapter 用 `/tmp/x`、`/data/raw/...`（§8.0 L338）；**无**测试 DATA_ROOT 变更下 fetch_log 仍正确。

**影响：** Batch A 可接受；但 Tier C（若修复 env var）仍 **不覆盖** ResourceGuard + ingestion 共存。

**需改：** 记入 Batch D smoke；§8.5 可选 1 条 monkeypatch `QMD_DATA_ROOT` 的 fetch 测试。

---

### P3-2 — GitNexus index  stale 风险未绑定 003 landing

**证据：** `gitnexus-summary.md` L8–9 已警告模块不存在；Execute 6.pre 要求 refresh 但 **Plan audit 未验证** index 日期。

**影响：** Execute 第一天 impact 结果 **空**，与 Plan audit 结论相同——属已知，但应在 §0.1 加「Plan BLOCK 解除条件含 re-analyze」。

---

## 5. 计划章节需更新（具体 §）

| § | 变更 |
|---|------|
| **§0.1** | 门控：`QMD_DATA_ROOT` 替换所有 `DATA_ROOT` 字面量；Execute vs Audit sandbox 命令示例 |
| **§6.2** | 冻结 UPSERT；导出 `DomainRoleBinding` + `get_domain_roles` |
| **§6.3** | 完整 `FetchResult` 字段列表；NOT_PUBLISHED_YET 去留 |
| **§6.4** | 完整 `_ERROR_TYPE_MAP`；fetch_log 是否 audit 表、是否必须 writer |
| **§8.0** | bootstrap 顺序（stub → conftest → collect-only）；`migrated_con` 是否 `@pytest.fixture` |
| **§8.1** | 扩展 `test_schema_contract.py`；消除与 `test_source_registry` 重复；003 SQL 类型对照表 |
| **§8.4** | writer 锁集成测（或 DECISIONS 例外）；staging 证据完整性规则 |
| **§8.5** | rg 范围；`QMD_DATA_ROOT` Tier C |
| **§10** | Tier C 环境变量修正 |
| **§8.6** | 与 §6 类型对齐后再列 Batch D 依赖 |
| **DECISIONS.md §7–§8** | env var 名 + 测试计数 |
| **AUDIT.plan §2 A7** | `QMD_DATA_ROOT=.audit-sandbox/data` |

---

## 6. 残余风险：Batch A 可接受 vs Execute 前必改

### Execute 前必改（阻塞）

- P0-1 环境变量名（Tier C / Audit **无效验收**）
- P0-2 schema contract 测试缺口（**数据完整性**）
- P0-3 写路径与 ConnectionManager 关系（**并发安全**）
- P0-4 §8.0 bootstrap 顺序（**TDD 无法启动**）

### Batch A 可接受若文档化（非阻塞但需写入 DECISIONS）

- P1-3 staging 表不存在（§3.2 已豁免真实文件——需在 §8.6 显式写「Batch C 前补校验」）
- P3-1 ResourceGuard 与 ingestion 交叉（Batch D smoke）
- GitNexus/CodeGraph 预执行无 ingestion 符号（6.pre re-index 即可）

### 必须在 Batch B 前偿还（不阻塞 Batch A Execute，但阻塞 Batch B）

- P1-1 `DomainRoleBinding` 公共 API
- P1-2 完整 status/error_type 枚举
- P1-3 raw_file_paths 与 `FileRegistry` 对齐（Batch B 写 raw 时）
- `fetch_log` 写入 `schema.sql` 主契约（消除双权威）

---

## 附录：工具调用记录

```
GitNexus query("FetchLog source registry adapter fetch log writer")
GitNexus impact(reader, file_path=backend/app/db/connection.py, includeTests=true)
GitNexus impact(FileRegistry, direction=upstream)
GitNexus context(apply_migrations)
Fetch gitnexus://repo/quant-monitor-desk/processes

CodeGraph: sync | explore "source registry fetch adapter" | callers reader | affected backend/app/db/migrations/
```

**Agent Beta 签名：** 独立 adversarial auditor · security / data integrity / downstream coupling · v1.0 · 2026-06-17

---

## 7. Remediation 状态（v1.3 复核）

> **全表：** `research/adversarial-audit-remediation.md`

| 本报告 ID | v1.3 状态 |
|-----------|------------|
| P0-1 … P0-4 | **已修复**（plan/DECISIONS/AUDIT/schema/CI） |
| P1-1 … P1-4 | **已修复**（plan §6–§8）；实现 → **Execute** |
| P2-1 … P2-3 | **已修复** |
| P3-1 | **延后 Batch D**（**未在 Batch A 实现** · 已标注） |
| P3-2 | **已修复**（§0.1 再索引门控）；Execute 后执行命令 |

**Plan BLOCK：** **已解除**
