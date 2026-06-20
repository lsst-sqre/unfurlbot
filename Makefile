.PHONY: help
help:
	@echo "Make targets for unfurlbot"
	@echo "make init - Set up dev environment"
	@echo "make run - Start a local development instance"
	@echo "make update - Update pinned dependencies and run make init"
	@echo "make update-deps - Update pinned dependencies"
	@echo "make update-uv UV_VERSION=<version> - Update uv version in all config files"
	@echo "make lint - Lint the code with pre-commit"
	@echo "make typing - Run mypy"
	@echo "make test - Run the test suite (requires Docker for Kafka)"

.PHONY: init
init:
	uv sync --frozen --all-groups
	uv run --only-group=lint pre-commit install

.PHONY: run
run:
	uv run uvicorn unfurlbot.main:app --reload

.PHONY: update
update: update-deps init

.PHONY: update-deps
update-deps:
	uv lock --upgrade
	uv run --only-group=lint pre-commit autoupdate
	./scripts/update-uv-version.sh

.PHONY: update-uv
update-uv:
	./scripts/update-uv-version.sh $(UV_VERSION)

.PHONY: lint
lint:
	uv run --only-group=lint pre-commit run --all-files

.PHONY: typing
typing:
	uv run --only-group=nox nox -s typing

.PHONY: test
test:
	uv run --only-group=nox nox -s test
