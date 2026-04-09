#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: build_curated_subset.py <normalized_index.json> [n=18]")
        raise SystemExit(1)

    n = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    rows = json.loads(Path(sys.argv[1]).read_text())

    buckets: dict[str, list[dict]] = {
        "major": [],
        "minor": [],
        "patch": [],
        "other": [],
    }

    for r in rows:
        old_v = str(r.get("old_version") or "")
        new_v = str(r.get("new_version") or "")
        try:
            old_parts = [int(x) for x in old_v.split(".")[:3]]
            new_parts = [int(x) for x in new_v.split(".")[:3]]
            if new_parts[0] != old_parts[0]:
                buckets["major"].append(r)
            elif new_parts[1] != old_parts[1]:
                buckets["minor"].append(r)
            elif new_parts[2] != old_parts[2]:
                buckets["patch"].append(r)
            else:
                buckets["other"].append(r)
        except Exception:
            buckets["other"].append(r)

    random.seed(7)
    out = []
    per_bucket = max(1, n // 4)
    for key in ["major", "minor", "patch", "other"]:
        sample = buckets[key][:]
        random.shuffle(sample)
        out.extend(sample[:per_bucket])

    if len(out) < n:
        remain = [r for r in rows if r not in out]
        random.shuffle(remain)
        out.extend(remain[: n - len(out)])

    templ = [
        {
            "case_sha": x["sha"],
            "acceptable_dependencies": [x.get("updated_dependency")],
            "expected_root_cause_level": "unknown",
            "method_tokens": [],
            "notes": "Fill manually after code inspection / bisect.",
        }
        for x in out[:n]
    ]

    Path("eval/curated_gold_subset.generated.json").write_text(json.dumps(templ, indent=2))
    print("Wrote eval/curated_gold_subset.generated.json")


if __name__ == "__main__":
    main()
