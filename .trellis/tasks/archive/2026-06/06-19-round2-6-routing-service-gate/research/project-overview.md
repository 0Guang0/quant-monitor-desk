# Project Overview — Routing Service Gate

Round2 currently has working source registry, adapter skeletons, sync runners, validators, job_event_log payloads, and fixture E2E. Round2.6 Phase A introduced missing design contracts; Task 1 will make those contracts executable. This task then implements the production service boundary required before Round3 modeling expands dependencies.

The central design is a three-layer boundary:

```text
SourceRegistry — source/domain/role authority
SourceCapabilityRegistry — operation/field/auth capability authority
SourceRoutePlanner — runtime candidate/disabled/fallback explanation
DataSourceService — production fetch facade using ResourceGuard and internal adapter factory
```

Route persistence should use existing `job_event_log.payload_json` unless Execute proves it cannot satisfy SourceRoutePlan evidence needs.
