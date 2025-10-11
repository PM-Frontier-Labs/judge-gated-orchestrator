#!/bin/bash
# Trigger the judge for a given phase

set -e

if [ -z "$1" ]; then
  echo "Usage: run_judge.sh <PHASE_ID>"
  exit 1
fi

PHASE_ID="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

echo "Running judge for phase $PHASE_ID..."

python3 tools/judge.py "$PHASE_ID"
