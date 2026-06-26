# Context Closure — R3FR-03 Execute

## Upstream / wiring closure

- `tdx_manual_probe` → `TdxPytdxProbeFetchPort` → `TdxPytdxFetchPort` (gate-issued auth only)
- `normalizers/tdx.py` ← `adapters/tdx_pytdx.py` re-exports
- Caps SSOT: frozen §5.1 synced to gate, authorization MD, `source_capabilities.yaml`

## L2 modules (context_pack.json)

- `datasources` — fetch_ports/tdx_pytdx_port.py, normalizers/tdx.py, adapters
- `ops` — tdx_manual_probe, tdx_live_manual_probe_gate, interface_probe_fetch_ports

## Manifest §3 read

All implement.jsonl paths read; caps SSOT frozen §5.1 (equity/index max_rows=3).

## Evidence

- `execute-evidence/9.0`–`9.7` RED/GREEN txt present
- `research/gitnexus-execute-summary.md`

## Open (not closed by this task)

- B01-C03 live PROBE_REDEFERRED host placeholder (per frozen §12)
