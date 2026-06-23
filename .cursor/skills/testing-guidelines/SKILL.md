---
name: testing-guidelines
description: Behavioral guidelines for writing and reviewing tests that verify business outcomes, not implementation details. Use when writing tests, reviewing test quality, planning MASTER §5, Audit A8, refactoring brittle tests, fixing flaky tests, or raising coverage without weak asserts. Triggers on "写测试", "单测规范", "mock 边界", "脆化测试", "GLOBAL_TESTING_POLICY".
license: MIT
---

# Testing Guidelines

Behavioral guidelines to reduce common LLM testing mistakes: over-mocking, weak assertions, and tests that break on every refactor. Derived from the project **Global Testing Policy** and user testing standards.

**Tradeoff:** These guidelines bias toward **behavioral confidence** over **coverage KPIs** or **call-count theater**. For trivial one-liners, use judgment — still avoid `assertNotNull`-only tests.

## When to Use

- Writing or extending unit/integration tests before or after production code (TDD / RED–GREEN).
- Reviewing AI-generated or human-written tests for semantic assertions and mock boundaries.
- Trellis Execute (MASTER §5), Audit A8, or `execute-skill-paths.yaml` routes testing work here.
- Refactoring brittle suites (`verify()`-only, call-order asserts) or stabilizing flaky fixtures.
- Planning coverage gates or prioritizing high-risk modules (WriteManager, ResourceGuard, validators).

## When NOT to Use

- **Production implementation only** — pair with `karpathy-guidelines` for code changes; this skill governs tests, not feature logic.
- **One-line trivial helpers** — judgment applies; still avoid null-only asserts if a test is added.
- **E2E / browser / load testing playbooks** — follow project CI and dedicated ops docs unless the task explicitly scopes pytest/unit work.
- **Replacing `GLOBAL_TESTING_POLICY.md`** — that doc is the project policy summary; this skill is the agent-facing behavioral contract.

## 1. Mock Only External I/O

**Mock at the system boundary. Run real logic inside.**

生成单测时：

1. 最多mock外部I/O（数据库、HTTP调用、消息队列）
2. 纯计算逻辑和条件分支，使用真实值而不是mock
3. Assert要验证返回值的内容，而不只是验证方法调用
4. 每个测试的assert至少要有一个assertEquals/assertThat对实际值的断言

Allow mock / fixture / fake:

- Database connections and drivers (use sandbox DB or in-memory when feasible).
- HTTP clients and remote APIs.
- Filesystem I/O outside `tmp_path` / sandbox fixtures.
- Message queues and async brokers.
- Email, webhooks, desktop notifications, third-party SDKs.

Do **not** mock:

- Pure calculation and branching you own.
- Schema / validation logic you own.
- Domain rules (e.g. ResourceGuard decisions, conflict resolution) — feed real inputs.

## 2. Assert Behavior, Not Implementation

**Test what the caller observes. Ignore how private helpers get there.**

让测试断言行为而非实现：约束：

- 断言的是方法的输出（返回值、状态变化、持久化结果）
- 不断言内部private方法是否被调用、被调用几次
- 不断言两个协作方法的调用顺序，除非顺序本身是业务约束

Unless call order **is** the business contract, never assert:

- Private or internal methods were called (or how many times).
- Collaboration order between internal helpers.
- Implementation details unrelated to the observable outcome.

Map to your stack (examples, not exclusive):

| Intent            | Java           | Python (pytest)                   | Go                 |
| ----------------- | -------------- | --------------------------------- | ------------------ |
| Business equality | `assertEquals` | `assert x == y`                   | `assert.Equal`     |
| Rich condition    | `assertThat`   | `assert ...` with clear predicate | `assert` + helpers |

## 3. Meaningful Assertions Required

**Every test must prove a business fact. Weak-only tests are invalid.**

每个测试必须包含至少一个对业务语义有意义的断言，即：

- assertEquals(expectedValue, actualValue) 其中 expectedValue 是业务上正确的值
- 或 assertThat(result).satisfies(r -> ...) 包含业务约束的条件检查
- 禁止只写 assertNotNull、assertDoesNotThrow 作为唯一断言

Valid semantic assertions include:

- Return value equals a **business-correct** expected value.
- State or persisted record contains the right fields / codes / flags.
- Error code, validation report, or quality marker matches the rule.

Forbidden as the **only** assertion:

- `assertNotNull` / `assertIsNotNone` / non-nil checks alone.
- `assertDoesNotThrow` / "no exception" alone.
- Mock `verify()` with **no** outcome assertion.

## 4. Scenarios to Cover

**One test, one behavior. Cover the paths that fail in production.**

Each `@Test` / `test_*` should verify **one** behavior. Per module, aim for at least:

- Happy path.
- Null / missing / empty input.
- Boundary values (0, min, max, empty collection).
- Exception / error path.
- Resource limits (disk, memory guard, batch caps) when applicable.
- Data-quality / validation failure paths.
- Blocked or disallowed actions (fail-closed).

Naming (language-neutral):

```text
methodName_condition_expectedBehavior
```

Examples:

```text
validate_sourceConflict_disabledSource_shouldRejectWrite
resourceGuard_lowDisk_shouldHardStop
```

## 5. Coverage Strategy

**Cover risk first. Do not chase a vanity percentage on day one.**

1. **Discover baseline** — use **this repo's** coverage tool (read manifest / CI; do not assume a language):
   - Examples: `pytest --cov`, `go test -coverprofile`, JaCoCo, `cargo tarpaulin`, Istanbul — **pick what the project already uses**.
2. **Prioritize** — lowest coverage + highest business risk first; bugs historically cluster there.
3. **High-value 20%** beats uniform 80% with shallow tests.
4. **CI gate** — start at **current coverage minus a small margin** (e.g. −5%), not 80% on day one; raise gradually per quarter.
5. **Prevent regression** — new code should not lower the gate without explicit approval.

For **quant-monitor-desk**, prioritize (see [GLOBAL_TESTING_POLICY.md](../../../docs/implementation_tasks/GLOBAL_TESTING_POLICY.md)):

- WriteManager, ResourceGuard, validators, Layer loaders, fail-closed guards.

## 6. Generate, Then Review

**AI-generated tests are drafts until a human (or Audit) checklist passes.**

When generating tests, enforce the constraints in §1–§4. After generation, **do not merge** until:

- [ ] Assertions check **business values**, not only `verify()` / call counts.
- [ ] Mocks are **external** dependencies, not the unit under test's core logic.
- [ ] At least one boundary (null, empty, negative, max) is covered.
- [ ] Name reads as **condition → expected behavior**.

Typical review: ~5 minutes per class; catches most bad tests early.

## 7. Fix Brittle Tests

**If every refactor breaks tests, you asserted the wrong layer.**

Symptom: large red suites after small production edits.

Fix:

1. Apply §1–§3 to **new** tests.
2. Refactor **existing** tests: replace `verify` / call-order asserts with outcome asserts; delete order checks unless contractual.
3. Re-run the **full** suite — same command CI uses.

## 8. Determinism and Golden Fixtures

**Non-deterministic tests are broken tests.**

When tests touch ingest, snapshots, reports, agents, or backtest output:

- Fix random seeds.
- Inject clock / `as_of_date`; no bare `now()` in assertions.
- Declare timezone (UTC or exchange TZ).
- Golden fixtures: manifest with input hash, as_of, version.
- Contract snapshots for API envelopes and structured JSON.
- No real network in unit tests — mock or fixture files.

Details: [GLOBAL_TESTING_POLICY.md §7](../../../docs/implementation_tasks/GLOBAL_TESTING_POLICY.md).

## 9. Trellis / quant-monitor-desk

**Tests are contract evidence for Execute and Audit.**

- Every test file: **中文** comment block — `purpose` / `verifies` / `failure_meaning` (do not change test **goal** to make green).
- Sandbox: `QMD_DATA_ROOT=<task>/.audit-sandbox/data`; Audit A8: `--basetemp=.audit-sandbox/pytest`.
- New module: `uv run python scripts/loop_maintain.py --fix` (test catalog).
- Audit A8: each original Red Flag → test | explicit defer | §4.3.
- Evidence: pytest output in `execute-evidence/`; not self-reported PASS.

## 10. Goal-Driven Execution

**Define what "green" proves. Loop until the command says so.**

Transform requests into verifiable goals:

- "Add tests" → "Write failing test for [behavior], then make `uv run pytest <selector>` pass"
- "Fix flaky" → "Reproduce with fixed seed/clock, then stabilize fixture"
- "Raise coverage" → "Cover [risky module] with semantic asserts; gate unchanged or raised in CI config"

For multi-step test work:

```text
1. Read existing tests in module → verify: pattern + fixtures understood
2. RED: one failing semantic test → verify: fails for right reason
3. GREEN: minimal prod change → verify: full pytest green
4. Review §6 checklist → verify: no weak-only asserts
```

Strong criteria let you loop independently. Weak criteria ("add some tests") require constant clarification.
