"""Layer1 execute-evidence tooling shim (L1-06 — canonical: ops.layer1_evidence.inventory)."""

from backend.app.ops.layer1_evidence.inventory import *  # noqa: F403
from backend.app.ops.layer1_evidence import inventory as _inventory

_relative_to_project = _inventory._relative_to_project
