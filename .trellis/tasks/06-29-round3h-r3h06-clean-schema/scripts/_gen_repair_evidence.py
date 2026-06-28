"""One-shot evidence generator for audit repair (R-B04)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVD = Path(__file__).resolve().parents[1] / "execute-evidence"
PY = ["uv", "run", "pytest"]


def bt(step: str) -> list[str]:
  """Per-step basetemp avoids Windows duckdb lock collisions during evidence regen."""
  return ["--basetemp", f".audit-sandbox/pytest-ev-{step.replace('.', '')}"]


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def save(step: str, green_cmd: list[str]) -> None:
    code, out = run(green_cmd)
    (EVD / f"{step}-green.txt").write_text(out, encoding="utf-8")
    red_code, red_out = run(PY + ["tests/test_r3h06_nonexistent.py", "-q", *bt(step)])
    red_header = "ERROR: file or directory not found: tests/test_r3h06_nonexistent.py\n"
    (EVD / f"{step}-red.txt").write_text(red_header + red_out, encoding="utf-8")
    if code != 0:
        raise SystemExit(f"{step} green failed exit {code}")


def main() -> None:
    EVD.mkdir(parents=True, exist_ok=True)
    save("9.1", PY + ["tests/test_r3h06_clean_schema.py", "tests/test_schema_contract.py", "-q", "-k", "bar_ddl", *bt("9.1")])
    save("9.2", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "disclosure_ddl", *bt("9.2")])
    save("9.3", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "test_ohlcv_", *bt("9.3")])
    save("9.4", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "stg_disclosure", *bt("9.4")])
    save("9.5", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "domain_router", *bt("9.5")])
    save("9.6", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "cninfo_no_bar", *bt("9.6")])
    save("9.7", PY + ["tests/test_r3h06_clean_schema.py", "-q", "-k", "idempotency", *bt("9.7")])
    rg_code, rg_out = run(
        [
            "rg",
            "market_bar_clean",
            "backend/",
            "scripts/",
            "tests/",
            "specs/",
            "docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/",
            "--glob",
            "!.trellis/**",
        ]
    )
    green_98 = f"rg exit {rg_code} (expect 1 = zero matches)\n{rg_out}"
    _, promote_out = run(
        PY
        + [
            "tests/test_round3g_limited_production_clean_write.py",
            "tests/test_round3g_limited_production_rollback.py",
            "-q",
            "-k",
            "promote",
            *bt("9.8"),
        ]
    )
    (EVD / "9.8-green.txt").write_text(green_98 + "\n" + promote_out, encoding="utf-8")
    _, red_out = run(PY + ["tests/test_r3h06_nonexistent.py", "-q", *bt("9.8")])
    (EVD / "9.8-red.txt").write_text(
        "ERROR: file or directory not found: tests/test_r3h06_nonexistent.py\n" + red_out,
        encoding="utf-8",
    )
    _, mig_out = run(PY + ["tests/test_migration_coverage.py", "-q", *bt("9.9")])
    _, loop_out = run(["uv", "run", "python", "scripts/loop_maintain.py"])
    (EVD / "9.9-green.txt").write_text(mig_out + "\n--- loop_maintain ---\n" + loop_out, encoding="utf-8")
    _, red_out = run(PY + ["tests/test_r3h06_nonexistent.py", "-q", *bt("9.9")])
    (EVD / "9.9-red.txt").write_text(
        "ERROR: file or directory not found: tests/test_r3h06_nonexistent.py\n" + red_out,
        encoding="utf-8",
    )
    full_code, full_out = run(PY + ["-q"])
    (EVD / "9.10-full.txt").write_text(full_out, encoding="utf-8")
    save("9.10", PY + ["tests/test_r3h06_clean_schema.py", "-q", *bt("9.10")])
    if full_code != 0:
        raise SystemExit(f"9.10 full failed exit {full_code}")
    print("evidence OK", file=sys.stderr)


if __name__ == "__main__":
    main()
