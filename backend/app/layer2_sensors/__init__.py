"""Layer 2 cross-asset sensors (Round 3 Batch 3 — staged-only)."""

from backend.app.layer2_sensors.clean_observation_reader import (
    Layer2CleanObservationFallbackForbiddenError,
    Layer2CleanObservationReadError,
    Layer2CleanObservationReader,
)
from backend.app.layer2_sensors.double_count_guard import (
    DoubleCountGuardError,
    assert_model_eligible,
    quality_flags_for_registry_entry,
    validate_registry_double_count_rules,
)
from backend.app.layer2_sensors.futures_roll import (
    ContractLiquidity,
    FuturesRollError,
    FuturesRollHandler,
)
from backend.app.layer2_sensors.lineage import Layer2LineageBuilder, Layer2LineageError
from backend.app.layer2_sensors.models import (
    CrossAssetDailySnapshot,
    CrossAssetLoadResult,
    CrossAssetObservation,
    CrossAssetRegistryEntry,
    Layer2LineageEnvelope,
    MainContractRollEvent,
)
from backend.app.layer2_sensors.observation import CrossAssetObservationError
from backend.app.layer2_sensors.observation_writer import Layer2ObservationWriter
from backend.app.layer2_sensors.resource_guard_helper import ResourceGuardBlockedError
from backend.app.layer2_sensors.roll_writer import Layer2RollEventWriter
from backend.app.layer2_sensors.sensor_loader import (
    CLEAN_REPLAY_REGISTRY_FIXTURE,
    CrossAssetRegistryLoader,
    CrossAssetRegistryLoadError,
    CrossAssetRegistryWriter,
)
from backend.app.layer2_sensors.snapshot_builder import (
    CrossAssetSnapshotBuilder,
    Layer2SnapshotWriter,
)

__all__ = [
    "CLEAN_REPLAY_REGISTRY_FIXTURE",
    "ContractLiquidity",
    "CrossAssetDailySnapshot",
    "CrossAssetLoadResult",
    "CrossAssetObservation",
    "CrossAssetObservationError",
    "CrossAssetRegistryEntry",
    "CrossAssetRegistryLoadError",
    "CrossAssetRegistryLoader",
    "CrossAssetRegistryWriter",
    "CrossAssetSnapshotBuilder",
    "DoubleCountGuardError",
    "FuturesRollError",
    "FuturesRollHandler",
    "Layer2CleanObservationFallbackForbiddenError",
    "Layer2CleanObservationReadError",
    "Layer2CleanObservationReader",
    "Layer2LineageBuilder",
    "Layer2LineageEnvelope",
    "Layer2LineageError",
    "Layer2ObservationWriter",
    "Layer2RollEventWriter",
    "Layer2SnapshotWriter",
    "MainContractRollEvent",
    "ResourceGuardBlockedError",
    "assert_model_eligible",
    "quality_flags_for_registry_entry",
    "validate_registry_double_count_rules",
]
