.PHONY: help
help:
	@echo "Make targets for unfurlbot"
	@echo "make init - Set up dev environment"
	@echo "make run - Start a local development instance"
	@echo "make update - Update pinned dependencies and run make init"
	@echo "make update-deps - Update pinned dependencies"
	@echo "make update-uv UV_VERSION=<version> - Update UV version in all config files"

.PHONY: init
init:
	uv sync --frozen --all-groups
	uv run --group=lint pre-commit install

.PHONY: run
run:
	uv run uvicorn unfurlbot.main:app --reload

.PHONY: update
update: update-deps init

.PHONY: update-deps
update-deps:
	uv lock --upgrade
	uv run --group=lint pre-commit autoupdate

.PHONY: update-uv
update-uv:
	./scripts/update-uv-version.sh $(UV_VERSION)
