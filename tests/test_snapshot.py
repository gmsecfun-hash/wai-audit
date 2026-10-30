from pathlib import Path

import pytest

from workspace_artifact_indexer.snapshot import (
    SCHEMA,
    build_snapshot,
    resolve_context_dir,
)


def test_snapshot_contains_direct_items_only(tmp_path: Path) -> None:
    (tmp_path / "report.csv").write_text("sample", encoding="utf-8")
    (tmp_path / "notes.md").write_text("sample", encoding="utf-8")

    snapshot = build_snapshot(Path("checkout"), tmp_path, allow_external=True)

    assert snapshot["schema"] == SCHEMA
    assert snapshot["items"] == ["notes.md", "report.csv"]
    assert snapshot["count"] == 2


def test_context_directory_can_be_configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKSPACE_CONTEXT_DIR", str(tmp_path))

    assert resolve_context_dir() == tmp_path.resolve()


def test_missing_context_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        build_snapshot(Path("checkout"), tmp_path / "missing", allow_external=True)


# --- regression tests for the 0.4.0 hardening -------------------------------


def test_default_context_is_the_checkout_not_the_desktop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The context root must never silently become a personal directory."""

    monkeypatch.delenv("WORKSPACE_CONTEXT_DIR", raising=False)

    assert resolve_context_dir(tmp_path) == tmp_path.resolve()
    assert resolve_context_dir(tmp_path) != (Path.home() / "Desktop").resolve()


def test_desktop_is_refused_even_when_named_explicitly() -> None:
    with pytest.raises(PermissionError):
        build_snapshot(Path("checkout"), Path.home() / "Desktop", allow_external=True)


def test_home_is_refused_even_when_named_explicitly() -> None:
    with pytest.raises(PermissionError):
        build_snapshot(Path("checkout"), Path.home(), allow_external=True)


def test_external_context_requires_opt_in(tmp_path: Path) -> None:
    project = tmp_path / "checkout"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("x", encoding="utf-8")

    with pytest.raises(PermissionError):
        build_snapshot(project, outside)

    allowed = build_snapshot(project, outside, allow_external=True)
    assert allowed["items"] == ["secret.txt"]


def test_oversized_context_is_rejected(tmp_path: Path) -> None:
    for index in range(10):
        (tmp_path / f"f{index}").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        build_snapshot(Path("checkout"), tmp_path, allow_external=True, max_items=5)
