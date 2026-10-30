# Contributing

## Fresh checkout

```
make bootstrap
make test
```

`make bootstrap` is local-only: it builds the checkout snapshot and prints it.
It does not require a reachable status bridge, so an empty or unreachable
dashboard is **not** a reason to rerun it in a clean shell or to point it at
another machine. If it fails, read the error -- the common causes are a missing
`--project-dir` or a context directory outside the checkout.

Publishing is a separate, explicit step (`--publish-to`). Never add a default
endpoint, and never one that is plaintext HTTP to a non-loopback host.

## Pull requests

Keep changes focused, add a regression test for behavior changes, and include
the bootstrap and test results in the pull request description.

Tests must not open network sockets. `tests/test_transport.py` installs a guard
that fails any test that does; if you need to exercise a real endpoint, mark the
test and monkeypatch `transport.urlopen` explicitly.
