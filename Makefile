PYTHON ?= python3
VENV := .venv
PY := $(VENV)/bin/python

# `bootstrap` is local-only and never requires the network; `test` uses the
# same interpreter as the install so results are reproducible.
.PHONY: all venv bootstrap test check clean

all: check

$(PY):
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -e ".[dev]"

venv: $(PY)

bootstrap: venv
	$(PY) tools/bootstrap.py --project-dir .

test: venv
	$(PY) -m pytest

check: bootstrap test

# Opt-in publishing. Refuses non-https/non-loopback endpoints.
publish: venv
	$(PY) tools/bootstrap.py --project-dir . --publish-to "$$(WORKSPACE_PUBLISH_URL)"

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
