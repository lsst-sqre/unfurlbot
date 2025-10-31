#!/bin/bash
# Update UV version across all configuration files

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <uv-version>"
    echo "Example: $0 0.8.19"
    exit 1
fi

UV_VERSION="$1"

echo "Updating UV version to $UV_VERSION"

# Update Dockerfile
sed -i.bak "s|ghcr.io/astral-sh/uv:[0-9.]*|ghcr.io/astral-sh/uv:$UV_VERSION|g" Dockerfile
rm Dockerfile.bak

# Update GitHub Actions workflows
find .github/workflows -name "*.yaml" -exec sed -i.bak "s/UV_VERSION: \"[0-9.]*\"/UV_VERSION: \"$UV_VERSION\"/g" {} \;
find .github/workflows -name "*.yaml.bak" -delete

echo "UV version updated to $UV_VERSION in:"
echo "  - Dockerfile"
echo "  - .github/workflows/*.yaml"
echo ""
echo "Done!"
