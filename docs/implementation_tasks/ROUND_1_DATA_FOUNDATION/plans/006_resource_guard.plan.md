# 006 ResourceGuard — 深度实现计划

> **给执行者：** 配合 `006_implement_resource_guard.md`，按 TDD 执行。
> 遵守 `/karpathy-guidelines` 与 `/testing-guidelines`。

**目标：** 读取 `resource_limits.yaml`，用 `psutil` 采集系统读数，按当前 profile 给出 `OK / WARN / PAUSE / HARD_STOP` 决策，并在非 OK 时写 `resource_guard_log`。

**架构：** 纯函数 `evaluate(snapshot, thresholds) -> Decision` 做判定（可用真实值测试）；`ResourceGuard.check()` 负责采集（psutil）+ 判定 + 落库。采集与判定分离，便于测试。

**范围（DECISIONS.md §5）：** 允许 `psutil`。Round 1 只做读数与判定 + 落库，不做自动 kill 进程。

---

## 文件结构

- 创建：`backend/app/core/__init__.py`（如缺）
- 创建：`backend/app/core/resource_guard.py`
- 测试：`tests/test_resource_guard.py`
- 依赖：`pyproject.toml` 增加 `psutil>=6.0.0`

---

## API 签名

```python
# backend/app/core/resource_guard.py
from dataclasses import dataclass
from enum import Enum

class Decision(str, Enum):
    OK = "OK"
    WARN = "WARN"
    PAUSE = "PAUSE"
    HARD_STOP = "HARD_STOP"

@dataclass(frozen=True)
class ResourceSnapshot:
    available_memory_gb: float
    disk_free_gb: float
    process_rss_mb: float
    project_size_gb: float

def evaluate(snapshot: ResourceSnapshot, thresholds: dict) -> tuple[Decision, str]:
    """纯函数：返回 (决策, 触发原因)。HARD_STOP 优先级 > PAUSE > WARN > OK。"""

class ResourceGuard:
    def __init__(self, profile: str | None = None, con=None): ...
    def snapshot(self) -> ResourceSnapshot:
        """用 psutil 采集当前读数。"""
    def check(self) -> tuple[Decision, str]:
        """采集 + evaluate；非 OK 时写 resource_guard_log（若 con 提供）。"""
```

判定口径取自 `resource_limits.yaml` 的 `system_thresholds` 与 `project_size_thresholds`：

| 信号 | WARN | PAUSE | HARD_STOP |
|------|------|-------|-----------|
| available_memory_gb | < 4 | < 2 | < 1 |
| disk_free_gb | < 30 | < 20 | < 10 |
| project_size_gb | > 15 | > 25 | > 40 |

任一信号命中更严重档位即采用该档（取最严重）。

---

## 任务步骤（TDD）

### Step 1: 写失败测试

```python
from backend.app.core.resource_guard import Decision, ResourceSnapshot, evaluate

THRESH = {
    "system_thresholds": {
        "available_memory_warn_gb": 4, "available_memory_pause_gb": 2,
        "available_memory_hard_stop_gb": 1, "disk_free_warn_gb": 30,
        "disk_free_pause_gb": 20, "disk_free_hard_stop_gb": 10,
    },
    "project_size_thresholds": {
        "project_warn_gb": 15, "project_pause_gb": 25, "project_hard_stop_gb": 40,
    },
}

def test_evaluate_healthyResources_returnsOk():
    snap = ResourceSnapshot(available_memory_gb=8, disk_free_gb=100,
                            process_rss_mb=300, project_size_gb=1)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK

def test_evaluate_lowMemory_returnsPause():
    snap = ResourceSnapshot(available_memory_gb=1.5, disk_free_gb=100,
                            process_rss_mb=300, project_size_gb=1)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert "memory" in reason.lower()

def test_evaluate_criticalDisk_returnsHardStop():
    snap = ResourceSnapshot(available_memory_gb=8, disk_free_gb=5,
                            process_rss_mb=300, project_size_gb=1)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP

def test_evaluate_multipleSignals_picksMostSevere():
    # 内存仅 WARN，磁盘 HARD_STOP → 取 HARD_STOP
    snap = ResourceSnapshot(available_memory_gb=3.5, disk_free_gb=5,
                            process_rss_mb=300, project_size_gb=1)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP
```

### Step 2: 运行确认失败

Run: `pytest tests/test_resource_guard.py -v`
Expected: FAIL（模块不存在）

### Step 3: 实现 `evaluate` 纯函数 + 数据类

先只实现 `evaluate`、`Decision`、`ResourceSnapshot`，让上面 4 个测试通过。

### Step 4: 运行确认通过

Run: `pytest tests/test_resource_guard.py -v`
Expected: PASS（4 passed）

### Step 5: 实现 `ResourceGuard.snapshot()/check()`

- `snapshot()`：`psutil.virtual_memory().available`、`psutil.disk_usage(...).free`、`psutil.Process().memory_info().rss`、`data/` 目录大小。
- `check()`：采集 → evaluate → 非 OK 写 `resource_guard_log`（con 为 None 时跳过落库）。

补一条 mock psutil 的测试（只 mock I/O）：

```python
def test_check_lowMemorySnapshot_writesGuardLog(monkeypatch, tmp_path):
    import duckdb
    from backend.app.db.migrate import apply_migrations
    from backend.app.core.resource_guard import ResourceGuard, Decision
    con = duckdb.connect(":memory:"); apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    monkeypatch.setattr(guard, "snapshot", lambda: ResourceSnapshot(1.5, 100, 300, 1))
    decision, _ = guard.check()
    assert decision == Decision.PAUSE
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 1
```

### Step 6: 验收 + 提交

Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Commit: `feat(core): add ResourceGuard with eco/normal/batch thresholds (task 006)`

---

## 自检

- [ ] 判定逻辑用真实值测试（未 mock evaluate）
- [ ] 仅 psutil I/O 被 mock
- [ ] HARD_STOP/PAUSE/WARN 优先级正确
- [ ] 非 OK 落 `resource_guard_log`

---

## 实现记录（含审计修复与缺口补充）

> 首版实现后的 hardening 轮次在本 task 范围内的变更记录。

### 首版交付（task 006）

- `backend/app/core/resource_guard.py`：`Decision`、`ResourceSnapshot`、`evaluate()`、`ResourceGuard`
- `tests/test_resource_guard.py`：5 个测试（OK / PAUSE / HARD_STOP / 多信号 / check 落库）

### 审计修复与实现缺口

| 项 | 问题 | 修复 |
|----|------|------|
| 缺口 | `process_rss_mb` 采集但未参与判定 | `evaluate(..., profile_limits=)` 增加 RSS 信号；`check()` 传入当前 profile 阈值 |
| 缺口 | `_dir_size_gb` 跟随 symlink 可能误判或慢 | `rglob(..., follow_symlinks=False)` |
| 测试 | `Decision.WARN` 未覆盖 | 新增 WARN / project_size / RSS 边界测试 |
| 测试 | OK 路径是否误写 guard log 未验证 | 新增 `test_check_okDecision_doesNotWriteGuardLog`（mock 健康 snapshot） |

### 测试缺口补充

| 测试 | 证明什么 |
|------|----------|
| `test_evaluate_warnMemory_returnsWarn` | 内存 3.5GB → `WARN` |
| `test_evaluate_largeProject_returnsPause` | 项目目录 30GB → `PAUSE` |
| `test_evaluate_highRss_returnsPause` | RSS 超 warn 阈值 → `WARN` |
| `test_check_okDecision_doesNotWriteGuardLog` | OK 时不写 `resource_guard_log` |

### 当前测试规模

- 本 task 相关：`tests/test_resource_guard.py` **9** 个（原 5 + 4）

---

## 评估报告跟进（二次修复）

| 评估项 | 修复 |
|--------|------|
| guard_log 靠 autocommit 巧合 | `check()` 非 OK 落库改为显式 `BEGIN` → `INSERT` → `COMMIT` |

---

## 评估报告跟进（三次修复）

| 评估项 | 修复 |
|--------|------|
| **P1** 缺 `RESOURCE_GUARD_PAUSED` 输出 | `format_pause_event()` + PAUSE/HARD_STOP 时 `print(..., file=sys.stderr)` |
| **P0** guard_log INSERT 失败事务悬挂 | `check()` 落库包裹 try/except + ROLLBACK |
| 测试命名 `test_evaluate_highRss_returnsPause` 误导 | 重命名为 `test_evaluate_rssAboveWarnNotPause_returnsWarn` |
| HARD_STOP / 边界值 / sentinel 无测试 | 新增 4 个测试 |

### Round 1 范围说明（非 bug）

- contract 中 `system_memory_usage_*pct`、`cache_*gb` 阈值 Round 1 未接入 `evaluate()`，留 Round 2+ 按需实现。

### 当前测试规模（三次修复后）

- 本 task：**13** 个
