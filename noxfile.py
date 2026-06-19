"""Nox configuration for unfurlbot."""

import logging
import os
from pathlib import Path

import nox
import nox_uv

# Default sessions (run with `nox`)
nox.options.sessions = ["lint", "typing", "test"]
nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


def _setup_testcontainers_logging() -> None:
    """Suppress overly-verbose testcontainers logging."""
    logging.getLogger("testcontainers").setLevel(logging.ERROR)
    logging.getLogger("docker").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)


def _setup_testcontainers_env() -> None:
    """Set up testcontainers environment variables.

    This handles macOS/Colima Docker host configuration.
    """
    # Check if running on macOS with Colima
    if Path.home().joinpath(".colima/docker.sock").exists():
        os.environ["DOCKER_HOST"] = "unix://" + str(
            Path.home().joinpath(".colima/docker.sock")
        )


def _make_env_vars(extra: dict[str, str]) -> dict[str, str]:
    """Create environment variables for tests.

    Parameters
    ----------
    extra
        Additional environment variables to include.

    Returns
    -------
    dict
        Complete set of environment variables for tests.
    """
    env_vars = {
        "UNFURLBOT_LOG_LEVEL": "DEBUG",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "UNFURLBOT_SLACK_SIGNING": "1234",
        "UNFURLBOT_SLACK_TOKEN": "1234",
        "UNFURLBOT_SLACK_APP_ID": "1234",
        "UNFURLBOT_GAFAELFAWR_TOKEN": "gt-1234",
        "UNFURLBOT_ENVIRONMENT_URL": "https://example.com",
    }
    env_vars.update(extra)
    return env_vars


@nox_uv.session(uv_groups=["lint"])
def lint(session: nox.Session) -> None:
    """Run pre-commit linting."""
    session.run("pre-commit", "run", "--all-files")


@nox_uv.session(uv_groups=["typing"])
def typing(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.run("mypy", "src/unfurlbot", "tests")


@nox_uv.session(uv_groups=["dev"])
def test(session: nox.Session) -> None:
    """Run pytest tests with Kafka testcontainer."""
    _setup_testcontainers_logging()
    _setup_testcontainers_env()

    from testcontainers.kafka import KafkaContainer  # noqa: PLC0415

    with KafkaContainer().with_kraft() as kafka:
        env_vars = _make_env_vars(
            {
                "KAFKA_BOOTSTRAP_SERVERS": kafka.get_bootstrap_server(),
            }
        )

        session.run(
            "pytest",
            "--cov=unfurlbot",
            "--cov-branch",
            "--cov-report=term",
            "--cov-report=html",
            *session.posargs,
            env=env_vars,
        )


@nox_uv.session(name="test-coverage", uv_groups=["dev", "nox"])
def test_coverage(session: nox.Session) -> None:
    """Run tests and generate coverage report."""
    test(session)
    session.run("coverage", "report")


@nox_uv.session(uv_groups=["docs"])
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


@nox_uv.session(name="docs-linkcheck", uv_groups=["docs"])
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
