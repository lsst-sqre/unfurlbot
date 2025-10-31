"""Nox configuration for unfurlbot."""

import nox

# Default sessions (run with `nox`)
nox.options.sessions = ["lint", "typing", "test"]
nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


@nox.session(uv_groups=["lint"])
def lint(session: nox.Session) -> None:
    """Run pre-commit linting."""
    session.run("pre-commit", "run", "--all-files")


@nox.session(uv_groups=["typing"])
def typing(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.run("mypy", "src/unfurlbot", "tests")


@nox.session(uv_groups=["dev"])
def test(session: nox.Session) -> None:
    """Run pytest tests (no Kafka integration yet)."""
    # Environment variables for tests
    env_vars = {
        "UNFURLBOT_LOG_LEVEL": "DEBUG",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "UNFURLBOT_SLACK_SIGNING": "1234",
        "UNFURLBOT_SLACK_TOKEN": "1234",
        "UNFURLBOT_SLACK_APP_ID": "1234",
        "UNFURLBOT_GAFAELFAWR_TOKEN": "gt-1234",
        "UNFURLBOT_ENVIRONMENT_URL": "https://example.com",
    }

    session.run(
        "pytest",
        "--cov=unfurlbot",
        "--cov-branch",
        "--cov-report=term",
        "--cov-report=html",
        *session.posargs,
        env=env_vars,
    )


@nox.session(uv_groups=["dev"])
def test_coverage(session: nox.Session) -> None:
    """Run tests and generate coverage report."""
    test(session)
    session.run("coverage", "report")


@nox.session(uv_groups=["docs"])
def docs(session: nox.Session) -> None:
    """Build documentation with Sphinx."""
    session.run(
        "sphinx-build",
        "-W",
        "--keep-going",
        "-n",
        "-T",
        "-b",
        "html",
        "docs",
        "docs/_build/html",
    )


@nox.session(uv_groups=["docs"])
def docs_linkcheck(session: nox.Session) -> None:
    """Check documentation links."""
    session.run(
        "sphinx-build",
        "-W",
        "--keep-going",
        "-n",
        "-T",
        "-b",
        "linkcheck",
        "docs",
        "docs/_build/linkcheck",
    )
