-- Round 1 repair: extended ResourceGuard metrics on audit log (GPT P0-4)

ALTER TABLE resource_guard_log ADD COLUMN IF NOT EXISTS system_memory_usage_pct DOUBLE;
ALTER TABLE resource_guard_log ADD COLUMN IF NOT EXISTS system_disk_usage_pct DOUBLE;
ALTER TABLE resource_guard_log ADD COLUMN IF NOT EXISTS cache_size_gb DOUBLE;
ALTER TABLE resource_guard_log ADD COLUMN IF NOT EXISTS duckdb_temp_size_gb DOUBLE;
