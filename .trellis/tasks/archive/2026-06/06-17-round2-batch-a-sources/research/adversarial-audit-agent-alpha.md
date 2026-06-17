# Adversarial Audit — Round 2 Batch A (Agent Alpha)

> **视角：** 计划完整性 / 正确性 vs **当前** codebase（post Round 0/1 remediation，HEAD `3d7f93a`）  
> **工件：** `MASTER.plan.md` v1.2 · 2026-06-17  
> **方法：** gitnexus-exploring · gitnexus-impact-analysis · doubt-driven-development · GitNexus MCP · CodeGraph CLI · 源码只读核对  
> **Cross-model：** 跳过（非交互子 agent；按 doubt-driven skill 已声明）

---

## 1. Executive Verdict

### **BLOCK**

MASTER v1.2 在接口草图与测试清单上接近可执行，但对抗当前 codebase 后，至少 **4 项 P0** 会在 Execute 阶段产生「Tier 全勾但验收无效」或「TDD 无法启动」：

1. **§10 Tier C 使用不存在的环境变量 `DATA_ROOT`**（实际为 `QMD_DATA_ROOT`，见 `backend/app/config.py:18`）。
2. **`test_schema_contract.py` 未规划扩展至 003**，而 `fetch_log` 不在 `specs/schema/schema.sql`，双权威无测试桥。
3. **§8.0 bootstrap 顺序矛盾**——conftest 立即 import 尚不存在的 `backend.app.datasources.*`。
4. **FetchLogWriter / `sync_to_db` 写路径与 ConnectionManager 单写锁关系未冻结**，测试全部裸 `duckdb.connect`。

此外，门控 commit 仍写 `d218162`，遗漏 **`3d7f93a` 对 schema contract 测试的扩展**；§6 `error_type` 映射与下游 orchestrator 文档 **枚举口径冲突**。在 §0.1、§6、§8.0–§8.1、§10 完成最小 patch 前，**不应 Execute §8.0**。

---

## 2. Tool Evidence Summary

### 2.1 GitNexus MCP（server: `user-gitnexus`）

| 调用 | 关键结果 |
|------|----------|
| `query({query: "schema migration apply_migrations ingestion datasource"})` | 命中 `apply_migrations` → `init_db.main` → `ConnectionManager._apply_pragmas`；**无 ingestion / SourceRegistry / FetchLogWriter 流程**（与 gitnexus-summary 一致） |
| `impact({target: "apply_migrations", direction: "upstream", includeTests: true})` | **HIGH**：47 符号；d=1 含 `test_schema_migration`×6、`init_db.main`、smoke/raw_store/resource_guard/write_manager 等；`init_db.main` 关联 7 条 process |
| `impact({target: "ConnectionManager", direction: "upstream", includeTests: true})` | **MEDIUM**：6 符号；d=1 为 `init_db`、connection/raw_store/write_manager/smoke 测试 import |
| `context({name: "WriteManager"})` | 入向 import：`file_registry.py`、write/raw/smoke 测试；**无 datasources 路径**；出向为 write/audit 方法链 |
| `detect_changes({scope: "compare", base_ref: "main"})` | **失败**：仓库无 `main` 分支 |
| `detect_changes({scope: "compare", base_ref: "master"})` | 低危：仅 `AGENTS.md` + Round 2 README 文档节变更；**无代码 symbol 影响** |

**解读：** Batch A 将 HIGH 冲击 `apply_migrations` 上游；计划改 `test_appliedVersions_afterMigration_containsFoundation` 为硬编码三元组时，漏改即全库回归。WriteManager 边界当前靠「模块不存在」维持，Execute 后 GitNexus 仍无法沿边检测「裸 INSERT fetch_log」——仅 import 字面量。

### 2.2 CodeGraph CLI（项目根，`npx -y @colbymchenry/codegraph`）

| 命令 | 输出摘要 |
|------|----------|
| `status` | Index OK：111 files，920 nodes，2,315 edges |
| `explore migration schema datasource` | 46 symbols / 12 files；`apply_migrations` **21 callers**；`verify_applied_checksums` **无覆盖测试** |
| `impact apply_migrations` | **51 affected symbols**（与 GitNexus 47 同阶，测试文件列表高度重叠） |
| `node WriteManager` | 9 methods；**无 datasources 依赖** |

**GitNexus vs CodeGraph 交叉：** 两者对 `apply_migrations` blast radius **一致（HIGH/MEDIUM+）**；均 **0 nodes** 于 `SourceRegistry` / `FetchLogWriter`（代码未建）。CodeGraph 额外标注 `verify_applied_checksums` 无测试——003 landing 后 checksum 回归仍靠现有 6 条 migration 测试，**不覆盖新 migration 内容校验**。

### 2.3 当前 codebase 快照（审计时只读）

| 项 | 现状 |
|----|------|
| HEAD | `3d7f93a` — docs: 扩展 `test_schema_contract` 至 6 张 foundation 表；README 明确 pytest 不依赖 init_db |
| 门控 commit（§0.1） | 仍写 `d218162`（Round 0/1 remediation）；**未含** `3d7f93a` |
| pytest 收集 | **105** tests（`pytest --collect-only -q`） |
| migrations | 仅 `001_foundation.sql`、`002_registry_hardening.sql` |
| `backend/app/datasources/` | 仅 `__init__.py` docstring |
| `specs/datasource_registry/source_registry.yaml` | **已存在**（5 sources，4 domain_roles） |
| `specs/schema/schema.sql` | 含 `source_registry`（L13–33）；**无 `fetch_log` 表** |
| `tests/conftest.py` | 仅 `PROJECT_ROOT`（7 行） |
| `tests/test_schema_contract.py` | 6 foundation 表 vs 001/002 migrations |
| CI (`.github/workflows/ci.yml`) | `pytest -q --cov-fail-under=75` + `ruff`；**无** compileall / rg / init_db |

---

## 3. Findings Table

| ID | Sev | Category | Claim in plan | Reality in codebase | Recommended plan change |
|----|-----|----------|---------------|---------------------|-------------------------|
| **F-01** | P0 | Env / §10 | Tier C：`$env:DATA_ROOT='data'; pytest -q`（§10 L606,L640） | `DATA_ROOT` 由 `QMD_DATA_ROOT` 驱动（`config.py:18`）；设 `DATA_ROOT` **零效果** | §0.1 Execute DATA_ROOT 行改为 **`QMD_DATA_ROOT`**；§10 Tier C 同步；DECISIONS §7 L89、AUDIT A7 一并改 |
| **F-02** | P0 | Schema contract | 003 列与 schema 一致；§8.1 Step 5 更新 migration 测试即可 | `test_schema_contract.py` 仅 001/002；`fetch_log` **不在** `schema.sql`；003 drift **CI 不捕获** | §8.1 增 Step：`source_registry` ⊆ `schema.sql`；`fetch_log` ⊆ `data_sources.md` §5.6（或先补进 `schema.sql`） |
| **F-03** | P0 | TDD / §8.0 | §8.0 先于 8.1；Step 3 `collect-only` 无 import 错误 | Step 1 import `FetchRequest`/`SourceRegistry` **模块不存在**；Step 3 **必 FAIL** | 拆 §8.0：0a 最小 stub → 0b fixtures → 0c conftest → 0d collect-only；**禁止** Step 0 表内预建 `003_*.sql` |
| **F-04** | P0 | Concurrency | Adapter 禁止 WriteManager；§3.3 不修改 WriteManager | `init_db` 用 `ConnectionManager.writer()`；§8.0/§8.4 全用 **裸** `duckdb.connect`；fetch_log 直接 INSERT **扩大 rw 面** | §6.4–§6.5 冻结：生产 `con` 必须来自 `writer()`；或 DECISIONS 写明 fetch_log 审计表例外 + 1 条 writer 锁集成测 |
| **F-05** | P1 | §6 contract | `_ERROR_TYPE_MAP`：`NETWORK_ERROR→network`（§6.4 L210） | `data_sync_orchestrator.md` §13.8 用 **`NETWORK_TIMEOUT`/`RATE_LIMITED` 等大写**；module doc **无** lowercase `network` 表 | §6.4 贴 **完整映射表** 并引用唯一权威（建议对齐 orchestrator §13.8 + FetchResult.status） |
| **F-06** | P1 | §6 / §8.2 | `InvalidRegistryError`：Primary 绑定 disabled 或 `license_type=unknown`（§6.1 L144） | 测试清单有 `bad_unknown_primary`（**不存在 source_id**）、`disabled_registry`（assert_enabled）；**无** primary→unknown license fixture | §8.0 增 `bad_unknown_license_primary.yaml`；§8.2 增 `test_load_primaryUnknownLicense_raises` |
| **F-07** | P1 | §6.5 / AC-6 | 每次 fetch 写 fetch_log；`request_params_hash` 来自 `FetchRequest.model_dump_json()`（§6.4） | §6.5 `write(con, result, ...)` **未传 req**；hash 列计划默认 NULL 与 AC 审计意图冲突 | §6.5 签名增 `req: FetchRequest \| None`；§8.4 断言 hash 非空（SUCCESS 路径） |
| **F-08** | P1 | §8.6 / §6 | Batch D 依赖 `DomainRoleBinding`（§8.6 L619） | §6 **未定义** 类型；§8.2 仅 `get_domain_roles(...).primary_source_id` 散点断言 | §6.2 增加 frozen `DomainRoleBinding` + 字段列表；§8.2 round-trip 测试 |
| **F-09** | P2 | Gate / §0.1 | Round 0/1 已通过 @ `d218162`，105/105 | HEAD **`3d7f93a`** 改 `test_schema_contract` + README；门控 **未追踪** 该 commit | §0.1 门控改为 `3d7f93a`（或 `d218162..3d7f93a` 范围）并注：contract 测试已 6 表，Batch A 需 **再加 003** |
| **F-10** | P2 | §8.1 TDD | Step 1 `test_source_registry` + Step 5 **强制** `test_schema_migration` 同名语义 | 两处 `includesIngestionTables` → **重复维护**；Step 5 snippet 含 `...` **不完整** | Canonical：**仅** `test_schema_migration.py`；删 §8.1 Step 1 或改为 schema 文件 import helper |
| **F-11** | P2 | §10 / CI | Tier A：pytest + ruff + compileall + rg WriteManager | CI 仅 pytest+cov+ruff（`ci.yml` L17–18）；**compileall/rg 非 CI gate** | §10 增列「CI 覆盖」：Tier A 本地项 vs CI 子集；或 PR 前 trellis-check 补 compileall |
| **F-12** | P2 | Docs drift | Pydantic v2 权威（§6.3）；DECISIONS §8「93 + 增量」 | `data_sources.md` §5.5 仍为 **dataclass** 示例；DECISIONS §8 仍写 **93**；collect **105** | §6.3 加「勿抄 module doc §5.5」；DECISIONS §8 改为「pytest -q 全绿，不硬编码计数」（MASTER §8.5 已有 P2-9，DECISIONS 未同步） |
| **F-13** | P3 | FallbackPolicy | `bad_invalid_fallback.yaml` 测非法 policy | `source_registry.yaml` / module doc §5.3 列 **6 种合法 policy**；**无** 合法 policy 正向测 | §8.2 增 parametrized 合法 `fallback_policy` load 成功 |
| **F-14** | P3 | Fixture scope | valid fixture「2 源 + 1 domain_roles 即可」（§8.0 L366） | repo seed **5 源 4 domain**；`test_defaultYaml_loadsFromRepoSeed` 读全量 seed | §8.0 明确 `DEFAULT_YAML` 路径 = `specs/datasource_registry/source_registry.yaml`；valid fixture 与 seed 关系写清 |

**Finding 计数：** 14（≥8 要求满足）。

---

## 4. §8 TDD Gaps（逐步）

| Step | Plan 声称 | Gap（对抗证据） |
|------|-----------|-----------------|
| **§8.0 Step 1** | 追加 conftest import | **RED 前无模块**：`datasources/*.py` 与 import 并列，无 stub 顺序 → collect 失败（F-03） |
| **§8.0 Step 2** | YAML fixtures | `bad_unknown_primary` 不覆盖 **unknown license** Primary（F-06）；Shadow/Emergency 覆盖 OK |
| **§8.0 Step 3** | `collect-only` | 当前仓库 **105** 项可 collect；按 Step 1 改完 **不可** collect |
| **§8.0 表** | 创建 `003_ingestion_sources.sql` | **违反 TDD**：migration 文件出现在 §8.1 RED **之前**（F-03） |
| **§8.1 Step 1–4** | RED→GREEN migration | 无 `test_schema_contract` 扩展 → GREEN 后仍可能 **列类型 drift**（F-02） |
| **§8.1 Step 5** | 改 `test_schema_migration.py` | 与 Step 1 重复（F-10）；snippet `...` 不完整 |
| **§8.2 sync 测试** | `json.loads(row[2])` on `allowed_domain` | 无 contract 测试保证 003 列名/类型与 `schema.sql` 一致 |
| **§8.3** | 7 status parametrized | 缺 `NOT_PUBLISHED_YET`（module doc L387 第 8 态）去留未决（F-05 关联） |
| **§8.4 FetchLogWriter** | `error_type == "network"` | 与 orchestrator 大写 enum **不一致**（F-05）；closed connection 测 optional 可能跳过 P0 传播 |
| **§8.4 BaseDataAdapter** | 恰好 1 条 log | 未测 **registry 校验失败时是否 0 条 log**（disabled/domain 在 impl 前 raise → 应明确 AC） |
| **§8.4** | FakeAdapter SUCCESS 证据 | 无 staging 表存在性校验（Batch B 前可文档化，但 §8.6 已依赖 staging_table） |
| **§8.5** | `rg WriteManager` | 不防 `write_manager` 小写路径变体；非 CI（F-11） |
| **§8.5 Tier C** | DATA_ROOT | **无效命令**（F-01） |

---

## 5. §10 CI / Tier Misalignment

| Tier | Plan 命令 | CI / 实际 | 差距 |
|------|-----------|-----------|------|
| **A (ci)** | Batch A 单测 + `pytest -q` + ruff + compileall + rg | CI：`pytest -q --cov-fail-under=75` + `ruff` | **compileall、rg WriteManager 不在 CI**；新增模块 coverage 缺口无单独 gate |
| **B (prod-path)** | `init_db` ×2 + SHOW TABLES | CI **不跑** init_db | 仅 Execute/Audit 手工；README 已说明 pytest 不依赖 init_db（`3d7f93a`）— Tier B 仍必要但 **与 CI 脱节** |
| **C (prod-path)** | `$env:DATA_ROOT='data'; pytest -q` | 应用读 **`QMD_DATA_ROOT`** | Tier C **验收 theater**（F-01） |
| **分支** | detect_changes `main` | 默认分支 **`master`**；CI on push `main, master` | Plan/Audit 应用 `master` 或 document 双分支 |
| **Coverage** | §8.5 未提 | CI **75% floor** | Batch A 大量新模块；无「新文件 coverage」计划 |

---

## 6. Minimum Plan Patch List（Execute §8.0 前，有序）

1. **§0.1** — 门控 commit → `3d7f93a`（或 range）；`Execute DATA_ROOT` / Audit sandbox → **`QMD_DATA_ROOT`** 示例路径。
2. **§8.0** — 重排 bootstrap：**stub modules → fixtures → conftest → collect-only**；从 §8.0 表 **移除** `003_ingestion_sources.sql`（挪入 §8.1 Step 3）。
3. **§8.1** — 新增 Step：扩展 `tests/test_schema_contract.py`（`source_registry` + `fetch_log`）；**删除** Step 1 重复 migration 测试或指定 canonical 文件；补全 Step 5 完整函数体（无 `...`）。
4. **§6.2** — 冻结 UPSERT 策略；导出 `DomainRoleBinding` + `get_domain_roles()`.
5. **§6.3** — 展开 `FetchResult` 全字段；声明 NOT_PUBLISHED_YET 范围。
6. **§6.4** — 完整 `_ERROR_TYPE_MAP`；明确 fetch_log 写路径与 ConnectionManager 关系（F-04）。
7. **§6.5** — `FetchLogWriter.write(..., req=...)` 传参；生产 `con` 来自 `writer()` 的契约句。
8. **§8.2** — 增 unknown-license fixture + 合法 FallbackPolicy 正向测。
9. **§8.4** — hash 断言；可选 writer-lock 集成测；明确 pre-impl 校验失败 **不写** fetch_log。
10. **§10** — Tier C → `$env:QMD_DATA_ROOT='data'; pytest -q`；Tier A 标注 CI 子集 vs 本地全量。
11. **DECISIONS.md §7–§8** — env var 名 + 测试计数与 §0.1 对齐。

---

## 7. Doubt-Driven 抽样（§6–§8 核心 CLAIM）

| CLAIM | CONTRACT | 对抗结论 |
|-------|----------|----------|
| 「003 两表 + migration 回归足够」 | DECISIONS §3 + Round 1 contract 测试模式 | **FAIL**：`fetch_log` 双权威且无 contract 测试（F-02） |
| 「§8.0 共享基础设施先于 8.1」 | TDD + 当前 105 collect | **FAIL**：import 顺序导致 Step 3 不可达（F-03） |
| 「Tier C 验证 prod-path」 | `config.py` env 名 | **FAIL**：变量名错误（F-01） |
| 「Adapter 禁止 WriteManager」 | rg datasources | **PARTIAL**：静态 rg 不足；写锁语义未测（F-04） |

---

## 8. 附录：Mandatory Tool Transcript

```
# GitNexus
query("schema migration apply_migrations ingestion datasource")
impact(apply_migrations, upstream, includeTests=true)  → HIGH, 47
impact(ConnectionManager, upstream, includeTests=true) → MEDIUM, 6
context(WriteManager) → imports: file_registry, tests; no datasources
detect_changes(compare, main) → FAIL (no main branch)
detect_changes(compare, master) → 9 doc sections, risk low

# CodeGraph
status → 920 nodes, index OK
explore migration schema datasource → apply_migrations 21 callers; verify_applied_checksums no tests
impact apply_migrations → 51 symbols
node WriteManager → 9 methods, backend/app/db/write_manager.py:42

# Codebase
pytest --collect-only -q → 105 tests
git log -1 → 3d7f93a (schema contract + README)
migrations → 001, 002 only
grep fetch_log specs/schema/schema.sql → no matches
```

**Agent Alpha 签名：** 独立 adversarial auditor · plan completeness vs codebase · v1.0 · 2026-06-17

---

## 9. Remediation 状态（v1.3 复核）

> **全表：** `research/adversarial-audit-remediation.md`

| 本报告 ID | v1.3 状态 |
|-----------|------------|
| F-01 … F-14 | plan/文档/CI/schema **已修复**；测试/模块实现 → **Execute E1–E11** |
| §4 TDD gap 各行 | 已写入 MASTER §8；代码 **Execute 待实现** |
| §5 CI gap | CI 已加 compileall + grep；Tier B/C 仍非 CI（**已知 · A7 手工**） |

**Plan BLOCK：** **已解除**（2026-06-17 remediation 主会话）
