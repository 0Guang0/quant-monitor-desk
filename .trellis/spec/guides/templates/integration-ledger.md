# Integration Ledger — {{slug}} (Plan 4→5c)

> **读者：Plan + Execute** · **目的：** 上下文打包地图——能 inline 的已在 MASTER；其余 pointer 须写清 **读什么、提取什么、用于哪条 AC/§8**。

## 打包策略

| 策略 | 含义 |
|------|------|
| **inline** | 已写入 MASTER；Execute 以 MASTER 为准，不必再读原稿 |
| **summary+pointer** | MASTER 有摘要冻结；原稿 pointer 供对照细节 |
| **pointer** | 仅 pointer；**必须**有 extract + for |

## ledger 表（每行一条来源）

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
|--------|----------|----------|---------------|-----------------|-------------|
| `docs/.../DECISIONS.md` | decision | summary+pointer | MASTER §3.2 | GPT-P2-2 tombstone vs generation 列 | AC-10 / §8.8 |
| `specs/contracts/sync_job_contract.yaml` | contract | summary+pointer | MASTER §6.2 | status 枚举 + terminal 集合 | AC-1 / §8.2 |
| `backend/app/db/migrations/004_....sql` | rule | pointer | MASTER §6.7 | 禁止 ALTER fetch_log | AC-7 / §8.1 |

**category：** `decision` | `rule` | `architecture` | `business` | `contract` | `wiring` | `test` | `gate`

## implement.jsonl 生成规则（5c）

- 仅 `strategy` 为 `summary+pointer` 或 `pointer` 的行 → 写入 implement（若文件存在）
- `reason` 格式：`extract: <一句> | for: <AC-x / §8.y>`

## inline 清单（可选速查）

- MASTER §3.2：…
- MASTER §4.4：ResourceGuard → FAILED_RETRYABLE
- MASTER §6.6：data_quality job_type 语义
