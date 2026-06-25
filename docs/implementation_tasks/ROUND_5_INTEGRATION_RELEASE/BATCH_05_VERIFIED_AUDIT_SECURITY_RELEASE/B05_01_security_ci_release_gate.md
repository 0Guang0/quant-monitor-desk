# B05_01 — Security CI Release Gate

> Owns: `VR-SEC-001`.  
> Roadmap: Round 5.1.  
> Suggested branch: `chore/round5-security-ci`.  
> Parallel: should run after baseline CI is stable; can start report-only before hard-fail release gate.

---

## Goal

Integrate secret scanning and backend/Python security checks into release CI so security posture is not only documented or deferred.

## Scope

- Add gitleaks or equivalent secret scanning job.
- Add at least one Python/backend security scan suitable for project dependencies, such as bandit, semgrep, or pip-audit.
- Start with baseline/report-only if existing findings require triage; move to hard fail once baseline is reviewed.
- Document commands in ops/release verification docs.
- Update `R2-RISK-5` / `VR-SEC-001` registry status.

## Forbidden scope

- Do not commit secrets or sample credentials.
- Do not disable existing tests to make security job green.
- Do not add heavy hosted services without approval.
- Do not treat npm audit alone as sufficient closure.

## Gates

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
# plus configured security job commands, for example:
gitleaks detect --no-git
```

## Done criteria

- `VR-SEC-001` resolved or precisely re-deferred.
- CI has a distinct security job or documented staged rollout.
- Security commands are recorded in release/ops verification docs.
