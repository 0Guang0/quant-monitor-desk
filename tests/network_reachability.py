"""Vendor reachability probes for @pytest.mark.network tests."""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request

_SEC_PROBE_URL = "https://data.sec.gov/submissions/CIK0000320193.json"
_SEC_PROBE_TIMEOUT_S = 15


def sec_edgar_reachable(*, user_agent: str = "reachability-probe@example.com") -> bool:
    """Return True when SEC fair-access API responds (TLS + HTTP)."""
    request = urllib.request.Request(
        _SEC_PROBE_URL,
        headers={"User-Agent": user_agent, "Accept": "application/json"},
        method="GET",
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=_SEC_PROBE_TIMEOUT_S, context=context) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout, ssl.SSLError):
        return False
