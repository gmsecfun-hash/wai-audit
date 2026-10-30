"""Build a compact snapshot of the *checkout* context.

Scope rules:

* The context directory defaults to the checkout itself. There is no fallback
  to ``$HOME`` or ``~/Desktop`` -- a directory listing of personal data is not
  a CI concern.
* ``~/Desktop``, ``~/Documents``, ``~/Downloads`` and ``$HOME`` are refused
  even when named explicitly.
* A context directory outside the checkout needs ``allow_external=True``.
"""

from __future__ import annotations

import os
from pathlib import Path

SCHEMA = "checkout-context/v3"

#: Directories that are never a valid context root, regardless of opt-in.
FORBIDDEN_ROOTS = ("Desktop", "Documents", "Downloads")

DEFAULT_MAX_ITEMS = 500


def _personal_roots() -> set[Path]:
    home = Path.home().resolve()
    return {home, *(home / name for name in FORBIDDEN_ROOTS)}


def resolve_context_dir(project_dir: Path | None = None) -> Path:
    """Resolve the context directory.

    Resolution order:

    1. ``WORKSPACE_CONTEXT_DIR`` when the operator configured it explicitly.
    2. The checkout directory itself.

    There is deliberately no home/Desktop fallback: listing a personal
    directory is not a CI concern.
    """

    configured = os.environ.get("WORKSPACE_CONTEXT_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (project_dir or Path.cwd()).expanduser().resolve()


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def _direct_names(context_dir: Path) -> list[str]:
    context_dir = context_dir.expanduser().resolve()
    if not context_dir.is_dir():
        raise NotADirectoryError(context_dir)
    return sorted(item.name for item in context_dir.iterdir())


def build_snapshot(
    project_dir: Path,
    context_dir: Path | None = None,
    *,
    allow_external: bool = False,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, object]:
    """Create the small checkout record consumed by the status bridge.

    ``allow_external`` must be passed when the context directory lives outside
    the checkout; personal directories are refused either way.
    """

    project_dir = project_dir.expanduser().resolve()
    resolved_context = (context_dir or resolve_context_dir(project_dir)).expanduser().resolve()

    # Refused on name, before existence: a runner with no ~/Desktop must still
    # get PermissionError rather than a misleading NotADirectoryError.
    if resolved_context in _personal_roots():
        raise PermissionError(
            f"refusing to index personal directory: {resolved_context}"
        )

    if not resolved_context.is_dir():
        raise NotADirectoryError(resolved_context)

    if not allow_external and not _is_within(resolved_context, project_dir):
        raise PermissionError(
            f"context directory {resolved_context} is outside the checkout "
            f"{project_dir}; pass allow_external=True to index it explicitly"
        )

    names = _direct_names(resolved_context)
    if len(names) > max_items:
        raise ValueError(
            f"context directory holds {len(names)} entries, above max_items={max_items}"
        )

    return {
        "schema": SCHEMA,
        "project": project_dir.name,
        "items": names,
        "count": len(names),
    }
