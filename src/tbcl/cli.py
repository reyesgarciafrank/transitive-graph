from __future__ import annotations

import argparse
import json
from pathlib import Path

from tbcl.bump_loader import load_bump_cases, write_normalized_index
from tbcl.evaluate import curated_eval, weak_oracle_eval
from tbcl.localizer import localize_case


def cmd_ingest(args: argparse.Namespace) -> None:
    cases = load_bump_cases(args.bump_root)
    write_normalized_index(cases, args.output)
    print(f"normalized_cases={len(cases)} output={args.output}")


def cmd_localize(args: argparse.Namespace) -> None:
    cases = load_bump_cases(args.bump_root)
    out = []
    for c in cases:
        out.append(localize_case(c, bump_root=args.bump_root).__dict__)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2))
    print(f"localized_cases={len(out)} output={args.output}")


def cmd_eval_weak(args: argparse.Namespace) -> None:
    summary = weak_oracle_eval(args.bump_root, args.out_dir)
    print(json.dumps(summary, indent=2))


def cmd_eval_curated(args: argparse.Namespace) -> None:
    metrics = curated_eval(args.case_reports, args.gold, args.output)
    print(json.dumps(metrics, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tbcl", description="Transitive Behavioral Change Localizer")
    sp = p.add_subparsers(dest="cmd", required=True)

    p_ing = sp.add_parser("ingest")
    p_ing.add_argument("--bump-root", required=True)
    p_ing.add_argument("--output", default="outputs/normalized_index.json")
    p_ing.set_defaults(func=cmd_ingest)

    p_loc = sp.add_parser("localize")
    p_loc.add_argument("--bump-root", required=True)
    p_loc.add_argument("--output", default="outputs/case_reports.json")
    p_loc.set_defaults(func=cmd_localize)

    p_ew = sp.add_parser("eval-weak")
    p_ew.add_argument("--bump-root", required=True)
    p_ew.add_argument("--out-dir", default="outputs/eval")
    p_ew.set_defaults(func=cmd_eval_weak)

    p_ec = sp.add_parser("eval-curated")
    p_ec.add_argument("--case-reports", default="outputs/eval/case_reports.json")
    p_ec.add_argument("--gold", default="eval/curated_gold_subset.json")
    p_ec.add_argument("--output", default="outputs/eval/curated_metrics.json")
    p_ec.set_defaults(func=cmd_eval_curated)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
