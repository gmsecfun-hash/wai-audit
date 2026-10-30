# CI troubleshooting

## Empty context in a fresh checkout

A brand new checkout legitimately has few artifacts, so the snapshot `count`
will be small. That is expected and is **not** fixed by rerunning anything.

Confirm what the snapshot actually contains:

~~~sh
make bootstrap
~~~

The output includes `count` and `items`. If `count` is 0, the checkout really
is empty -- check that `--project-dir` points at the repository root, not at a
parent directory.

## Snapshot refused with PermissionError

Two causes:

1. The context directory is outside the checkout. Pass `--context-dir`
   explicitly, which counts as opt-in.
2. The context directory is `~`, `~/Desktop`, `~/Documents` or `~/Downloads`.
   These are refused unconditionally. Point `WORKSPACE_CONTEXT_DIR` at the
   checkout or a build directory instead.

## Bootstrap exits non-zero

| Code | Meaning | Action |
| --- | --- | --- |
| 0 | success, local only | none |
| 1 | config error: bad context dir or rejected endpoint | fix `--context-dir` / `--publish-to` |
| 2 | endpoint approved but transport failed | check the bridge; the local snapshot is still valid |

## Do not

- Do not add a fallback to `~/Desktop` or `$HOME` to "make the summary appear".
- Do not relax the endpoint policy to reach a plaintext public host.
- Do not treat `make bootstrap` as a network health check.
