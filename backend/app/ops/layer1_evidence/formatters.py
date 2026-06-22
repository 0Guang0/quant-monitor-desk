"""Phase evidence markdown formatters (L1-07 extract)."""

from __future__ import annotations

from typing import Any


def _format_count_table_md(title: str, counts: dict[str, int | None]) -> list[str]:
    lines = [f"## {title}", "", "| table | row_count |", "| ----- | --------- |"]
    for name, count in counts.items():
        lines.append(f"| `{name}` | {count} |")
    lines.append("")
    return lines


def format_phase2_route_preview_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — Route Preview Matrix",
        "",
        f"- **Generated at:** {payload['generated_at']}",
        f"- **Frozen indicator:** `{payload['frozen_indicator']}`",
        f"- **Dry-run:** {payload['dry_run']}",
        f"- **FRED live deferred:** {payload.get('fred_primary_deferred')}",
        "",
        "## Allowlist",
        "",
    ]
    for item in payload.get("allowlist", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Route previews", ""])
    for entry in payload.get("previews", []):
        plan = entry["route_plan"]
        binding = entry["binding"]
        lines.extend(
            [
                f"### `{entry['indicator_id']}` @ {entry['as_of']}",
                "",
                f"- data_domain: `{binding['data_domain']}`",
                f"- operation: `{binding['operation']}`",
                f"- series_id: `{binding.get('series_id')}`",
                f"- declared primary: `{binding['primary_source_declared']}`",
                f"- staged note: {binding.get('staged_route_note')}",
                f"- route_status: `{plan['route_status']}`",
                f"- selected_source_id: `{plan.get('selected_source_id')}`",
                f"- resource_guard: `{entry['resource_guard_decision']}`",
                f"- capability_verified: {entry.get('capability_verified')}",
                f"- intended_as_of_range: {entry.get('intended_as_of_range')}",
                f"- stop_reason: {entry.get('stop_reason')}",
                "",
                "| source_id | role | enabled | skip_reason |",
                "| --------- | ---- | ------- | ----------- |",
            ]
        )
        for candidate in plan.get("candidates", []):
            lines.append(
                f"| `{candidate['source_id']}` | {candidate['role']} | "
                f"{candidate['enabled']} | {candidate.get('skip_reason')} |"
            )
        lines.append("")
    proof = payload.get("mutation_proof", {})
    lines.extend(
        [
            "## No-mutation proof",
            "",
            f"- db_path: `{proof.get('db_path')}`",
            f"- db_capture_strategy: `{proof.get('db_capture_strategy')}`",
            f"- db_file_hash_unchanged: {proof.get('db_file_hash_unchanged')}",
            f"- row_counts_unchanged: {proof.get('row_counts_unchanged')}",
            f"- before: `{proof.get('before_counts')}`",
            f"- after: `{proof.get('after_counts')}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def format_phase2_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — No Mutation Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **DB file hash unchanged:** {proof.get('db_file_hash_unchanged')}",
        f"- **Capture strategy:** {proof.get('db_capture_strategy')}",
        f"- **Row counts unchanged:** {proof['row_counts_unchanged']}",
        "",
    ]
    lines.extend(_format_count_table_md("Before preview", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After preview", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


def format_phase3_no_clean_write_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 3 — No Clean Write Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **axis_observation unchanged:** {proof['axis_observation_unchanged']}",
        f"- **fetch_log delta:** {proof['fetch_log_delta']}",
        f"- **file_registry delta:** {proof['file_registry_delta']}",
        "",
    ]
    lines.extend(_format_count_table_md("Before micro-fetch", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After micro-fetch", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


def format_phase4_inventory_delta_md(delta: dict[str, Any]) -> str:
    lines = [
        "# Phase 4 — Inventory Delta",
        "",
        f"- **Generated at:** {delta['generated_at']}",
        f"- **DB path:** `{delta['db_path']}`",
        f"- **Frozen indicator:** `{delta['frozen_indicator']}`",
        f"- **Staged fixture:** `{delta.get('staged_fixture_path')}`",
        "",
        "## Row-count deltas",
        "",
        "| table | before | after | delta |",
        "| ----- | ------ | ----- | ----- |",
    ]
    for name, counts in delta.get("table_deltas", {}).items():
        before = counts.get("before")
        after = counts.get("after")
        delta_val = (after or 0) - (before or 0)
        lines.append(f"| `{name}` | {before} | {after} | {delta_val} |")
    lines.append("")
    return "\n".join(lines) + "\n"
