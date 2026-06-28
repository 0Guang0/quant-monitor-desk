# B3V-REG 垂直切片 SSOT

> **Manifest:** `B3V-C05` · **活卡:** `B02_05_migration_registry_and_manifest_consistency.md`  
> **Wave 0 索引:** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §1  
> **粒度裁决:** §0.2（2026-06-28）— **整卡 1 GitHub issue**；票内 checklist 非独立 issue  
> **DEBT.plan 镜像:** `.trellis/tasks/round3v-registry-manifest-consistency/DEBT.plan.md`

---

## GitHub issue（整卡 1 票）

| Issue ID | 标题 | 范围 |
| -------- | ---- | ---- |
| **REG-ISSUE-1** | `[B3V-REG] migration 009 + manifest/doc 树对齐 + checker` | `VR-REG-001` + `VR-DOC-001` 全卡 |

---

## 票内垂直切片

| 序 | Slice ID | VR-* | 竖条 | 交付物 | 依赖 | 证据路径 |
| -- | -------- | ---- | ---- | ------ | ---- | -------- |
| 0 | **REG-BOOT** | `VR-REG-001` | 基线矩阵 | migration 009 ↔ `schema.sql` ↔ registry 现状断言 | — | `research/migration-009-coverage-matrix.md`（BOOT 节） |
| 1 | **REG-01** | `VR-REG-001` | Coverage matrix | 更新 `MIGRATION_COVERAGE.md` + `MIGRATION_008_PLAN.md` | BOOT | `execute-evidence/REG-01-matrix.txt` |
| 2 | **REG-02** | `VR-REG-001` | Registry reconcile | proposed delta；UNRESOLVED/RESOLVED 无矛盾 | REG-01 | `execute-evidence/REG-02-proposed-registry-delta.md` |
| 3 | **DOC-ALL** | `VR-DOC-001` | 文档树 + checker（原 DOC-01..03 合并） | restore/replace 决策 + README/MANIFEST/allowlist 一致 + `check_manifest_files.py` + pytest | REG-02 可并行起步 | `execute-evidence/DOC-01-restore.txt`、`DOC-02-doc-sync.txt`、`DOC-03-red.txt`、`DOC-03-green.txt` |

### DOC-ALL 票内 checklist（非独立 issue）

| 子步 | 原 B02 切片 | AC 摘要 |
| ---- | ----------- | ------- |
| 1 | `B02-DOC-01` | `FINAL_AUDIT_REPORT.md` restore（`416e74bc`）或 coordinator 批准 replace |
| 2 | `B02-DOC-02` | README / MANIFEST / `final_package_rules` / allowlist 与文件树一致 |
| 3 | `B02-DOC-03` | `tests/test_manifest_files_check.py` TDD 绿；`check_manifest_files.py` exit 0 |

---

## Execute 顺序

```text
REG-BOOT → REG-01 → REG-02 → DOC-ALL（REG-02 后可并行起步）→ uv run pytest -q
```

---

## 禁止水平关账

- 不得在单切片内同时闭合 `VR-REG-001` 与 `VR-DOC-001` 而无分步证据。
- registry 三件套：**仅 proposed delta**；主会话 §7.3 批闭合。
