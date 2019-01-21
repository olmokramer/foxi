PKG = foxi

PIP = pip3
PYTHON = python3
VIRTUALENV = virtualenv3 --python=$(PYTHON)

BLACK_ARGS += --py36 --line-length 79 --skip-string-normalization $(PKG)
ISORT_ARGS += --recursive $(PKG)
MYPY_ARGS += --package $(PKG)
PYLINT_ARGS += --rcfile=setup.cfg $(PKG)

# Prefix a line with $(VENV) to run it in a virtualenv.
VENV = source .venv/bin/activate;

all: run

.venv:
	$(VIRTUALENV) .venv

# Install deps only if requirements.txt has changed.
.PHONY: install-deps
install-deps: .venv/_previous_update
.venv/_previous_update: requirements.txt | .venv
	$(VENV) $(PIP) install $(PIP_ARGS) -r $<
	date > $@

.PHONY: run
run: install-deps
	$(VENV) $(PYTHON) -m $(PKG) $(ARGS)

.PHONY: debug
debug: ARGS += --debug
debug: run

.PHONY: test
test: TEST_FILE ?= $(wildcard ./tests/*)
test: ARGS += --test $(TEST_FILE)
test: run

.PHONY: python
python: install-deps
	$(VENV) $(PYTHON)

.PHONY: check
check: check-types check-lint check-format

.PHONY: check-types
check-types: install-deps
	$(VENV) mypy $(MYPY_ARGS)

.PHONY: check-lint
check-lint: install-deps
	$(VENV) pylint $(PYLINT_ARGS)

.PHONY: check-format
check-format: install-deps
	$(VENV) isort --check-only --diff $(ISORT_ARGS)
	$(VENV) black --check --diff $(BLACK_ARGS)

.PHONY: format
format: install-deps
	$(VENV) isort $(ISORT_ARGS)
	$(VENV) black $(BLACK_ARGS)

.PHONY: install
install:
	$(PIP) install --user $(PIP_ARGS) .

.PHONY: uninstall
uninstall:
	$(PIP) uninstall $(PIP_ARGS) $(PKG)
