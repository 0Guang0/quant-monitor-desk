# Project Overview — Contract Gate

Quant Monitor Desk is a local-first market monitoring and evidence system. Round2 established source registry, adapter skeletons, validators, sync runners, DuckDB schema, ResourceGuard, and fixture vendor E2E. Round2.6 Phase A added new contracts for capability registry, source route planning, DataSourceService, module boundaries, platform matrix, CLI dry-run behavior, and operational documentation.

This task is the test/check gate before implementation. It should not build the production service facade. It should fail fast if Phase A contracts are incomplete, stale, or inconsistent with current code. The most important known mismatch is adapter `supported_domains` using legacy names while `source_registry.yaml` uses concrete domains.
