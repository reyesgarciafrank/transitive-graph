from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from tbcl.bump_loader import load_bump_cases
from tbcl.localizer import localize_case


def weak_oracle_eval(bump_root: str, out_dir: str) -> dict:
    cases = load_bump_cases(bump_root)
    results = [localize_case(c, bump_root=bump_root) for c in cases]

    summary = {
        "cases_processed": len(results),
        "cases_with_failing_tests": sum(1 for r in results if r.failing_tests),
        "cases_with_nonempty_candidates": sum(1 for r in results if r.top_changed_methods),
        "root_level_distribution": defaultdict(int),
    }
    for r in results:
        summary["root_level_distribution"][r.root_cause_level] += 1
    summary["root_level_distribution"] = dict(summary["root_level_distribution"])

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(out_dir, "weak_oracle_summary.json").write_text(json.dumps(summary, indent=2))
    Path(out_dir, "case_reports.json").write_text(json.dumps([r.__dict__ for r in results], indent=2))
    return summary


def load_curated_gold(path: str) -> list[dict]:
    return json.loads(Path(path).read_text())


def curated_eval(case_reports_path: str, gold_path: str, out_path: str) -> dict:
    reports = {x["case_sha"]: x for x in json.loads(Path(case_reports_path).read_text())}
    gold = load_curated_gold(gold_path)
    n = len(gold)
    if n == 0:
        metrics = {"n": 0}
    else:
        dep_hits = 0
        lvl_hits = 0
        method_hits = 0
        for g in gold:
            r = reports.get(g["case_sha"], {})
            pred_dep = r.get("suspect_dependency")
            pred_lvl = r.get("root_cause_level")
            top_methods = r.get("top_changed_methods", [])
            if pred_dep in g.get("acceptable_dependencies", []):
                dep_hits += 1
            if pred_lvl == g.get("expected_root_cause_level"):
                lvl_hits += 1
            gold_tokens = set(g.get("method_tokens", []))
            if gold_tokens and any(any(t in (m.get("signature", "") + m.get("class", "")) for t in gold_tokens) for m in top_methods):
                method_hits += 1

        metrics = {
            "n": n,
            "topk_dependency_accuracy": dep_hits / n,
            "direct_vs_transitive_accuracy": lvl_hits / n,
            "suspect_method_hit_rate": method_hits / n,
        }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(metrics, indent=2))
    return metrics
