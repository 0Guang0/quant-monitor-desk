# B04_02 — Agent Policy Runtime and First Read-Only Tool

> **Batch:** Batch 04 — Verified Audit Productization  
> **Owns:** `VR-AGENT-001`, loose historical cards `025_implement_agent_tool_layer.md`, `030_implement_no_action_semantics_guard.md`  
> **Roadmap:** Round 4.2 track.  
> **Execution posture:** read-only Agent tool runtime; no write, no free SQL, no free web, no trading action semantics.

---

## 1. Business purpose

Turn `specs/contracts/agent_contract.yaml` from static policy into enforceable runtime policy plus one working read-only tool. The first vertical slice must prove that Agent access is bounded by QMD contracts and evidence, not by free-form LLM behavior.

This task is not complete if it only creates a policy class or package shell.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
specs/contracts/agent_contract.yaml
specs/contracts/api_security_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/data_quality_rules.yaml
specs/contracts/source_conflict_rules.yaml
specs/contracts/user_input_privacy_contract.yaml
docs/modules/agent_module.md
docs/modules/layer5_security_evidence.md
docs/modules/data_validation_and_conflict.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/025_implement_agent_tool_layer.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/030_implement_no_action_semantics_guard.md
```

---

## 3. Reference project source to inspect

Read these files under `参考项目/**` as design references only:

```text
参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
参考项目/agents-for-openbb/31-vanilla-agent-reasoning-steps/
参考项目/agents-for-openbb/32-vanilla-agent-raw-widget-data-citations/
参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py
```

Useful ideas to adapt into QMD-owned code:

- descriptor/registry idea similar to `/agents.json`, but QMD should expose internal tool metadata, not OpenBB agent descriptors;
- explicit context/widget-data retrieval pattern: fetch data only when tool context is explicitly supplied or allowed;
- context truncation and latest-context-only idea to prevent unbounded prompt context;
- dashboard/widget formatting idea from `40-vanilla-agent-dashboard-widgets`, but only as output-shape inspiration;
- streaming/LLM invocation is **not** required in this task.

Must not copy:

- OpenAI client calls or model invocation loop;
- OpenBB `openbb_ai` imports;
- CORS config from the reference;
- external widget fetchers;
- any path that lets Agent fetch arbitrary web/source data;
- any source of facts outside QMD evidence/tool outputs.

---

## 4. Target QMD files

Create/update QMD-owned files only:

```text
backend/app/agents/__init__.py
backend/app/agents/tool_registry.py
backend/app/agents/execution_policy.py
backend/app/agents/tools/source_readiness.py
backend/app/agents/tools/evidence_context.py
backend/app/agents/output_contract.py
backend/app/api/routes/agent_tools.py
backend/app/api/schemas/agent_tools.py
specs/contracts/agent_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_agent_contract.py
tests/test_agent_policy.py
tests/test_agent_tools_source_readiness.py
tests/test_no_action_semantics.py
tests/test_catalog.yaml
```

If final names differ, the PR must document the mapping.

---

## 5. Implementation plan

1. **Tool registry**
   - Load allowed and forbidden tool names from `agent_contract.yaml`.
   - Expose a deterministic registry API such as `list_allowed_tools()` and `resolve_tool(tool_name)`.
   - Unknown or forbidden tools fail closed with stable error codes.

2. **Execution policy**
   - Implement `AgentExecutionPolicy` checks before any tool call:
     - read-only only;
     - no arbitrary SQL;
     - no direct DuckDB write;
     - no free internet/web fetch;
     - no registry mutation;
     - no clean table mutation;
     - ResourceGuard budget where applicable.

3. **First allowed tool**
   - Implement one real read-only tool, preferably `get_data_quality_summary`, `get_source_conflict_summary`, or `source_readiness_summary`.
   - Tool must use B04_01 API/service layer or QMD service boundary, not direct YAML parsing in Agent code and not free SQL.
   - Output must include `facts_used`, `evidence_ids` or `missing_evidence`, `limitations`, and `source_contract_refs`.

4. **No-action output contract**
   - Implement output validation that rejects or rewrites forbidden action terms from `agent_contract.yaml`.
   - Agent output may include analysis, risk explanation, missing evidence, and human-review recommendation.
   - Agent output must not include buy/sell/add/reduce/position instructions or broker/order language.

5. **API exposure**
   - If exposing HTTP route, add read-only route under `backend/app/api/routes/agent_tools.py`.
   - Route must require API auth and policy checks.
   - Do not expose LLM chat orchestration in this task unless contract already exists; this task is tool/policy runtime.

6. **Contract/test updates**
   - Update `contract_coverage.yaml` if new tests become authoritative.
   - Update `tests/test_catalog.yaml` for new test files.

---

## 6. Forbidden scope

- No autonomous trading/order APIs.
- No direct DuckDB writes.
- No arbitrary SQL.
- No free internet search or browser fetch.
- No clean table mutation from Agent output.
- No Agent-triggered source fetch or production write.
- No import from `参考项目/**`.
- No OpenBB/agents-for-openbb runtime dependency.

---

## 7. Tests / gates

Required commands:

```bash
uv sync --locked
uv run pytest tests/test_agent_contract.py tests/test_agent_policy.py tests/test_agent_tools_source_readiness.py tests/test_no_action_semantics.py -q
uv run ruff check backend/app/agents backend/app/api tests
```

Test expectations:

- allowed read-only tool executes and returns evidence-bound context;
- forbidden tool names are rejected;
- unknown tools are rejected;
- prompt-injection attempt cannot bypass policy;
- output with forbidden action terms fails validation or is converted to non-action language;
- tool output includes limitations when evidence is incomplete;
- no runtime import from `参考项目/**`.

---

## 8. Done criteria

B04_02 is done only when `backend/app/agents` contains enforceable policy/runtime and one working read-only tool with tests. Policy-only scaffolding is not acceptable.
