"""ponytail: regenerate §8.x-green.txt with pytest -v case names (AR-02)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[2]
OUT_DIRS = [TASK / "execute-evidence", TASK / "research" / "execute-evidence"]

# GREEN commands from MASTER §8 (append -v, drop -q)
STEPS: dict[str, list[str]] = {
    "8.0": ["tests/test_staged_pilot.py"],
    "8.1": [
        "tests/test_staged_pilot.py::test_stagedPilotV2_capsJson_matchesApprovedEnvelope",
        "tests/test_staged_pilot.py::test_stagedPilotV2_capsExceedingMaxSymbols_rejects",
    ],
    "8.2": ["tests/test_staged_pilot.py::test_stagedPilotV2_baostockExpanded_writesManifestV2"],
    "8.3": ["tests/test_staged_pilot.py::test_stagedPilotV2_cninfoExpanded_schemaFieldsPresent"],
    "8.4": ["tests/test_staged_pilot.py::test_stagedPilotV2_akshareValidation_recordsTaxonomy"],
    "8.5": ["tests/test_staged_pilot.py::test_stagedPilotV2_routePreviewMatrixV2_allStatuses"],
    "8.6": ["tests/test_staged_pilot.py::test_stagedPilotV2_validationReportV2_exposesQualityFlags"],
    "8.7": ["tests/test_staged_pilot.py::test_stagedPilotV2_conflictSummaryV2_primaryOrDeferred"],
    "8.8": [
        "tests/test_staged_pilot.py::test_mutationProof_verifiedOnlyWhenHashAndCountsUnchanged",
        "tests/test_staged_pilot.py::test_mutationProof_mutationDetectedWhenKeyTableRowsChange",
        "tests/test_staged_pilot.py::test_mutationProof_mutationDetectedWhenNonKeyTableRowCountChanges",
        "tests/test_staged_pilot.py::test_mutationProof_inconclusiveWhenHashChangesKeyCountUnchanged",
    ],
    "8.9": ["tests/test_staged_pilot.py::test_stagedPilotV2_closeoutMatrix_allSourcesClassified"],
    "8.10": [],  # full suite below
}


def run_pytest(targets: list[str]) -> tuple[int, str]:
    cmd = ["uv", "run", "pytest", "-v", *targets]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main() -> int:
    failed = False
    for step, targets in STEPS.items():
        if step == "8.10":
            code, out = run_pytest(["-q"])
        else:
            code, out = run_pytest(targets)
        body = out.rstrip() + f"\n\nEXIT:{code}\n"
        for d in OUT_DIRS:
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{step}-green.txt").write_text(body, encoding="utf-8")
        if code != 0:
            print(f"{step} FAILED exit {code}", file=sys.stderr)
            failed = True
        else:
            print(f"{step} OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
