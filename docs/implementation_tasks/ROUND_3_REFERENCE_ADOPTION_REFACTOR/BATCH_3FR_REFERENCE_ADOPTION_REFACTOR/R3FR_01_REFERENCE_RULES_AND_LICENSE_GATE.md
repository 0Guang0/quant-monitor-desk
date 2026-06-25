# R3FR-01 — Reference Rules and License Gate

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** reference-adoption governance from ad hoc planning to enforceable task-local rules.  
> **Execution posture:** planning/contract only; no runtime fetch; no clean write.

---

## 1. Purpose

Replace the earlier “central reference inventory first” approach with a lower-maintenance rule:

```text
Executable adoption details live in the task card that uses the reference source.
```

This task creates/updates only the global guardrails that every future task card must follow. It must not create `docs/architecture/reference_adoption_inventory.md` as an execution dependency.

---

## 2. Required updates

Update these files:

```text
specs/contracts/reference_adoption_guardrails.yaml
docs/implementation_tasks/README.md
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
```

Required semantics:

- one Task ID = one executable task card;
- executable reference adoption details must be local to the relevant task card;
- a separate reference inventory, if ever created, may only be a non-executable index;
- external code may be adapted only into QMD-owned modules;
- no backend runtime import from `参考项目/**`;
- no OpenBB AGPL runtime source copy;
- no EasyXT/JQ2PTrade action, account-control, auto-login, or broad-scan semantics;
- no module may require more than three implementation batches to reach full stable production form for its declared scope;
- first implementation batch must be a real vertical slice, not a placeholder.

---

## 3. Reference projects and task-local placement

| Reference project                    | Allowed use                                                                                        | Where executable details must be written                        |
| ------------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `参考项目/EasyXT`                    | QMD-owned adaptation of data quality rules, TDX provider lifecycle, selected backtest/report ideas | The task card implementing data health, TDX, or backtest/review |
| `参考项目/JQ2PTrade`                 | QMD-owned read-only loader/report/review shape and forbidden API deny-list                         | The backtest/review or sandbox rehearsal task card              |
| `参考项目/OpenBB`                    | Architecture-only provider/package/catalog pattern                                                 | Provider catalog or datasource task card                        |
| `参考项目/agents-for-openbb`         | Future Agent/UI artifact shape reference only                                                      | Round4 Agent/UI task card                                       |
| TradingAgents / TradingAgents-astock | Future license-reviewed Agent/UI reference only                                                    | Round4 Agent/UI task card after license review                  |

---

## 4. License gate

For every implementation task that adapts reference code, the task card must include:

```yaml
reference_project:
  path: ""
  license: ""
  allowed_use: direct_adaptation | architecture_only | forbidden_until_review
  qmd_target_files: []
  direct_copy_allowed: false
  rewrite_required: []
  forbidden_semantics: []
  attribution_required: true|false
```

Rules:

- MIT/Apache code may be directly adapted only when the card names source path and target QMD path.
- AGPL code is architecture-only unless a separate legal/architecture decision explicitly allows a compatible integration.
- Unknown license is forbidden for runtime adoption.
- Reference docs/examples may inform design, but runtime code must be QMD-owned.

---

## 5. Tests / gates

Required verification:

```bash
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q
```

Expected checks:

- no `backend/app/**` imports from `参考项目/**`;
- forbidden action/account-control names are not introduced into runtime modules;
- OpenBB runtime copy is not introduced;
- `reference_adoption_guardrails.yaml` states task-card-local detail placement;
- Round 3F-R cards do not depend on a central executable reference inventory.

---

## 6. Done criteria

R3FR-01 is done when:

- guardrails no longer require a new central reference inventory for execution;
- R3F-R task cards carry their own source-path adaptation details;
- the root completion rating file exists and is referenced by planning/task files only;
- design/contract/architecture files remain complete-product targets and are not polluted with current-completion labels.
