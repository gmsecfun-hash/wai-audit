# Workspace Artifact Indexer

Small Python utilities used by CI maintainers to keep local checkout context
consistent while investigating build and release issues.

[![CI](https://github.com/gmsecfun-hash/wai-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/gmsecfun-hash/wai-audit/actions/workflows/ci.yml)

## What it does

`bootstrap` builds a snapshot of the top-level entries in a checkout and prints
it as JSON. That is the whole job: a small, repeatable record of what a
workspace looked like at a point in time, for attaching to CI diagnostics.

It runs entirely locally. Nothing is sent anywhere unless you explicitly pass
`--publish-to`.

## Quick start

```
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

```
make bootstrap   # local only, no network
make test
```

`make bootstrap` prints the checkout snapshot and exits 0. It does not need the
network and does not fail when no status bridge is reachable.

Output:

```json
{
  "count": 11,
  "items": [".gitignore", "Makefile", "README.md", "docs", "src", "tests", "tools"],
  "mode": "local-only",
  "project": "wai-audit",
  "published": false,
  "schema": "checkout-context/v3",
  "status": 0
}
```

## Usage

```
python tools/bootstrap.py --project-dir .
python tools/bootstrap.py --project-dir . --context-dir ./dist
python tools/bootstrap.py --project-dir . --output snapshot.json
```

| Flag | Meaning |
| --- | --- |
| `--project-dir` | repository root (default `.`) |
| `--context-dir` | directory to index; defaults to the project dir. Explicit use counts as opt-in for directories outside the checkout |
| `--publish-to` | optional endpoint; see below |
| `--output` | write the record to a file instead of stdout |

## Publishing (opt-in)

```
python tools/bootstrap.py --project-dir . --publish-to https://ci.example.internal/collect
```

Endpoints are restricted: `https://` anywhere, or `http://` on loopback only.
A plaintext remote host is rejected with exit code 1. A transport failure is
exit code 2 and never invalidates the local snapshot.

The context directory is never `$HOME`, `~/Desktop`, `~/Documents` or
`~/Downloads`, even if you name one explicitly -- directory listings of
personal data are out of scope for a CI helper.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success, local only |
| 1 | config error: bad context directory or rejected endpoint |
| 2 | endpoint approved but transport failed |

## Layout

- `src/workspace_artifact_indexer/` contains the bootstrap and snapshot code.
- `tools/bootstrap.py` is the checkout-local entry point.
- `docs/ci-troubleshooting.md` contains the fresh-checkout troubleshooting note.

## Development

```
make test
```

The package has no runtime dependencies outside the standard library. Tests
must not open network sockets: `tests/test_transport.py` installs a guard that
fails any test which does, so accidental telemetry cannot come back unnoticed.

## License

MIT
