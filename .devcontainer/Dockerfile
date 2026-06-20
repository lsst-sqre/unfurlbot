# Dev container image for unfurlbot.
#
# A minimal Python 3.14 base with uv for dependency management. Kept COPY-free
# (no repo files baked in) so the human build and stoker's cloned-volume
# sandbox build are identical. System tooling beyond this (firewall, gh, commit
# signing, the agent harness) is layered separately by the stoker-sandbox
# devcontainer Feature and is intentionally absent here.

FROM mcr.microsoft.com/devcontainers/python:1-3.14-bookworm

# Install uv (pinned to match CI and the production Dockerfile).
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

# Copy mode avoids hardlink warnings when the uv cache and the project venv
# live on different filesystems (e.g. a mounted workspace volume).
ENV UV_LINK_MODE=copy
