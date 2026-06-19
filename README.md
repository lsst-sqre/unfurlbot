# Unfurlbot

Unfurlbot is a [Squarebot](https://squarebot.lsst.io) backend that provides links to tokens like Jira issue keys in Slack.

Unfurlbot is developed with [FastAPI](https://fastapi.tiangolo.com), [FastStream](https://faststream.airt.ai/latest/), and [Safir](https://safir.lsst.io) and is deployed with [Phalanx](https://phalanx.lsst.io) to Rubin Observatory's Roundtable cluster for internal developer services.

## Development

Unfurlbot targets **Python 3.14** and uses [uv](https://docs.astral.sh/uv/) (pinned to `0.11.21`) for dependency management, with a single committed `uv.lock`.

### Environment set up

```bash
make init
```

`make init` runs `uv sync --frozen --all-groups` from the committed `uv.lock` and installs the pre-commit hooks. A dev container is also provided under `.devcontainer/` (Python 3.14 + uv).

### Testing and linting

```bash
make lint     # pre-commit (Ruff) on all files
make typing   # mypy via nox
make test     # pytest via nox (stands up Kafka with testcontainers; needs Docker)
```

These delegate to nox; you can also run the sessions directly, e.g. `uv run --only-group=nox nox -s test`. The `test` session stands up a Kafka broker via [testcontainers](https://testcontainers-python.readthedocs.io/), so Docker must be available. Run `uv run --only-group=nox nox` to run lint, typing, and test together, or `uv run --only-group=nox nox -l` to list all sessions.

### Running the app

```bash
make run
```

### Updating dependencies

```bash
make update-deps
```

`make update-deps` regenerates `uv.lock`, runs `pre-commit autoupdate`, and refreshes the pinned uv version (default `0.11.21`) across the `Dockerfile`, `.devcontainer/Dockerfile`, and the CI workflows via `./scripts/update-uv-version.sh`. Use `make update` to do that and re-run `make init`.
