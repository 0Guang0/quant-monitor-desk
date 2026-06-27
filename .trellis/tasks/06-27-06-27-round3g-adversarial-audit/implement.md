# Implement — R3G-02（simple track）

> SSOT：`R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` + `prd.md`  
> 分支：`feature/round3g-adversarial-audit`（自 `master`）  
> 纪律：TDD、karpathy、testing-guidelines（五字段）、**全部代码（含测试）严格遵守 ponytail**、GitNexus impact、不 commit（主会话收尾）

## 步骤

### 1.0 Boot

- Read `implement.jsonl` 每行 + `prd.md` + 任务卡 §3–7
- `task.py start 06-27-round3g-adversarial-audit`
- GitNexus `impact` on `validate_source_caps` / `write_rehearsal_report` 等将触碰符号

### 1.1 决策类型与契约对齐（RED → GREEN）

- 新增 `backend/app/ops/sandbox_clean_write/audit_decision.py`
  - `AuditDecision` enum（契约三值）
  - `AuditFinding` / `AuditResult`（reasons + evidence_paths）
- 测试：枚举冻结、未知决策不可序列化

### 1.2 对抗审计核心（RED → GREEN）

- 新增 `backend/app/ops/sandbox_clean_write/adversarial_audit.py`
- 输入：`rehearsal_report` path、`sandbox_db` path、`evidence_dir`
- 实现 task card §3.1–3.5 检查（读报告 JSON + 契约 block_if + registry YAML；**不** runtime import `参考项目/**`）
- ponytail：复用 `required_report_fields()`、现有 registry loader；避免重复 R3G-01 runner 逻辑

### 1.3 CLI `audit` 子命令（RED → GREEN）

- 扩展 `backend/app/cli/data_commands.py` + `main.py`
- 形态见任务卡 §5；拒绝生产 DB 写路径（对齐 R3G-01 `canonical_prod` + `config.DATA_ROOT` 模式）
- 写出 `audit_decision.json`

### 1.4 测试矩阵（RED → GREEN）

- 扩展 `tests/test_round3g_pre_production_adversarial_audit.py` 覆盖 task card §7：
  - missing report → BLOCK
  - missing DH profile evidence → BLOCK
  - approximate calendar → WARN 上限
  - uncapped candidate → BLOCK
  - forbidden API names / OpenBB copy / agent path → BLOCK
  - valid bounded fixture → PASS 或 WARN+manual
- 使用 `tests/fixtures/sandbox_clean_write/r3g01/` + 合成坏例 fixture（最小新增）

### 1.5 Handoff

- `uv run pytest tests/test_round3g_pre_production_adversarial_audit.py tests/test_reference_adoption_guardrails.py -q`
- `uv run pytest -q` 全库
- `uv run python scripts/loop_maintain.py`（若触达 backend/specs/tests catalog）
- 产出 `research/execute-evidence/` 简要 green 日志
- **不 commit**

## 禁止

- 生产 mutation；cap 扩大；新 ad-hoc runner 绕过 QMD gates
- `参考项目/**` runtime import
- 修改 `staged_pilot.py` 行为

## 验证命令

```bash
uv run pytest tests/test_round3g_pre_production_adversarial_audit.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest -q
```
