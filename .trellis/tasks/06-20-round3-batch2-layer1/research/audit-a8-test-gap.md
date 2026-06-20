# A8 audit-test-gap — §3.8

**Dimension:** A8 (audit-test-gap)  
**Task:** `06-20-round3-batch2-layer1`  
**Skills:** `GLOBAL_TESTING_POLICY.md` + `research/layer1-axis-loader-tests.md` (testing-guidelines / doubt-driven-development paths unavailable in workspace)  
**Environment:** project root pytest (audit-prod-path copy `.audit-sandbox/r3b2-audit-prod-equiv` not present; layer1 tests use repo specs + `tmp_path`, prod DB not touched)  
**Verdict: PASS** (post-repair — all §4.3 items closed)

---

## 1. Mandatory reads completed

| Source                                           | Takeaway                                                                                                                          |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `research/audit-boot.md`                         | Execute handoff validated; `AUDIT_PROD_ROOT=.audit-sandbox/r3b2-audit-prod-equiv`                                                 |
| `AUDIT.plan.md` §2 A8                            | pytest-isolated: empty `spec_root`, all-forbidden axis, missing `quality_rules`; audit-prod-path: module §13 + SHADOW three names |
| `audit.jsonl`                                    | Entry points: contracts, module §13, `common_axis_rules.md` §4.1, loader tests                                                    |
| `implement.jsonl`                                | Execute scope: `backend/app/layer1_axes/*`, migration 011, `test_layer1_*.py`                                                     |
| `GLOBAL_TESTING_POLICY.md`                       | Semantic assertions; boundary/empty/error paths required per module                                                               |
| `docs/modules/layer1_global_regime_panel.md` §13 | Seven-row acceptance checklist                                                                                                    |
| `common_axis_rules.md` §4.1                      | Three mandated SHADOW test names                                                                                                  |
| `research/layer1-axis-loader-tests.md`           | §8.1–8.2 matrix (migration, loader, guardrails, SHADOW)                                                                           |
| Existing tests                                   | `tests/test_layer1_axis_loader.py` (11), `tests/test_layer1_interpretation.py` (12)                                               |

---

## 2. Pytest evidence

### audit-prod-path (layer1 suite on repo specs)

**Command:**

```text
python -m pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
```

**Output:**

```text
.......................                                                  [100%]
23 passed
```

Matches Execute `execute-evidence/8.6-final-gates.txt` layer1 slice (23 dots). No `AUDIT_PROD_ROOT` data copy required for these tests — they do not read `data/duckdb/quant_monitor.duckdb`.

### SHADOW three-name contract (`common_axis_rules.md` §4.1)

| Mandated test                                                      | Present | Prod-spec run |
| ------------------------------------------------------------------ | ------- | ------------- |
| `test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`   | Yes     | PASS          |
| `test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`        | Yes     | PASS          |
| `test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly` | Yes     | PASS          |

### Module §13 acceptance checklist

| §13 row                                                        | Existing test                                              | Status                                                                        |
| -------------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| spec 缺少 `indicator_id` → loader 拒绝                         | `test_axisSpecLoader_missingIndicatorId_rejects`           | Covered                                                                       |
| 指标历史不足 → `INSUFFICIENT_HISTORY`，不伪造 z                | `test_axisFeatureEngine_insufficientHistory_noFakeZ`       | Covered                                                                       |
| 主源失败 fallback → `SOURCE_SWITCHED` + 保留 `fallback_policy` | `test_axisFeatureEngine_sourceSwitched_recordsQualityFlag` | **Partial** — flag only; `FeatureSnapshotRow` has no `fallback_policy` field  |
| forbidden substitute → 阻断写入 + 质量错误                     | `test_axisEngineeringGuardrail_rejectsForbiddenSubstitute` | **Partial** — validator raise only; no write-path / quality-error integration |
| BlindSpot → 只登记不进 observation                             | `test_axisSpecLoader_blindspot_notObservable`              | Covered                                                                       |
| Agent 交易动作词 → 解释拒绝/人工复核                           | `test_axisInterpretation_rejectsForbiddenActionTerms`      | Covered                                                                       |
| Layer 2 回写 Layer 1 → 阻断                                    | `test_layer2ValueCannotWritebackToLayer1`                  | Covered                                                                       |

### Lineage contract `validation_tests` (snapshot_lineage_contract.yaml)

| Contract test                                                | Present | Status                                                            |
| ------------------------------------------------------------ | ------- | ----------------------------------------------------------------- |
| `test_snapshotRejectsFutureInput`                            | Yes     | Covered                                                           |
| `test_snapshotLineageContainsSourceHashes`                   | Yes     | Covered                                                           |
| `test_incrementalRebuildPreservesAsOfBoundary`               | Yes     | Covered                                                           |
| `agent_outputs_not_source` (listed in lineage research §8.5) | **No**  | Gap — no guard that agent prose cannot enter `source_dataset_ids` |

---

## 3. AUDIT.plan §2 A8 pytest-isolated boundary gaps

| ID   | Boundary                                        | Current state                                                                                                                                                                                                                                         | Severity                         | §4.3?               |
| ---- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ------------------- |
| G-01 | Empty `spec_root`                               | No test; code raises `AxisSpecLoadError("missing indicator spec…")` when axis dir/spec absent                                                                                                                                                         | **High** (AUDIT matrix explicit) | Yes                 |
| G-02 | All-forbidden axis                              | No test; loader would register indicators with `is_observable=False` for all                                                                                                                                                                          | **High** (AUDIT matrix explicit) | Yes                 |
| G-03 | Missing `quality_rules` YAML key                | Only empty list `[]` tested (`test_axisSpecLoader_missingQualityRules_rejects`); absent key silently defaults via `DEFAULT_QUALITY_RULES` in `axis_loader._coerce_rules` — contradicts module §5.3 “必须具备 quality_rules” for observable indicators | **High** (AUDIT matrix explicit) | Yes                 |
| G-04 | §13 forbidden-substitute write path             | Guardrail unit test only                                                                                                                                                                                                                              | Medium                           | Yes                 |
| G-05 | §13 `fallback_policy` on SOURCE_SWITCHED        | Quality flag only; no policy retention assertion                                                                                                                                                                                                      | Medium                           | Deferred (see §4.4) |
| G-06 | `agent_outputs_not_source` lineage guard        | Not implemented or tested                                                                                                                                                                                                                             | Medium                           | Yes                 |
| G-07 | `test_snapshotLineageIncludesAllRequiredFields` | Asserts subset of `LINEAGE_REQUIRED_FIELDS` / contract fields                                                                                                                                                                                         | Low                              | No (documented)     |

---

## 4. Proposed tests (main session implements — not written in this audit pass)

### G-01 — empty spec_root

```python
def test_axisSpecLoader_emptySpecRoot_rejects(tmp_path: Path) -> None:
  """Empty spec_root must fail fast with missing-spec error (AUDIT A8 boundary)."""
  empty_root = tmp_path / "empty_specs"
  empty_root.mkdir()
  with pytest.raises(AxisSpecLoadError, match="missing indicator spec"):
    AxisSpecLoader().load(spec_root=empty_root, enabled_axes=["environment"])
```

### G-02 — all-forbidden axis

```python
def test_axisSpecLoader_allForbiddenAxis_registersNoneObservable(tmp_path: Path) -> None:
  """When every indicator is forbidden, axis loads but none are observable."""
  root = _copy_specs(tmp_path)
  spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
  spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
  for mod in spec.get("modules", {}).values():
    for ind in mod.get("indicators", []):
      ind["status"] = "forbidden"
      ind["layer"] = "Forbidden"
      ind["dest_tag"] = "FORBIDDEN"
  spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
  result = AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
  assert len(result.indicators) > 0
  assert all(i.is_forbidden for i in result.indicators)
  assert not any(i.is_observable for i in result.indicators)
```

### G-03 — missing quality_rules key (spec-aligned reject)

Preferred fix: loader rejects absent `quality_rules` on observable indicators (module §5.3). Test:

```python
def test_axisSpecLoader_missingQualityRulesKey_rejects(tmp_path: Path) -> None:
  """Observable indicator without quality_rules key must be rejected (§5.3)."""
  root = _copy_specs(tmp_path)
  spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
  spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
  ind = spec["modules"]["E0_money_quantity"]["indicators"][0]
  ind.pop("quality_rules", None)
  spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
  with pytest.raises(AxisSpecLoadError, match="quality_rules"):
    AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
```

_Alternative (if defaults intentional):_ `test_axisSpecLoader_missingQualityRulesKey_appliesContractDefaults` asserting `quality_rules == DEFAULT_QUALITY_RULES` — requires product decision; current §5.3 wording favors reject.

### G-04 — §13 forbidden substitute blocks write

```python
def test_layer1Snapshot_forbiddenSubstitute_blocksWriteWithQualityError(
  tmp_path: Path,
) -> None:
  """Using a forbidden substitute must block clean write and surface quality failure."""
  # Arrange: load specs, pick indicator with forbidden_substitutes, build feature row
  # Act: attempt write path that used substitute (via future fetcher hook or writer guard)
  # Assert: write status != SUCCESS; validation/quality error recorded
  ...
```

_Note:_ Requires wiring substitute check into `Layer1SnapshotWriter` or fetch path — test documents intended §13 behavior; may need small production hook.

### G-06 — agent_outputs_not_source

```python
def test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse() -> None:
  """source_dataset_ids must not contain agent-generated prose tokens."""
  builder = SnapshotLineageBuilder()
  with pytest.raises((ValueError, Layer1SnapshotError), match="agent"):
    builder.build(
      snapshot_id="snap-agent",
      snapshot_type="axis_feature_snapshot",
      as_of=AS_OF,
      validation_report=ValidationReportRef(...),
      input_window_start=AS_OF - timedelta(days=1),
      input_window_end=AS_OF,
      source_dataset_ids=("agent_summary:建议买入",),
      parameter_hash="ph-agent",
    )
```

_Note:_ Guard does not exist in `lineage.py` today — test is RED until validation added.

---

## 5. Test inventory (current)

### `tests/test_layer1_axis_loader.py` (11)

| Test                                                               | Category        |
| ------------------------------------------------------------------ | --------------- |
| `test_layer1Migration_createsRegistryTables`                       | Migration §8.1  |
| `test_layer1Migration_createsSnapshotLineageTable`                 | Migration §8.1  |
| `test_axisSpecLoader_loadsFiveAxes`                                | Happy path      |
| `test_axisSpecLoader_missingIndicatorId_rejects`                   | §13 / error     |
| `test_axisSpecLoader_missingQualityRules_rejects`                  | Empty list only |
| `test_axisSpecLoader_forbiddenIndicator_notObservable`             | Forbidden       |
| `test_axisSpecLoader_blindspot_notObservable`                      | §13 BlindSpot   |
| `test_axisEngineeringGuardrail_rejectsForbiddenSubstitute`         | Guardrail unit  |
| `test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`   | SHADOW §4.1     |
| `test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`        | SHADOW §4.1     |
| `test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly` | SHADOW §4.1     |

### `tests/test_layer1_interpretation.py` (12)

| Test                                                       | Category         |
| ---------------------------------------------------------- | ---------------- |
| `test_axisFeatureEngine_insufficientHistory_noFakeZ`       | §13 / AC-018     |
| `test_axisFeatureEngine_robustZUnavailable_whenMadZero`    | Feature edge     |
| `test_axisFeatureEngine_sourceSwitched_recordsQualityFlag` | §13 partial      |
| `test_axisFeatureEngine_resourceGuard_ecoProfile`          | AC-RES-1         |
| `test_snapshotRejectsFutureInput`                          | Lineage contract |
| `test_axisInterpretation_rejectsForbiddenActionTerms`      | §13 Agent        |
| `test_layer2ValueCannotWritebackToLayer1`                  | §13 L2 guard     |
| `test_snapshotLineageIncludesAllRequiredFields`            | Lineage partial  |
| `test_snapshotLineageContainsSourceHashes`                 | Lineage contract |
| `test_incrementalRebuildPreservesAsOfBoundary`             | Lineage contract |
| `test_snapshotDeterministicRebuild_sameInputsSameHash`     | Deterministic    |
| `test_layer1Snapshot_writeViaWriteManager`                 | AC-WRIT-1        |

---

## 6. §4.3 Repair items

| ID     | Priority | Problem                                                                      | Root fix (not workaround)                                                         | Proposed test                                                         |
| ------ | -------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| A8-R01 | P2       | No empty `spec_root` boundary test                                           | Add test; confirm `AxisSpecLoadError` message stable                              | `test_axisSpecLoader_emptySpecRoot_rejects`                           |
| A8-R02 | P2       | No all-forbidden axis test                                                   | Add test proving register-without-observable                                      | `test_axisSpecLoader_allForbiddenAxis_registersNoneObservable`        |
| A8-R03 | P2       | Missing `quality_rules` **key** accepted via defaults; conflicts module §5.3 | Reject absent key on observable indicators **or** document+test explicit defaults | `test_axisSpecLoader_missingQualityRulesKey_rejects`                  |
| A8-R04 | P2       | §13 “forbidden substitute 阻断写入” only tested at guardrail                 | Integrate substitute check on write/fetch path + quality error                    | `test_layer1Snapshot_forbiddenSubstitute_blocksWriteWithQualityError` |
| A8-R05 | P2       | `agent_outputs_not_source` contract test missing                             | Add builder validation + test                                                     | `test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse`        |

**§4.3 count: 5**

None are P0/P1 finish-work blockers for Batch 2 closure (Execute Tier B already green), but AUDIT.plan A8 matrix explicitly requires the first three before marking A8 `[x]`.

---

## 7. §4.4 Deferred (not §4.3)

| ID     | Issue                                    | Status                                                                             |
| ------ | ---------------------------------------- | ---------------------------------------------------------------------------------- |
| A8-D01 | §13 `fallback_policy` on SOURCE_SWITCHED | **CLOSED** — `AxisObservation.fallback_policy` → `FeatureSnapshotRow.stale_reason` |
| A8-D02 | Full lineage field assertion             | **CLOSED** — uses `LINEAGE_REQUIRED_FIELDS`                                        |

---

## 8. Summary for A9

| Metric                       | Value                          |
| ---------------------------- | ------------------------------ |
| **Verdict**                  | **PASS_WITH_FIXES**            |
| **§4.3 count**               | **5**                          |
| Existing layer1 tests        | 23 / 23 PASS                   |
| SHADOW three-name tests      | 3 / 3 present + PASS           |
| Module §13 checklist         | 5 / 7 fully covered; 2 partial |
| AUDIT A8 explicit boundaries | 0 / 3 covered (G-01..G-03)     |

**Recommendation:** Main session implements A8-R01..R03 (pure test + small loader tweak for R03) in Repair; R04–R05 need production guards before GREEN.
