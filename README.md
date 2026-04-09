# TBCL — Transitive Behavioral Change Localizer

TBCL is a deterministic and explainable MVP (research-grade) for localizing **behavioral breaking changes** after Java + Maven dependency updates, with explicit support for **transitive dependency blame**.

## Problem addressed

Given a BUMP case where:
- build compiles before and after update,
- tests pass before,
- tests fail after,

TBCL tries to explain:
1. likely culprit dependency,
2. direct vs transitive root-cause level,
3. most suspicious changed methods,
4. evidence chain backing the conclusion.

## Explicit difference vs Fika

- **Fika**: emphasizes reachability/context for test generation.
- **TBCL**: emphasizes **causal differential localization** for regressions introduced by dependency updates.
  - Differential old vs new version analysis,
  - Failing-test-guided ranking,
  - Dependency/version blame,
  - Direct vs transitive classification,
  - Structured causal evidence.

## Architecture

Pipeline modules:

1. `bump_loader.py`:
   - Loads `data/benchmark/*.json`.
   - Filters `failureCategory == TEST_FAILURE`.
   - Enriches with SHA, project, updated dep, versions, compare/source links, repro commands.
   - Merges `RQData/test-types.json`.
   - Parses reproduction log if present.

2. `log_parser.py`:
   - Cleans `\x00` null bytes.
   - Extracts failing test class/method.
   - Extracts Surefire summary (`tests run`, `failures`, `errors`, `skipped`).
   - Extracts stack frames.

3. `diff_analyzer.py`:
   - Downloads old/new source jars.
   - Extracts Java methods from source.
   - Detects methods where signature remains but body hash changes.

4. `localizer.py`:
   - Scores changed methods with deterministic heuristics:
     - stack-trace class match,
     - package proximity to failing tests,
     - name overlap,
     - changed-body evidence.
   - Classifies direct/transitive (or unknown when unresolved).
   - Emits structured report per case.

5. `evaluate.py`:
   - Weak-oracle metrics over all TEST_FAILURE cases.
   - Curated subset metrics for stronger validation.

6. `dynamic_mode.py` (optional):
   - Executes pre/post reproduction commands if environment available.
   - Non-blocking fallback to offline mode.

## Data and benchmark usage (BUMP)

TBCL expects a local clone/path of BUMP and uses:
- `data/benchmark/*.json`
- `RQData/test-types.json`
- `reproductionLogs/successfulReproductionLogs/<sha>.log`

Implemented details:
- null-byte log cleaning,
- parsing failing tests + Surefire summary,
- offline end-to-end mode without requiring Docker.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run full offline pipeline:

```bash
scripts/run_tbcl_pipeline.sh /path/to/bump
```

Or step by step:

```bash
python -m tbcl.cli ingest --bump-root /path/to/bump --output outputs/normalized_index.json
python -m tbcl.cli localize --bump-root /path/to/bump --output outputs/eval/case_reports.json
python -m tbcl.cli eval-weak --bump-root /path/to/bump --out-dir outputs/eval
python -m tbcl.cli eval-curated --case-reports outputs/eval/case_reports.json --gold eval/curated_gold_subset.json --output outputs/eval/curated_metrics.json
```

## Curated subset workflow

BUMP has no gold label for exact causal method. TBCL supports:
- weak-oracle on all TEST_FAILURE,
- stronger eval on a manually curated subset (15-20 cases).

Generate a stratified starter template:

```bash
python scripts/build_curated_subset.py outputs/normalized_index.json 18
```

Then manually fill expected labels in `eval/curated_gold_subset.json`.

## Report schema per case

Each localization output includes:
- `case_sha`
- `root_cause_level` (`direct|transitive|unknown`)
- `suspect_dependency`
- `suspect_versions`
- `top_changed_methods`
- `failing_tests`
- `evidence`
- `confidence`
- `limitations`

## Limitations (current MVP)

- Direct vs transitive classification is only fully reliable when benchmark metadata contains directness hints.
- Static reachability is approximated through deterministic proxies (stack/package/name signals) rather than full call-graph reconstruction.
- Changed-method detection relies on source jar availability and Java parsing heuristics.
- Curated strong-eval labels require manual curation.

## Next steps

- Parse and compare full Maven dependency trees (pre/post) to improve direct/transitive certainty.
- Add bytecode-level semantic diff (AST/CFG level) for stronger behavioral-change signals.
- Add optional static call-graph analysis from failing tests into third-party APIs.
- Expand curated benchmark subset and inter-rater agreement process.
