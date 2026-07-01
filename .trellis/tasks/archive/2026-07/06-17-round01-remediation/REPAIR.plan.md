# REPAIR 计划 — Round 0 / Round 1 Remediation

> **Phase 8 · 复杂任务协议** · 输入：`ROUND01_REMEDIATION_BACKLOG.md`（GPT 审计复核）  
> **Execute 者：** Repair agent / 主会话 · **不读** Batch A `MASTER.plan.md`  
> **完成门控：** 本文件 §5 Tier 全绿 → 允许 Round 2 Batch A `task.py start`

---

## 0. 元信息

| 字段          | 值                                                          |
| ------------- | ----------------------------------------------------------- |
| slug          | `06-17-round01-remediation`                                 |
| 前置          | GPT 审计 + `ROUND01_REMEDIATION_BACKLOG.md` 复核            |
| 阻塞          | Round 2 Batch A Execute（用户已同意「先 P0 再 Round 2」时） |
| DATA_ROOT     | `data/`（与 Round 1 一致）                                  |
| Audit sandbox | `.audit-sandbox/data`（仅 Batch D CI 本地试跑）             |

### 0.1 Repair Skill 冻结

| Skill                          | 本任务   | 绑定                                                             |
| ------------------------------ | -------- | ---------------------------------------------------------------- |
| TDD / test-driven-development  | **必做** | §8 每步先红后绿                                                  |
| Karpathy Guidelines            | **必做** | 最小 diff，修根因                                                |
| testing-guidelines             | **必做** | 行为断言                                                         |
| systematic-debugging           | **条件** | P1-3 锁冲突若复现                                                |
| verification-before-completion | **必做** | §5 全命令                                                        |
| GitNexus `impact`              | **必做** | 改 `connection.py` / `write_manager.py` / `resource_guard.py` 前 |

---

## 1. 修复批次（建议 2 PR）

| 批次    | 范围                                        | PR 标题建议                                                 | 阻塞 Round 2             |
| ------- | ------------------------------------------- | ----------------------------------------------------------- | ------------------------ |
| **R-A** | P0-1, P0-2, P0-3, SEC-4                     | `fix: clean checkout tests, reader pragmas, frontend audit` | **是**                   |
| **R-B** | P0-4（部分）, P1-1, P1-2 文档+contract 测试 | `fix: resource guard temp/cache + docs/schema contract`     | **是**                   |
| **R-C** | P1-3, P1-4                                  | `fix: write audit path + file_registry dedupe`              | 建议                     |
| **R-D** | GAP-1..5 CI 门禁                            | `chore: ci pytest ruff npm-audit link-check coverage`       | 建议（Round 2 首 PR 前） |
| **R-E** | P1-5, P2 文档                               | `docs: agent workflow boundaries and doc cleanup`           | 否                       |

---

## 2. §8 TDD 步骤

### §8.0 — P0-1：clean checkout pytest（Batch R-A）

**目标：** 无预先存在的 `data/duckdb` 时 `pytest -q` 通过。

**Step 0 — 红**

```bash
# 确认当前 scaffold 测依赖目录（有目录时绿、无目录时红）
pytest tests/test_project_scaffold.py -k duckdb -q
```

**Step 1 — 改测试逻辑（首选，不修 .gitignore 提交 runtime）**

- 文件：`tests/test_project_scaffold.py`
- 从 `REQUIRED_DIRS` **移除** `data/duckdb`
- **新增** `test_dataLayout_initDbCreatesDuckDbDir`：monkeypatch `DATA_ROOT` 到 `tmp_path`，跑 `scripts/init_db.main()`，断言 `(tmp_path / "duckdb").is_dir()`

**Step 2 — README**

- 文件：`README.md`
- 说明：首次开发跑 `python scripts/init_db.py`（非 pytest 前置）

**Step 3 — 绿**

```bash
pytest -q
```

**GitNexus：** `impact({target: "ConnectionManager", direction: "upstream"})` — 仅当改 connection 时；本步通常不需要。

---

### §8.1 — SEC-4：空 env fallback（Batch R-A）

**Step 0 — 红**

- 新建 `tests/test_config.py`：

```python
def test_dataRoot_emptyEnv_fallsBackToProjectData(monkeypatch):
    monkeypatch.setenv("QMD_DATA_ROOT", "")
    import importlib
    import backend.app.config as cfg
    importlib.reload(cfg)
    assert cfg.DATA_ROOT == cfg.PROJECT_ROOT / "data"
```

**Step 1 — 绿**

- 文件：`backend/app/config.py`

```python
def _path_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return Path(raw)
```

- 替换 `DATA_ROOT` / `CONFIGS_ROOT` 赋值
- `.env.example`：注释 `# 留空则使用默认 <repo>/data`

**Step 2 — 绿**

```bash
pytest tests/test_config.py -q
```

---

### §8.2 — P0-3 + GAP-5：reader pragma（Batch R-A）

**GitNexus（必做）：** `impact({target: "reader", direction: "upstream"})` 或 `context({name: "ConnectionManager"})`

**Step 0 — 红**

- `tests/test_duckdb_connection.py` 新增：

```python
def test_applyPragmas_readerProfile_setsThreadsAndMemory(tmp_path):
    ...
    with cm.reader() as r:
        threads = r.execute("SELECT current_setting('threads')").fetchone()[0]
        mem = r.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    assert int(threads) == 2
    assert "1536" in mem or "1.5" in mem.lower()
```

**Step 1 — 绿**

- `backend/app/db/connection.py`：`reader()` 在 yield 前调用 `self._apply_pragmas(con)`  
  （DuckDB read_only 连接支持 SET memory_limit/threads/temp_directory — 与 writer 同函数即可）

**Step 2 — 绿**

```bash
pytest tests/test_duckdb_connection.py -q
pytest -q
```

---

### §8.3 — P0-2：前端 npm audit（Batch R-A）

**Step 0 — 记录基线**

```bash
cd frontend && npm audit
```

**Step 1 — 选一路径（二选一，PR 描述写清）**

| 路径     | 动作                                                                                |
| -------- | ----------------------------------------------------------------------------------- |
| **升级** | 升 `vite` / `@vitejs/plugin-react` 到 audit 通过版本；`npm ci`                      |
| **例外** | 新建 `docs/ops/security_exception.md`：CVE、原因、计划修复日、仅 dev 服务器威胁模型 |

**Step 2 — 绿**

```bash
cd frontend && npm ci && npm audit && npm run typecheck && npm run build
```

---

### §8.4 — P0-4：ResourceGuard temp/cache（Batch R-B）

**范围（与 DECISIONS 对齐）：**

- **本 Repair 做：** `duckdb_temp_max_gb`（扫描 `DATA_ROOT/cache/duckdb_tmp` 体量）；`cache_warn_gb` / `cache_pause_gb` / `cache_hard_stop_gb`（扫描 `DATA_ROOT/cache`）
- **Deferred（写 DECISIONS 脚注）：** `system_*_pct` → Round 2+ 或 task 032

**Step 0 — 红**

- `tests/test_resource_guard.py`：mock `DATA_ROOT/cache` 目录大小，断言 `evaluate()` 在超 pause 阈值时 `PAUSE`

**Step 1 — 绿**

- `resource_guard.py`：`snapshot()` 或新 helper 读 cache 大小；`evaluate()` 增加 signals
- 更新 `ROUND_1 DECISIONS.md` §7 脚注：已接入 vs 仍 deferred

**Step 2 — 绿**

```bash
pytest tests/test_resource_guard.py -q
```

---

### §8.5 — P1-1 + GAP-3：docs 链接（Batch R-B）

**Step 0 — 红**

- 新建 `scripts/check_doc_links.py`：扫描 `docs/INDEX.md` 与 `docs/**/*.md` 相对链接，exit 1 若目标不存在

**Step 1 — 绿**

- 修复 `docs/INDEX.md` L10、L15 路径

**Step 2 — 绿**

```bash
python scripts/check_doc_links.py
```

---

### §8.6 — P1-2 + GAP-4：schema contract（Batch R-B）

**Step 0 — 红**

- 新建 `tests/test_schema_contract.py`：
  - 解析 `001_foundation.sql` + `002_registry_hardening.sql` 创建的表
  - 对每张 foundation 表，断言 `specs/schema/schema.sql` 中同表 **列名集合** 为 superset（允许 schema.sql 含未来列，但 migration 列必须在 schema.sql 中有定义）
  - 文档化：`migrations` = runtime truth；`schema.sql` = 目标契约

**Step 1 — 绿**

- 若测试失败：修 migration 或 schema.sql 注释/列定义（不整库执行 schema.sql）
- 更新 `DECISIONS.md` §3 一段「contract 测试：`test_schema_contract.py`」

---

### §8.7 — P1-3：WriteManager 失败 audit（Batch R-C，条件）

**仅当** Batch R-A 后仍担心双连接锁：

**Step 0 — 红**

- 扩展 `test_write_ownTransactionFalse_stubFail_doesNotRollbackOuterTxn`：断言失败 audit 行存在且外层 txn 仍 open

**Step 1 — 评估**

- 若 DuckDB 双连接在持锁 writer 下稳定：文档化于 `write_manager.py` docstring，**REJECTED 改代码**
- 若 flaky：失败 audit 改用传入的 `con`（同一连接）INSERT audit，不 `duckdb.connect` 新连接

---

### §8.8 — P1-4：FileRegistry dedupe（Batch R-C）

**Step 0 — 红**

- `test_register_duplicateHash_returnsSameFileId` 已有；新增 migration 或测试文档说明 `content_hash` UNIQUE（若加约束）

**Step 1 — 绿（最小）**

- `file_registry.py`：捕获 DuckDB unique violation → `_lookup_by_content_hash` → return existing  
  （若无 UNIQUE，002 migration 增加 `CREATE UNIQUE INDEX ... ON file_registry(content_hash)` 需 GitNexus impact）

---

### §8.9 — GAP CI 门禁（Batch R-D）

**新建** `.github/workflows/ci.yml`：

```yaml
# 伪代码结构 — Execute 时写完整
jobs:
  backend:
    - pip install -e ".[dev]"
    - pytest -q --cov=backend --cov-fail-under=75
    - ruff check .
  frontend:
    - npm ci
    - npm audit --audit-level=high
    - npm run typecheck && npm run build
  docs:
    - python scripts/check_doc_links.py
```

`pyproject.toml` 增加 `pytest-cov` dev 依赖。

---

## 3. §5 Repair DoD（Tier 验收）

| Tier | 命令                                               | 预期                             |
| ---- | -------------------------------------------------- | -------------------------------- |
| A    | `pytest -q`（**无** `data/duckdb` 目录）           | 全绿                             |
| A    | `ruff check .`                                     | 0 error                          |
| A    | `python -m compileall -q backend scripts tests`    | 0                                |
| B    | `python scripts/init_db.py` ×2                     | 第二次 `up to date`              |
| B    | `cd frontend && npm audit --audit-level=high`      | 0 high **或** exception 文档存在 |
| C    | `pytest tests/test_duckdb_connection.py -k reader` | reader pragma 绿                 |
| C    | `pytest tests/test_schema_contract.py`             | 绿                               |
| D    | `python scripts/check_doc_links.py`                | exit 0                           |
| D    | CI workflow 本地 act/手动等效                      | 绿                               |

**GitNexus（Repair 收尾）：** `detect_changes({scope: "compare", base_ref: "main"})` — 确认仅触及 backlog 文件。

---

## 4. §6 与 Round 2 Batch A 衔接

| 顺序 | 动作                                                                 |
| ---- | -------------------------------------------------------------------- |
| 1    | 合并 **R-A** PR                                                      |
| 2    | 合并 **R-B** PR（或 R-A+R-B 单 PR 若体量小）                         |
| 3    | 用户确认 Round 2 准入 §5 Tier A–C 绿                                 |
| 4    | `python .trellis/scripts/task.py start 06-17-round2-batch-a-sources` |
| 5    | Batch A 6.pre → MASTER §8 Execute                                    |

**禁止：** 在 P0-1 / P0-3 未修复前 Execute Batch A migration 003（否则 clean checkout + reader 路径仍不达标）。

---

## 5. Deferred（需用户书面批准才可跳过）

| 项                             | 理由                           |
| ------------------------------ | ------------------------------ |
| P0-4 `system_*_pct`            | DECISIONS Round 1 已 defer     |
| P0-2 vite 不升级只写 exception | 需用户接受 dev-server CVE 风险 |
| P1-5 移除 `.cursor`            | Trellis 工作流依赖；仅文档化   |
| P2 文档 dedupe                 | 非 Round 2 阻塞                |

---

## 6. 批准

- [ ] 用户确认 Repair 批次顺序（R-A → R-B → Round 2 或合并 PR）
- [ ] 用户确认 P0-2 路径：升级 vite **vs** security exception
- [ ] 用户确认 P0-4 范围：仅 temp/cache **vs** 全量 system\_\*\_pct
