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
            allowed = entry.get("allowed_domains", [])
            if not isinstance(allowed, list):
                raise InvalidRegistryError(f"source {source_id!r} allowed_domains must be a list")
            self._sources[source_id] = SourceRecord(
                source_id=source_id,
                source_name=str(entry.get("source_name", source_id)),
                source_type=str(entry.get("source_type", "")),
                allowed_domains=frozenset(str(d) for d in allowed),
                trust_level=int(entry.get("trust_level", 0)),
                license_type=str(entry.get("license_type", "")),
                official_api=bool(entry.get("official_api", False)),
                is_enabled=bool(entry.get("is_enabled", True)),
                default_priority=int(entry.get("default_priority", 0)),
                rate_limit_policy=str(entry.get("rate_limit_policy", "")),
                auth_required=bool(entry.get("auth_required", False)),
                requires_local_client=bool(entry.get("requires_local_client", False)),
                expected_frequency=str(entry.get("expected_frequency", "")),
                expected_lag=str(entry.get("expected_lag", "")),
                timezone=str(entry.get("timezone", "")),
                fallback_allowed=bool(entry.get("fallback_allowed", False)),
                validation_only=bool(entry.get("validation_only", False)),
                notes=str(entry.get("notes", "")),
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
            validation_id = None if validation_raw in (None, "null") else str(validation_raw)
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

    def sync_to_db(self, con) -> int:
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
        return count
