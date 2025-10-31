# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unfurlbot is a Squarebot backend that provides link unfurling for tokens like Jira issue keys in Slack messages. It's deployed with Phalanx to Rubin Observatory's Roundtable cluster.

**Tech Stack:**
- FastAPI for HTTP endpoints
- FastStream for Kafka message consumption
- Safir library for Rubin Observatory infrastructure patterns
- Redis for caching/deduplication
- Pydantic for configuration and validation

## Development Commands

### Initial Setup
```bash
make init
```
Sets up the development environment by installing dependencies with uv and configuring pre-commit hooks.

### Running the Application
```bash
make run
# Or directly:
uv run uvicorn unfurlbot.main:app --reload
```
Starts the development server with auto-reload enabled via uvicorn.

### Testing

**Note:** Always run nox with `uv run --only-group=nox nox` to ensure nox uses the correct dependency group.

```bash
# Run all default sessions (lint, typing, test)
uv run --only-group=nox nox

# Run all tests with coverage
uv run --only-group=nox nox -s test

# Run specific test file
uv run pytest tests/services/jiraunfurler_test.py

# Run with specific markers or keywords
uv run pytest -k "test_name"

# View coverage report
uv run --only-group=nox nox -s test-coverage
```

### Type Checking
```bash
uv run --only-group=nox nox -s typing
```
Runs mypy on both src and tests directories.

### Linting
```bash
uv run --only-group=nox nox -s lint
# Or run pre-commit directly:
pre-commit run --all-files
```
Runs Ruff for formatting and linting via pre-commit.

### Dependency Management
```bash
# Update all dependencies
make update

# Update only dependency pins
make update-deps
```
Uses uv to manage dependencies via uv.lock. Dependencies are defined in pyproject.toml using PEP 735 dependency groups.

## Architecture

### Request Flow

1. **Kafka Message Ingestion**: Kafka messages from Squarebot arrive on various topics (message.channels, message.groups, message.im, message.mpim)
2. **Consumer Processing**: The `handle_slack_message` function in `handlers/kafka.py` receives messages
3. **Context Creation**: `ConsumerContextDependency` creates a `ConsumerContext` with logger and factory for each message
4. **Unfurling Pipeline**: The `SlackUnfurlService` orchestrates domain-specific unfurlers (currently just Jira)
5. **Token Detection**: Domain unfurlers extract tokens from message text (e.g., "DM-12345")
6. **Deduplication**: Redis-backed `SlackUnfurlEventStore` prevents duplicate unfurls
7. **Message Posting**: Unfurlers post Block Kit messages to Slack via the chat.postMessage API

### Key Components

**Factory Pattern** (`factory.py`):
- `ProcessContext`: Holds singleton resources (HTTP client, Redis) shared across all requests
- `Factory`: Creates service instances with proper dependency injection and logger binding

**Consumer Context** (`dependencies/consumercontext.py`):
- Provides per-message context to Kafka consumers
- Binds Kafka metadata (topic, partition, offset) to structured logger
- Manages Factory lifecycle with logger rebinding

**Domain Unfurlers** (`services/`):
- `DomainUnfurler`: Abstract base class defining the unfurler contract
  - `extract_tokens()`: Extract domain tokens from Slack message text
  - `create_slack_message()`: Generate Block Kit message for a token
  - Built-in debouncing and staleness checking
- `JiraUnfurler`: Detects Jira issue keys, fetches issue data, formats as Slack blocks
- `SlackUnfurlService`: Coordinates multiple domain unfurlers

**Storage Layers** (`storage/`):
- `JiraIssueClient`: Fetches issue data from Jira Data Proxy via Gafaelfawr authentication
- `SlackUnfurlEventStore`: Redis-based deduplication (key: channel+thread+token, TTL: slack_debounce_time)
- `SlackBlockKitMessage`: Type-safe Slack Block Kit message builder

### Configuration

All configuration is environment-based via Pydantic settings with `UNFURLBOT_` prefix. See `config.py` for the full schema. Key settings:

- `UNFURLBOT_ENVIRONMENT_URL`: Base URL for the environment
- `UNFURLBOT_GAFAELFAWR_TOKEN`: Token for accessing Jira Data Proxy
- `UNFURLBOT_SLACK_TOKEN`: Slack bot token
- `UNFURLBOT_JIRA_PROJECTS`: Comma-separated Jira project keys to recognize (e.g., "DM,RFC")
- `UNFURLBOT_SLACK_DEBOUNCE_TIME`: Seconds before same token can be unfurled again (default: 300)
- `UNFURLBOT_SLACK_TRIGGER_MESSAGE_TTL`: Max age of trigger message to process (default: 60)

### Testing Patterns

Tests use pytest with async support via pytest-asyncio. The `conftest.py` provides:
- `app` fixture: FastAPI app with lifespan management
- `client` fixture: HTTPX AsyncClient for API testing

Mock external services (Slack API, Jira Data Proxy) in tests. The `ConsumerContextDependency` can be overridden for testing specific scenarios.

## Adding a New Domain Unfurler

1. Create a new class inheriting from `DomainUnfurler` in `services/`
2. Set `unfurler_domain` class variable to a unique identifier
3. Implement `extract_tokens()` to detect your tokens in Slack message text
4. Implement `create_slack_message()` to format Block Kit messages
5. Register the unfurler in `Factory.get_slack_unfurler()`
6. Add tests in `tests/services/`

## Code Style

- Uses Ruff for formatting and linting (configuration in `ruff-shared.toml`)
- Strict mypy settings: all functions must have type annotations
- docstrings follow Google/NumPy style (see existing code for examples)
- Use structured logging with bound loggers from structlog

## Dependencies

Dependencies are defined in `pyproject.toml` using PEP 735 dependency groups:
- `dependencies`: Runtime dependencies (FastAPI, Safir, FastStream, etc.)
- `dev`: Development and testing dependencies (pytest, httpx, etc.)
- `docs`: Documentation dependencies (Sphinx, documenteer, etc.)
- `lint`: Linting dependencies (ruff, pre-commit, etc.)
- `nox`: Nox testing framework dependencies
- `typing`: Type checking dependencies (mypy, type stubs, etc.)

After editing dependencies in `pyproject.toml`, run `make update-deps` to update the `uv.lock` file.
