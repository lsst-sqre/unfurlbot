#!/bin/bash
# Update uv version references across all configuration files.
#
# Usage: update-uv-version.sh [uv-version]
#
# With no argument the script uses the default version below; this is what
# `make update-deps` invokes so the pin stays in sync with the rest of the
# tooling refresh. Pass an explicit version (or `make update-uv
# UV_VERSION=<version>`) to bump to a specific release.

# Bash "strict mode", to help catch problems and bugs in the shell script.
# See http://redsymbol.net/articles/unofficial-bash-strict-mode/ for details.
set -euo pipefail

# Default/example uv version. Keep this in sync with the pin used across the
# Dockerfile, CI workflows, and the dev container.
DEFAULT_UV_VERSION="0.11.21"

UV_VERSION="${1:-$DEFAULT_UV_VERSION}"

echo "Updating uv version to $UV_VERSION"

# Update the production Dockerfile.
sed -i.bak "s|ghcr.io/astral-sh/uv:[0-9][0-9.]*|ghcr.io/astral-sh/uv:$UV_VERSION|g" Dockerfile
rm Dockerfile.bak

# Update the dev container Dockerfile (kept COPY-free of repo files, but it
# still pins the same uv release as CI and production).
sed -i.bak "s|ghcr.io/astral-sh/uv:[0-9][0-9.]*|ghcr.io/astral-sh/uv:$UV_VERSION|g" .devcontainer/Dockerfile
rm .devcontainer/Dockerfile.bak

# Update GitHub Actions workflows.
find .github/workflows -name "*.yaml" -exec sed -i.bak "s/UV_VERSION: \"[0-9][0-9.]*\"/UV_VERSION: \"$UV_VERSION\"/g" {} \;
find .github/workflows -name "*.yaml.bak" -delete

echo "uv version updated to $UV_VERSION in:"
echo "  - Dockerfile"
echo "  - .devcontainer/Dockerfile"
echo "  - .github/workflows/*.yaml"
echo ""
echo "Done!"
