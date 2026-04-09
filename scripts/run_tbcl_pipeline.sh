#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <bump_root>"
  exit 1
fi

BUMP_ROOT="$1"
python -m tbcl.cli ingest --bump-root "$BUMP_ROOT" --output outputs/normalized_index.json
python -m tbcl.cli localize --bump-root "$BUMP_ROOT" --output outputs/eval/case_reports.json
python -m tbcl.cli eval-weak --bump-root "$BUMP_ROOT" --out-dir outputs/eval
python -m tbcl.cli eval-curated --case-reports outputs/eval/case_reports.json --gold eval/curated_gold_subset.json --output outputs/eval/curated_metrics.json
