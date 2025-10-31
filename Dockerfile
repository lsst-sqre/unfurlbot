# This Dockerfile has three stages:
#
# base-image
#   Updates the base Python image with security patches and common system
#   packages. This image becomes the base of all other images.
# install-image
#   Installs third-party dependencies and the application into a virtual
#   environment using uv sync. This virtual environment is ideal for copying
#   across build stages.
# runtime-image
#   - Copies the virtual environment into place.
#   - Runs a non-root user.
#   - Sets up the entrypoint and port.

FROM python:3.13.7-slim-bookworm AS base-image

# Update system packages
COPY scripts/install-base-packages.sh .
RUN ./install-base-packages.sh && rm ./install-base-packages.sh

FROM base-image AS install-image

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.8.19 /uv /bin/uv

# Install system packages only needed for building dependencies.
COPY scripts/install-dependency-packages.sh .
RUN ./install-dependency-packages.sh

# Create working directory and set up virtual environment
WORKDIR /app
ENV UV_LINK_MODE=copy

# Install dependencies with cache and bind mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-default-groups --compile-bytecode --no-install-project

# Install the application itself
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps --compile-bytecode .

FROM base-image AS runtime-image

# Create a non-root user
RUN useradd --create-home appuser

# Copy the application and virtual environment
COPY --from=install-image /app /app

# Make sure we use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Switch to the non-root user.
USER appuser

# Set working directory
WORKDIR /app

# Expose the port.
EXPOSE 8080

# Run the application.
CMD ["uvicorn", "unfurlbot.main:app", "--host", "0.0.0.0", "--port", "8080"]
