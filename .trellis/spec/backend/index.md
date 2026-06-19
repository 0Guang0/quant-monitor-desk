# Backend Development Guidelines

> Best practices for backend development in this project (Round 0–2 baseline filled).

---

## Overview

This directory contains **project-specific** backend conventions derived from the implemented codebase. Guides marked **Filled** reflect current `master` behavior; update them when architecture changes.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | Filled |
| [Database Guidelines](./database-guidelines.md) | DuckDB, migrations, WriteManager | Filled |
| [Error Handling](./error-handling.md) | Error types, redaction, gate failures | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Ruff, pytest, coverage, forbidden patterns | Filled |
| [Datasource Adapters](./datasource-adapters.md) | FetchPort, skeleton base, factory contracts | Filled |
| [Datasource Routing Service](./datasource-routing-service.md) | CapabilityRegistry, RoutePlanner, DataSourceService, sync service path | Filled (Round 2.6) |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, redaction on persisted errors | Partial (Batch D) |

---

## Maintenance

When adding a new backend package or changing write/validation boundaries:

1. Update the relevant guide with **actual** conventions and file paths.
2. Run `python scripts/check_doc_links.py` and full pytest before merge.
3. Run GitNexus `impact` before editing shared symbols.

---

**Language**: All documentation should be written in **English**.
