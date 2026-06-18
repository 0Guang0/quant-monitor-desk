"""Source registry YAML loader and DB sync (Batch A)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from backend.app.config import PROJECT_ROOT

VALID_FALLBACK_POLICIES = frozenset({
    "retry_same_source",
    "use_validation_source_with_flag",
    "use_last_good_cache",
    "mark_missing",
    "manual_review_required",
    "skip_until_next_publish",
})

BANNED_ROLE_NAMES = frozenset({"Shadow", "Emergency"})


class LegacyRoleError(ValueError):
    """Raised when YAML uses banned Shadow/Emergency role aliases."""


class InvalidRegistryError(ValueError):
    """Raised when YAML is malformed or fails validation."""


class SourceNotFoundError(KeyError):
    """Raised when source_id is unknown."""


class SourceDisabledError(RuntimeError):
    """Raised when source is disabled."""


class DomainNotAllowedError(ValueError):
    """Raised when data_domain is not allowed for source."""


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_name: str
    source_type: str
    allowed_domains: frozenset[str]
    trust_level: int
    license_type: str
    official_api: bool
    is_enabled: bool
    default_priority: int
    rate_limit_policy: str
    auth_required: bool
    requires_local_client: bool
    expected_frequency: str
    expected_lag: str
    timezone: str
    fallback_allowed: bool
    validation_only: bool
    notes: str


@dataclass(frozen=True)
class DomainRoleBinding:
    """Batch D Orchestrator stable getter contract."""

    primary_source_id: str
    validation_source_id: str | None
    fallback_policy: str


def _allowed_domains_to_db(domains: frozenset[str]) -> str:
    return json.dumps(sorted(domains))


def _resolve_registry_path(path: Path) -> Path:
    """Reject registry YAML paths outside the project root (SEC-A3-1)."""
    resolved = path.resolve()
    root = PROJECT_ROOT.resolve()
    if not resolved.is_relative_to(root):
        raise InvalidRegistryError(
            f"registry path must be under project root, got: {path}"
        )
    return resolved


def _parse_bool(entry: dict, key: str, *, default: bool, source_id: str) -> bool:
    if key not in entry:
        return default
    val = entry[key]
    if not isinstance(val, bool):
        raise InvalidRegistryError(
            f"source {source_id!r}: {key} must be YAML boolean, got {type(val).__name__}"
        )
    return val


def _parse_int(entry: dict, key: str, *, default: int, source_id: str) -> int:
    if key not in entry:
        return default
    val = entry[key]
    if isinstance(val, bool) or not isinstance(val, int):
        raise InvalidRegistryError(
            f"source {source_id!r}: {key} must be integer, got {type(val).__name__}"
        )
    return val


def _parse_required_str(entry: dict, key: str, source_id: str) -> str:
    if key not in entry:
        raise InvalidRegistryError(f"source {source_id!r}: missing required field {key!r}")
    val = entry[key]
    if not isinstance(val, str) or not val.strip():
        raise InvalidRegistryError(f"source {source_id!r}: {key} must be non-empty string")
    return val


def _parse_optional_str(entry: dict, key: str, *, default: str, source_id: str) -> str:
    if key not in entry:
        return default
    val = entry[key]
    if not isinstance(val, str):
        raise InvalidRegistryError(
            f"source {source_id!r}: {key} must be string, got {type(val).__name__}"
        )
    return val


def _parse_allowed_domains(entry: dict, source_id: str) -> frozenset[str]:
    if "allowed_domains" not in entry:
        raise InvalidRegistryError(f"source {source_id!r}: allowed_domains is required")
    allowed = entry["allowed_domains"]
    if not isinstance(allowed, list) or not allowed:
        raise InvalidRegistryError(
            f"source {source_id!r}: allowed_domains must be non-empty list"
        )
    domains: list[str] = []
    for item in allowed:
        if not isinstance(item, str) or not item.strip():
            raise InvalidRegistryError(
                f"source {source_id!r}: allowed_domains entries must be non-empty strings"
            )
        domains.append(item)
    return frozenset(domains)


def _record_to_db_row(rec: SourceRecord) -> dict[str, object]:
    return {
        "source_id": rec.source_id,
        "source_name": rec.source_name,
        "source_type": rec.source_type,
        "allowed_domain": _allowed_domains_to_db(rec.allowed_domains),
        "trust_level": rec.trust_level,
        "license_type": rec.license_type,
        "official_api": rec.official_api,
        "is_enabled": rec.is_enabled,
        "default_priority": rec.default_priority,
        "rate_limit_policy": rec.rate_limit_policy,
        "auth_required": rec.auth_required,
        "requires_local_client": rec.requires_local_client,
        "expected_frequency": rec.expected_frequency,
        "expected_lag": rec.expected_lag,
        "timezone": rec.timezone,
        "fallback_allowed": rec.fallback_allowed,
        "validation_only": rec.validation_only,
        "notes": rec.notes,
    }


class SourceRegistry:
    DEFAULT_YAML: Path = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or self.DEFAULT_YAML
        self._sources: dict[str, SourceRecord] = {}
        self._domain_roles: dict[str, DomainRoleBinding] = {}

    def load(self, path: Path | None = None) -> None:
        yaml_path = _resolve_registry_path(path or self._path)
        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise InvalidRegistryError(f"malformed YAML: {exc}") from exc
        if not isinstance(raw, dict):
            raise InvalidRegistryError("registry root must be a mapping")

        for banned_key in ("shadow_source", "emergency_source"):
            if banned_key in raw:
                raise LegacyRoleError(f"banned top-level key: {banned_key}")

        sources_raw = raw.get("sources")
        if not isinstance(sources_raw, dict):
            raise InvalidRegistryError("sources must be a mapping")

        self._sources = {}
        for source_id, entry in sources_raw.items():
            if not isinstance(entry, dict):
                raise InvalidRegistryError(f"source {source_id!r} must be a mapping")
            self._sources[source_id] = SourceRecord(
                source_id=source_id,
                source_name=_parse_optional_str(
                    entry, "source_name", default=source_id, source_id=source_id
                ),
                source_type=_parse_required_str(entry, "source_type", source_id),
                allowed_domains=_parse_allowed_domains(entry, source_id),
                trust_level=_parse_int(entry, "trust_level", default=0, source_id=source_id),
                license_type=_parse_required_str(entry, "license_type", source_id),
                official_api=_parse_bool(entry, "official_api", default=False, source_id=source_id),
                is_enabled=_parse_bool(entry, "is_enabled", default=True, source_id=source_id),
                default_priority=_parse_int(
                    entry, "default_priority", default=0, source_id=source_id
                ),
                rate_limit_policy=_parse_required_str(entry, "rate_limit_policy", source_id),
                auth_required=_parse_bool(
                    entry, "auth_required", default=False, source_id=source_id
                ),
                requires_local_client=_parse_bool(
                    entry, "requires_local_client", default=False, source_id=source_id
                ),
                expected_frequency=_parse_required_str(entry, "expected_frequency", source_id),
                expected_lag=_parse_required_str(entry, "expected_lag", source_id),
                timezone=_parse_required_str(entry, "timezone", source_id),
                fallback_allowed=_parse_bool(
                    entry, "fallback_allowed", default=False, source_id=source_id
                ),
                validation_only=_parse_bool(
                    entry, "validation_only", default=False, source_id=source_id
                ),
                notes=_parse_optional_str(entry, "notes", default="", source_id=source_id),
            )

        domain_roles_raw = raw.get("domain_roles", {})
        if not isinstance(domain_roles_raw, dict):
            raise InvalidRegistryError("domain_roles must be a mapping")

        self._domain_roles = {}
        for data_domain, roles in domain_roles_raw.items():
            if not isinstance(roles, dict):
                raise InvalidRegistryError(f"domain_roles.{data_domain} must be a mapping")
            for field in ("primary", "validation"):
                value = roles.get(field)
                if value is not None and str(value) in BANNED_ROLE_NAMES:
                    raise LegacyRoleError(
                        f"domain_roles.{data_domain}.{field}: banned role {value!r}"
                    )
            primary = roles.get("primary")
            if primary is None:
                raise InvalidRegistryError(f"domain_roles.{data_domain}.primary is required")
            primary_id = str(primary)
            validation_raw = roles.get("validation")
            if validation_raw is None:
                validation_id = None
            elif validation_raw == "null":
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.validation: string 'null' is not "
                    "allowed; use YAML null for no validation source"
                )
            else:
                validation_id = str(validation_raw)
            fallback_policy = str(roles.get("fallback_policy", ""))
            if fallback_policy not in VALID_FALLBACK_POLICIES:
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.fallback_policy invalid: {fallback_policy!r}"
                )
            self._domain_roles[data_domain] = DomainRoleBinding(
                primary_source_id=primary_id,
                validation_source_id=validation_id,
                fallback_policy=fallback_policy,
            )

        self._validate_domain_roles()

    def _validate_domain_roles(self) -> None:
        for data_domain, binding in self._domain_roles.items():
            primary_id = binding.primary_source_id
            if primary_id not in self._sources:
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.primary references unknown source {primary_id!r}"
                )
            primary = self._sources[primary_id]
            if not primary.is_enabled:
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.primary {primary_id!r} is disabled"
                )
            if primary.license_type == "unknown":
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.primary {primary_id!r} has license_type unknown"
                )
            if data_domain not in primary.allowed_domains:
                raise InvalidRegistryError(
                    f"domain_roles.{data_domain}.primary {primary_id!r} "
                    f"does not allow domain {data_domain!r}"
                )
            if binding.validation_source_id is not None:
                vid = binding.validation_source_id
                if vid not in self._sources:
                    raise InvalidRegistryError(
                        f"domain_roles.{data_domain}.validation references unknown source {vid!r}"
                    )
                validation = self._sources[vid]
                if not validation.is_enabled:
                    raise InvalidRegistryError(
                        f"domain_roles.{data_domain}.validation {vid!r} is disabled"
                    )
                if validation.license_type == "unknown":
                    raise InvalidRegistryError(
                        f"domain_roles.{data_domain}.validation {vid!r} has license_type unknown"
                    )
                if data_domain not in validation.allowed_domains:
                    raise InvalidRegistryError(
                        f"domain_roles.{data_domain}.validation {vid!r} "
                        f"does not allow domain {data_domain!r}"
                    )

    def get(self, source_id: str) -> SourceRecord:
        if source_id not in self._sources:
            raise SourceNotFoundError(source_id)
        return self._sources[source_id]

    def get_domain_roles(self, data_domain: str) -> DomainRoleBinding:
        if data_domain not in self._domain_roles:
            raise KeyError(data_domain)
        return self._domain_roles[data_domain]

    def assert_enabled(self, source_id: str) -> None:
        rec = self.get(source_id)
        if not rec.is_enabled:
            raise SourceDisabledError(f"source {source_id!r} is disabled")

    def assert_domain_allowed(self, source_id: str, data_domain: str) -> None:
        rec = self.get(source_id)
        if data_domain not in rec.allowed_domains:
            raise DomainNotAllowedError(
                f"source {source_id!r} does not allow domain {data_domain!r}"
            )

    def sync_to_db(self, con, *, tombstone_missing: bool = True) -> int:
        """Upsert all YAML sources into source_registry.

        When ``tombstone_missing`` is True, sources absent from YAML are marked
        ``is_enabled=false``.

        **Transaction policy (caller-owned, intentional):** This method does
        *not* open ``BEGIN``/``COMMIT``. Batch C Orchestrator and CLI entry
        points must wrap a full sync in an explicit transaction when atomic
        all-or-nothing semantics are required. See
        ``docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md``.
        """
        count = 0
        for rec in self._sources.values():
            row = _record_to_db_row(rec)
            con.execute(
                """
                INSERT OR REPLACE INTO source_registry (
                    source_id, source_name, source_type, allowed_domain,
                    trust_level, license_type, official_api, is_enabled,
                    default_priority, rate_limit_policy, auth_required,
                    requires_local_client, expected_frequency, expected_lag,
                    timezone, fallback_allowed, validation_only, notes, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                [
                    row["source_id"],
                    row["source_name"],
                    row["source_type"],
                    row["allowed_domain"],
                    row["trust_level"],
                    row["license_type"],
                    row["official_api"],
                    row["is_enabled"],
                    row["default_priority"],
                    row["rate_limit_policy"],
                    row["auth_required"],
                    row["requires_local_client"],
                    row["expected_frequency"],
                    row["expected_lag"],
                    row["timezone"],
                    row["fallback_allowed"],
                    row["validation_only"],
                    row["notes"],
                ],
            )
            count += 1
        if tombstone_missing and self._sources:
            ids = list(self._sources.keys())
            placeholders = ", ".join("?" * len(ids))
            con.execute(
                f"""
                UPDATE source_registry
                SET is_enabled = false, updated_at = CURRENT_TIMESTAMP
                WHERE source_id NOT IN ({placeholders})
                """,
                ids,
            )
        return count
