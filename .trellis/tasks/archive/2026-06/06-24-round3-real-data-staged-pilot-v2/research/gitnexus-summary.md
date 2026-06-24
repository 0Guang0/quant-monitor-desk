# GitNexus Summary — B-19 staged pilot v2

## 影响面（Plan 1b）

| 符号                                                  | 风险   | 说明                                  |
| ----------------------------------------------------- | ------ | ------------------------------------- |
| `build_production_mutation_proof`                     | HIGH   | AUD-04；SP2-08 必改 proof_status 语义 |
| `run_staged_pilot_raw_only` / `run_full_staged_pilot` | MEDIUM | caps 扩样、evidence v2 文件名         |
| `validate_authorization`                              | MEDIUM | v2 envelope 扩样须 fail-closed        |
| `preview_staged_pilot`                                | LOW    | route matrix v2 字段                  |
| `DataSourceService.fetch`                             | MEDIUM | 真实网络；ResourceGuard cap           |

## 执行流

`staged_pilot` → route preview → authorized fetch → raw_store → staging → validation_gate → conflict inspect → mutation_proof → closeout

## Plan 建议

- 优先复用 v1 路径常量；最小 diff 扩 caps
- MUT-PROOF-001：一处修复 `mutation_proof.py`，closeout 读子字段
- GitNexus `impact()` 在改上述符号前必跑（Execute §8.0）
