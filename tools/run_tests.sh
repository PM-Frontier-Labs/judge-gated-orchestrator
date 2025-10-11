#!/bin/bash
# Run tests and save results

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRACES_DIR="$REPO_ROOT/.repo/traces"

cd "$REPO_ROOT"

echo "Running tests..."

# Run pytest and capture output
if pytest tests/ -v > "$TRACES_DIR/last_pytest.txt" 2>&1; then
  echo "✅ Tests passed"
  exit 0
else
  echo "❌ Tests failed"
  cat "$TRACES_DIR/last_pytest.txt"
  exit 1
fi
