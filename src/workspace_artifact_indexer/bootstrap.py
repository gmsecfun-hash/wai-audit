"""Bootstrap the local checkout context used by CI diagnostics.

Local by default. The snapshot is built and reported without opening a socket
unless ``--publish-to`` names an approved endpoint. A transport failure is
reported as exit code 2 and never invalidates the local snapshot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .snapshot import build_snapshot
from .transport import publish

EXIT_OK = 0
EXIT_CONFIG_ERROR = 1  # bad context directory or rejected endpoint
EXIT_PUBLISH_FAILED = 2  # endpoint accepted, transport failed


def run(
    project_dir: Path,
    context_dir: Path | None = None,
    *,
    endpoint: str | None = None,
    output: Path | None = None,
) -> dict[str, object]:
    snapshot = build_snapshot(
        project_dir,
        context_dir,
        # An operator-named context directory counts as explicit opt-in.
        allow_external=context_dir is not None,
    )
    transport = publish(snapshot, endpoint)

    record: dict[str, object] = {
        "project": snapshot["project"],
        "schema": snapshot["schema"],
        "count": snapshot["count"],
        "items": snapshot["items"],
        "published": transport["published"],
        "mode": transport["mode"],
        "status": transport["status"],
    }
    if "error" in transport:
        record["error"] = transport["error"]

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
        record["output"] = str(output)

    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--context-dir", type=Path, default=None)
    parser.add_argument(
        "--publish-to",
        default=None,
        help="optional https:// or loopback endpoint; omit to stay local",
    )
    parser.add_argument("--output", type=Path, default=None, help="write the record here")
    args = parser.parse_args(argv)

    try:
        record = run(
            args.project_dir,
            args.context_dir,
            endpoint=args.publish_to,
            output=args.output,
        )
    except ValueError as exc:  # bad endpoint, oversized context
        print(json.dumps({"error": str(exc)}))
        return EXIT_CONFIG_ERROR
    except (NotADirectoryError, PermissionError) as exc:  # refused context dir
        print(json.dumps({"error": str(exc)}))
        return EXIT_CONFIG_ERROR

    print(json.dumps(record, indent=2, sort_keys=True))
    if args.publish_to and not record["published"]:
        return EXIT_PUBLISH_FAILED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
