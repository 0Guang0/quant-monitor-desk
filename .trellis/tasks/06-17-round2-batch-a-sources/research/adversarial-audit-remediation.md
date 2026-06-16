# 对抗审计 Remediation 全表（Alpha + Beta）

> **复核日期：** 2026-06-17  
> **计划版本：** MASTER v1.3  
> **原始报告：** `adversarial-audit-agent-alpha.md`（F-01…F-14）· `adversarial-audit-agent-beta.md`（P0-1…P3-2）  
> **原则：** 两 agent **全部**发现项逐项复核；plan/文档/CI/schema 能修的已修；**代码实现**属 Execute §8；**明确不能在本轮完成的**在「状态」列标注，禁止静默遗漏。

---

## 状态图例

| 状态 | 含义 |
|------|------|
| **已修复** | v1.3 已在 plan/文档/CI/schema 落地，Execute 可直接照做 |
| **Execute 待实现** | plan 已写清；**须 Execute §8 写代码/测试**后才算完成 |
| **延后 Batch B+** | Batch A 范围外；已在 plan §8.6 / DECISIONS 标注偿还批次 |
| **已知限制** | 接受风险；已文档化，非 Batch A 阻塞 |

---

## P0（阻塞项 · 8 条去重为 4 项）

| ID | 来源 | 问题 | 修复动作 | 状态 |
|----|------|------|----------|------|
| **P0-1** | F-01 · Beta P0-1 | Tier C / Audit 使用 `DATA_ROOT` env | MASTER §0.1/§8.5/§10 · DECISIONS §7 · AUDIT A7 → **`QMD_DATA_ROOT`** | **已修复** |
| **P0-2** | F-02 · Beta P0-2 | `test_schema_contract` 未覆盖 003；`fetch_log` 双权威 | `specs/schema/schema.sql` 追加 `fetch_log` · MASTER §8.1 Step 5–6 · DECISIONS §3 | **已修复**（contract **测试代码** → Execute 待实现） |
| **P0-3** | F-04 · Beta P0-3 | FetchLogWriter 绕过 writer 锁 | DECISIONS §5 · MASTER §6.4–§6.5 · §8.4 `test_write_underWriterLock_*` | **已修复**（plan）；**Execute 待实现**（集成测 + 生产路径） |
| **P0-4** | F-03 · Beta P0-4 | §8.0 bootstrap 顺序 | MASTER §8.0 重排 0a→0d；003 移出 §8.0 | **已修复** |

---

## P1

| ID | 来源 | 问题 | 修复动作 | 状态 |
|----|------|------|----------|------|
| **P1-1** | F-08 · Beta P1-1 | `DomainRoleBinding` 未定义 | MASTER §6.2 `DomainRoleBinding` + `get_domain_roles()` · §8.2 测试 | **已修复**（plan）；**Execute 待实现** |
| **P1-2** | F-05 · Beta P1-2 | FetchResult 不完整；NOT_PUBLISHED_YET 分裂 | MASTER §6.3 全字段 · §6.4 完整 `_ERROR_TYPE_MAP` · §8.3 注释排除 8 态 | **已修复** |
| **P1-3** | Beta P1-3 | staging 证据无完整性规则 | MASTER §3.2/§6.3/§8.4 EMPTY vs SUCCESS · §8.6 Batch C 偿还 | **已修复**（Batch A 不校验 DB 内 staging 表 → **延后 Batch C**） |
| **P1-4** | Beta P1-4 | UPSERT 未冻结 | DECISIONS §7.4 · MASTER §6.2 `INSERT OR REPLACE` · §8.2 `updated_at` 测试 | **已修复**（plan）；**Execute 待实现** |
| **P1-5** | §8.4 AC | SUCCESS 证据字段 | MASTER §8.4 `test_fetch_success_carriesEvidenceFields` | **Execute 待实现** |
| **P1-6** | §8.4 | NETWORK_ERROR error_type | MASTER §6.4 映射表 + §8.4 完整断言（非 `...`） | **已修复**（plan）；**Execute 待实现** |
| **P1-7** | §8.2 sync | sync round-trip 列 | 保留 §8.2 `test_syncToDb_roundTrip_*` | **Execute 待实现** |
| **P1-8** | §8.4 | adapter unsupported domain | §8.4 测试 + 0-row log | **Execute 待实现** |
| **P1-9** | §8.5 Tier B | init_db prod-path | §8.5/§10 Tier B 不变；env 文档修正 | **已修复** |
| **P1-10** | §8.4 | silent fallback | §8.4 `test_fetch_implDoesNotSwitchSourceId` | **Execute 待实现** |
| **P1-11** | F-06 | unknown license Primary | fixture `bad_unknown_license_primary.yaml` + §8.2 测试 | **已修复**（plan）；**Execute 待实现**（fixture 文件） |

---

## P2

| ID | 来源 | 问题 | 修复动作 | 状态 |
|----|------|------|----------|------|
| **P2-1** | F-10 · Beta P2-3 | migration 测试重复 | §8.1 canonical：仅 `test_schema_migration` + `test_schema_contract` | **已修复** |
| **P2-2** | F-09 | 门控 commit 仅 d218162 | §0.1 → `d218162..3d7f93a` | **已修复** |
| **P2-3** | §8.1 snippet | Step 5 含 `...` | §8.1 Step 1 完整函数体 | **已修复** |
| **P2-4** | §8.2 | malformed YAML 等 | 测试清单保留 | **Execute 待实现** |
| **P2-5** | §8.5 Tier C | 原 DATA_ROOT | → `QMD_DATA_ROOT` | **已修复** |
| **P2-6** | F-11 · Beta P2-1 | CI 缺 compileall/grep | `.github/workflows/ci.yml` 追加 compileall + grep gate · §10「CI 覆盖」列 | **已修复** |
| **P2-7** | Alpha §4 | closed connection optional | §8.4 **非 optional** | **已修复**（plan） |
| **P2-8** | F-12 · Beta P2-2 | DECISIONS §8 写 93 | DECISIONS §8 → 105 基线 + 不硬编码 | **已修复** |
| **P2-9** | MASTER §8.5 | 硬编码计数 | 保留「不硬编码」+ 基线 105 | **已修复** |

---

## P3

| ID | 来源 | 问题 | 修复动作 | 状态 |
|----|------|------|----------|------|
| **P3-1** | F-13 | 合法 FallbackPolicy 无正向测 | §8.2 parametrized 6 policies | **已修复**（plan）；**Execute 待实现** |
| **P3-2** | F-14 | valid fixture vs repo seed | §6.2 `DEFAULT_YAML` 路径 · §8.0/§8.2 说明 | **已修复** |
| **P3-3** | §8.3 | staging_table round-trip | 保留 `test_fetchResult_stagingTableField_roundTrips` | **Execute 待实现** |
| **P3-4** | §8.2 | defaultYaml seed 测试 | `test_defaultYaml_loadsFromRepoSeed` + DEFAULT_YAML | **Execute 待实现** |
| **P3-5** | §8.5 | rg 仅 WriteManager | → `grep -riE 'WriteManager\|write_manager'` | **已修复** |
| **P3-6** | Beta P3-1 | ResourceGuard + ingestion 交叉 | §8.5 可选注释 · §8.6 Batch D smoke | **延后 Batch D**（**未在 Batch A 实现**） |
| **P3-7** | Beta P3-2 | GitNexus stale after 003 | §0.1 Execute 后再 `analyze` + `codegraph sync` | **已修复**（plan 门控）；**Execute 待执行**（索引刷新命令） |

---

## Alpha §4 / §5 附加 gap（无独立 ID）

| Gap | 修复动作 | 状态 |
|-----|----------|------|
| §8.4 pre-impl 校验仍写 log | §6.5 + §8.4 0-row 测试 | **已修复**（plan）；**Execute 待实现** |
| §8.3 NOT_PUBLISHED_YET | Batch B+ · §8.3 注释 | **已修复** |
| §8.5 Tier C theater | → P0-1 | **已修复** |
| §10 Coverage 未提 | §8.5/§10 `--cov-fail-under=75` | **已修复** |
| detect_changes `main` 不存在 | §0.1 默认分支 `master` | **已修复** |
| `verify_applied_checksums` 无测试 | §8.1 已知限制脚注 | **已知限制** |
| Tier B 与 CI 脱节 | §10「CI 覆盖=否」+ A7 audit-sandbox | **已修复**（文档对齐） |
| F-12 data_sources.md dataclass | `data_sources.md` §5.5 实现口径注记 | **已修复** |

---

## Beta §6「Batch B 前偿还」项

| 项 | Batch A 处理 | 状态 |
|----|--------------|------|
| raw_file_paths ↔ FileRegistry | §8.6 → Batch B | **延后 Batch B** |
| staging 表 DuckDB 存在性 | §8.6 → Batch C | **延后 Batch C** |
| NOT_PUBLISHED_YET 8 态纳入 contract | §6.3 Batch B+ | **延后 Batch B** |

---

## Execute §8 待实现清单（**未修复项 · 必须写代码**）

以下 **plan 已补齐**，但 **仓库尚无实现**；Execute 完成前不得勾选 §10：

| 序号 | 交付物 | MASTER 章节 |
|------|--------|-------------|
| E1 | stub `backend/app/datasources/*.py` | §8.0 0a |
| E2 | fixtures YAML（含 `bad_unknown_license_primary.yaml`） | §8.0 0b |
| E3 | `tests/conftest.py` 扩展 | §8.0 0c |
| E4 | `003_ingestion_sources.sql` | §8.1 Step 3 |
| E5 | `test_schema_migration.py` 003 断言 | §8.1 Step 1–4 |
| E6 | `test_schema_contract.py` 003 扩展 | §8.1 Step 5–6 |
| E7 | `source_registry.py` + 全 §8.2 测试 | §8.2 |
| E8 | `fetch_result.py` + §8.3 测试 | §8.3 |
| E9 | `fetch_log.py` + `base_adapter.py` + §8.4 全测试（含 writer-lock） | §8.4 |
| E10 | §8.5 Tier A/B/C 证据 | §8.5 / §10 |
| E11 | Execute 后 GitNexus + CodeGraph 再索引 | §0.1 |

---

## 复核结论

| 维度 | 结论 |
|------|------|
| **Plan BLOCK** | **已解除**（文档/plan/CI/schema 侧 P0–P3 全部复核并修订） |
| **Execute 可启动** | **是** — 严格 §8.0→8.5 |
| **仍标注未修复** | **E1–E11**（代码）· **P3-6**（Batch D）· **Batch B/C 偿还项** · **`verify_applied_checksums` 已知限制** |

**签核：** 主会话 remediation · 对应 MASTER v1.3 · 2026-06-17
