# Batch 3G Coordinator Playbook

## 0. Scope

Coordinate Batch 3G from this folder only. README is the entrypoint; each Task ID has its own executable card.

Batch 3G may start because Round 3F-R is **closed** (roadmap condition A). If 3F-R were incomplete, entry would require ADR defer per open item — that path does not apply after R3FR-07.

## 1. Dispatch tracks

| Track                  | Card                                         | Suggested branch                      | Parallelism                                       |
| ---------------------- | -------------------------------------------- | ------------------------------------- | ------------------------------------------------- |
| Sandbox rehearsal      | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`    | `feature/round3g-sandbox-rehearsal`   | first                                             |
| Adversarial audit      | `R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` | `feature/round3g-adversarial-audit`   | after R3G-01 evidence                             |
| Limited approved entry | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`   | `feature/round3g-limited-clean-write` | after R3G-02 allow decision and explicit approval |

## 2. Required cross-reading

Every branch must read:

- `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F-R and Round 3G;
- `BATCH_3G_TASK_CARD_MANIFEST.md`;
- `BATCH_3G_HARDENING_RULES.md`;
- the relevant `R3G_*` card;
- `specs/contracts/reference_adoption_guardrails.yaml`;
- `specs/contracts/sandbox_clean_write_contract.yaml` if present, or create/update it as part of R3G-01.

Reference-source details must be read from the relevant `R3G_*` card, not from a separate inventory file.

## 3. Merge order

1. Merge R3G-01 implementation and evidence/report tests.
2. Merge R3G-02 audit implementation and decision tests.
3. Merge R3G-03 limited entry only after explicit approval fixture and rollback proof tests exist.

## 4. File locks

Avoid parallel edits to:

- `backend/app/ops/sandbox_clean_write/**`
- `backend/app/cli/data_commands.py`
- `specs/contracts/sandbox_clean_write_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`

## 5. Review checklist

Every Batch 3G PR must prove:

- it did not create a separate reference inventory file for execution details;
- it kept reference adoption details in the task card or PR notes;
- it did not import from `参考项目/**` at runtime;
- it did not copy OpenBB runtime code;
- it did not expose JQ2PTrade disallowed API names;
- it did not add Agent-triggered write paths;
- it preserved source/domain/symbol/window caps;
- it preserved QMD gates: DataSourceService, SourceRoutePlanner, ResourceGuard, DbValidationGate, WriteManager, data-health profiles.
