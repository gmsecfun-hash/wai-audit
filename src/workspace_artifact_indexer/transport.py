"""Transport for the local checkout status bridge.

Network publishing is strictly opt-in and loopback-only by policy:

* With no endpoint the snapshot stays on disk -- no socket is ever opened.
* An endpoint must be ``https://`` or point at loopback. Plaintext HTTP to a
  remote host is rejected -- a checkout snapshot carries directory structure
  that has no business crossing a network in the clear.
* Transport failures are reported, never fatal to the bootstrap itself.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MODE_LOCAL_ONLY = "local-only"
STATUS_LOCAL_ONLY = 0

_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", ""})


def validate_endpoint(url: str) -> str:
    """Return ``url`` when it is publishable, else raise ``ValueError``."""

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme in endpoint: {url!r}")

    host = (parsed.hostname or "").lower()
    if parsed.scheme == "http" and host not in _LOOPBACK_HOSTS:
        raise ValueError(
            f"refusing plaintext HTTP to non-loopback host {host!r}; "
            "use https:// or a loopback endpoint"
        )
    return url


def publish(
    snapshot: dict[str, object],
    endpoint: str | None = None,
    *,
    timeout: float = 3.0,
) -> dict[str, object]:
    """Publish one snapshot, or stay local when no endpoint is given."""

    if endpoint is None:
        return {
            "published": False,
            "mode": MODE_LOCAL_ONLY,
            "status": STATUS_LOCAL_ONLY,
            "bytes": 0,
        }

    url = validate_endpoint(endpoint)
    body = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
            return {
                "published": True,
                "mode": url,
                "status": response.status,
                "bytes": len(body),
            }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "published": False,
            "mode": url,
            "status": 0,
            "bytes": len(body),
            "error": str(exc),
        }
