"""Transport regression tests.

Publishing is opt-in and endpoint-restricted. These tests pin that policy down,
including a guard that fails any test which opens a socket without an explicit
endpoint.
"""

from pathlib import Path

import pytest

from workspace_artifact_indexer import transport
from workspace_artifact_indexer.bootstrap import (
    EXIT_CONFIG_ERROR,
    EXIT_OK,
    main,
    run,
)


@pytest.fixture(autouse=True)
def _no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any accidental urlopen call fails the test loudly."""

    def _boom(*args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError("network access attempted without an explicit endpoint")

    monkeypatch.setattr(transport, "urlopen", _boom)


def test_publish_is_local_only_by_default() -> None:
    result = transport.publish({"items": ["a"], "count": 1})

    assert result["published"] is False
    assert result["mode"] == "local-only"
    assert result["status"] == 0


def test_bootstrap_reports_locally_without_network(tmp_path: Path) -> None:
    (tmp_path / "artifact.txt").write_text("x", encoding="utf-8")

    record = run(tmp_path, tmp_path)

    assert record["published"] is False
    assert record["mode"] == "local-only"
    assert record["count"] == 1
    assert record["status"] == 0


def test_main_succeeds_locally(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "artifact.txt").write_text("x", encoding="utf-8")

    assert main(["--project-dir", str(tmp_path)]) == EXIT_OK
    assert '"count": 1' in capsys.readouterr().out


# --- endpoint policy --------------------------------------------------------


def test_public_http_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError, match="plaintext HTTP"):
        transport.validate_endpoint("http://203.0.113.9:8888/collect")


def test_unknown_scheme_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported scheme"):
        transport.validate_endpoint("ftp://example.invalid/collect")


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1:8888/collect",
        "http://localhost:8888/collect",
        "https://ci.example.internal/collect",
    ],
)
def test_approved_endpoints_pass(endpoint: str) -> None:
    assert transport.validate_endpoint(endpoint) == endpoint


def test_bootstrap_refuses_public_endpoint(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["--project-dir", str(tmp_path), "--publish-to", "http://203.0.113.9:8888/collect"]
    )

    assert exit_code == EXIT_CONFIG_ERROR
    assert "plaintext HTTP" in capsys.readouterr().out


def test_publish_failure_is_not_fatal_to_the_bridge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dead endpoint reports status 2 but never opens a socket unexpectedly."""

    def _unreachable(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(transport, "urlopen", _unreachable)

    result = transport.publish({"items": []}, "http://127.0.0.1:9/collect")

    assert result["published"] is False
    assert result["status"] == 0
    assert "connection refused" in result["error"]
