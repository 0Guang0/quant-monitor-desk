# B04_02 — Agent Policy Runtime

> Owns: `VR-AGENT-001`.  
> Roadmap: Round 4.2.  
> Suggested branch: `feature/round4-agent-policy-runtime`.  
> Parallel: can run after or alongside read-only API work; must precede Agent endpoint exposure.

---

## Goal

Turn `agent_contract.yaml` from a static contract into enforceable runtime policy: allowed tools are explicit, forbidden tools are rejected, Agent output must be evidence-bound and read-only.

## Scope

- Implement minimal `AgentToolRegistry` from contract allowed tools.
- Implement `AgentExecutionPolicy` for read-only/no-free-SQL/no-direct-write/no-free-network rules.
- Require `evidence_ids`, `facts_used`, and no-action semantics in Agent outputs.
- Add forbidden-tool rejection tests and prompt-injection/no-action wording tests.

## Forbidden scope

- No autonomous trading/order APIs.
- No direct DuckDB writes.
- No arbitrary SQL.
- No free internet search.
- No clean table mutation from Agent output.

## Gates

```bash
uv sync --locked
uv run pytest tests/test_agent_contract.py tests/test_agent_policy.py -q
uv run ruff check backend/app/agents tests
```

## Done criteria

- `VR-AGENT-001` resolved or precisely re-deferred.
- `backend/app/agents` contains enforceable policy/runtime, not only package shell.
- Forbidden tools produce stable rejection errors.
