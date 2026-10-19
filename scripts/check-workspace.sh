#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Checking API workspace"
(
  cd apps/api
  uv sync --locked
  uv lock --check
  uv run ruff format --check .
  uv run ruff check .
  uv run mypy app
  uv run pytest
)

for workspace in apps/web apps/pptx-generator packages/contracts; do
  echo "==> Checking $workspace"
  (
    cd "$workspace"
    npm ci
    npm run format:check
    npm run lint
    npm run typecheck
    npm run test
  )
done

echo "==> Building frontend"
(cd apps/web && npm run build)

echo "==> Building PPTX generator"
(cd apps/pptx-generator && npm run build)

echo "==> Building shared contracts"
(cd packages/contracts && npm run build)
