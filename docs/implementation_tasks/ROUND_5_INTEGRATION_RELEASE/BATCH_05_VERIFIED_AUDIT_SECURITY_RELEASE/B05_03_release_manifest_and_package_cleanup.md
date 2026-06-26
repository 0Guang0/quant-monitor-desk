# B05_03 — Release Manifest and Package Cleanup

> **Batch:** Batch 05 — Verified Audit Security and Release Gates  
> **Owns:** release runbook/final manifest/package cleanup, loose historical cards `034_implement_docs_consistency_check.md`, `035_implement_final_package_cleanup.md`, `036_create_final_release_manifest.md`  
> **Roadmap:** Round 5.3.  
> **Execution posture:** final release metadata and cleanup only; no product feature implementation.

---

## 1. Business purpose

Create a release manifest and package cleanup path that accurately represents project readiness without deleting historical evidence, overstating production status, or hiding unresolved/deferred items.

This task is the release truth layer. It must block or disclose missing Round3H/Round3G/Round4 capabilities; it must not implement them.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/implementation_tasks/README.md
docs/implementation_tasks/BATCH_FOLDER_REHOME_PLAN.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md
docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md
docs/quality/round3h_real_data_production_entry_audit.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/README.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
specs/verification/contract_coverage.yaml
specs/contracts/sandbox_clean_write_contract.yaml
specs/contracts/reference_adoption_guardrails.yaml
tests/test_catalog.yaml
```

No reference-project source is needed for this card. `参考项目/**` should be listed only as reference material status where relevant, not packaged as QMD runtime source.

---

## 3. Target QMD files

Create/update QMD-owned files only:

```text
docs/release/RELEASE_MANIFEST_TEMPLATE.yaml
docs/release/RELEASE_MANIFEST_<release_id>.yaml
docs/ops/release_verification.md
docs/ops/rollback_runbook.md
docs/ops/bad_source_quarantine.md
scripts/generate_release_manifest.py
scripts/check_docs_consistency.py
scripts/check_release_package.py
tests/test_release_manifest.py
tests/test_docs_consistency.py
tests/test_package_cleanup.py
tests/test_catalog.yaml
```

If final file names differ, the PR must document the mapping.

---

## 4. Required manifest fields

At minimum, manifest must include:

```yaml
release_id: ""
source_branch: ""
commit: ""
production_live_enabled: false
production_clean_write_enabled: false
first_executable_batch_entrypoint: ""
completed_rounds: []
canonical_batch_entrypoints: []
open_deferred_items: []
unresolved_registry_items: []
reference_adoption_status: ""
allowed_sources: []
forbidden_default_sources: []
source_enablement_posture: {}
round3h_admission_decision: ""
source_final_decisions: []
source_limitations: []
route_evidence_status: {}
r3h_audit_artifact: ""
clean_write_posture: {}
security_gate_status: {}
integration_resource_smoke_status: {}
test_commands: []
package_contents: []
excluded_paths: []
known_limitations: []
operator_runbooks: []
```

---

## 5. Implementation plan

1. **Manifest generator/checker**
   - Implement template and optional generator/checker.
   - Generator must read only QMD-owned roadmap/task/spec/test metadata.
   - Do not infer production readiness from docs prose; require explicit gate fields.

2. **Docs consistency check**
   - Check consistency among:
     - `PROJECT_IMPLEMENTATION_ROADMAP.md`;
     - `docs/implementation_tasks/README.md`;
     - canonical batch folders;
     - loose historical cards;
     - `contract_coverage.yaml`;
     - `tests/test_catalog.yaml`.
   - Loose cards must be retained with pointer/redirect status or explicitly audited before deletion.

3. **Package cleanup rules**
   - Remove only scratch/tmp/generated files that are safe to remove.
   - Preserve formal task cards, audit evidence, contract files, test catalogs, and release manifests.
   - Do not delete `参考项目/**` unless a separate repository-management decision exists; release package may exclude it from runtime artifacts but must not silently remove historical/reference material.

4. **Runbook pointers**
   - Manifest must point to backup/restore, rollback, bad-source quarantine, and production clean-write disable-switch docs.
   - If a runbook is absent, list as limitation or create a narrow pointer doc; do not invent completed operational proof.

5. **Readiness posture**
   - If Round3H/Round3G/Round4/3F-R items are incomplete, list them in `known_limitations` or `open_deferred_items` with owner/phase/closure test.
   - Source readiness must be represented only as `READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`, or `DISABLED_SOURCE`, with source limitation and route/evidence status carried forward from the R3H audit.
   - Do not claim production-live or clean-write readiness without matching gates.

---

## 6. Forbidden scope

- No product feature implementation.
- No deletion of formal historical task cards without redirect.
- No deletion of audit evidence.
- No hiding unresolved/deferred rows.
- No production-readiness claim without matching gates.
- No packaging of reference project runtime code as QMD runtime.
- No broad cleanup that removes files only because they are inconvenient.

---

## 7. Tests / gates

Required command set:

```bash
uv sync --locked
uv run pytest tests/test_docs_consistency.py tests/test_release_manifest.py tests/test_package_cleanup.py -q
```

If exact test files differ, update this card and `tests/test_catalog.yaml`.

Test expectations:

- manifest schema validates;
- manifest production/source/write posture matches roadmap and gate files;
- manifest carries Round3H source final decisions, source limitation, and route/evidence status without inventing source readiness;
- unresolved/deferred items are not hidden;
- package cleanup preserves formal tasks and evidence;
- docs consistency check recognizes canonical batch-folder hierarchy;
- excluded reference/runtime paths are explicit, not silent.

---

## 8. Done criteria

B05_03 is done only when release manifest, docs consistency checks, and cleanup rules accurately represent readiness and preserve evidence. It must not close by deleting files or by claiming readiness beyond proven gates.
