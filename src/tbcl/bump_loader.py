from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tbcl.log_parser import parse_log_file
from tbcl.models import BenchmarkCase, DependencyRef


BENCHMARK_DIR = Path("data/benchmark")
TEST_TYPES_FILE = Path("RQData/test-types.json")
LOGS_DIR = Path("reproductionLogs/successfulReproductionLogs")


def _pick(obj: dict[str, Any], keys: list[str], default=None):
    for k in keys:
        if k in obj and obj[k] not in (None, ""):
            return obj[k]
    return default


def _dep_from_case(c: dict[str, Any]) -> DependencyRef:
    dep = c.get("updatedDependency", {}) if isinstance(c.get("updatedDependency"), dict) else {}
    group = _pick(c, ["dependencyGroupId", "groupId"], _pick(dep, ["groupId", "group"])) or "unknown"
    artifact = _pick(c, ["dependencyArtifactId", "artifactId"], _pick(dep, ["artifactId", "artifact"])) or "unknown"
    old_v = _pick(c, ["oldVersion", "previousVersion", "fromVersion"], _pick(dep, ["from", "oldVersion"]))
    new_v = _pick(c, ["newVersion", "updatedVersion", "toVersion"], _pick(dep, ["to", "newVersion"]))
    hint = _pick(c, ["dependencyType", "updatedDependencyType", "directness"], _pick(dep, ["directness", "type"]))
    return DependencyRef(group_id=group, artifact_id=artifact, old_version=old_v, new_version=new_v, directness_hint=hint)


def _load_test_types(root: Path) -> dict[str, Any]:
    path = root / TEST_TYPES_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_bump_cases(root: str | Path) -> list[BenchmarkCase]:
    root = Path(root)
    tt = _load_test_types(root)
    out: list[BenchmarkCase] = []

    bench_dir = root / BENCHMARK_DIR
    for js in sorted(bench_dir.glob("*.json")):
        data = json.loads(js.read_text())
        entries = data if isinstance(data, list) else [data]
        for c in entries:
            if c.get("failureCategory") != "TEST_FAILURE":
                continue
            sha = _pick(c, ["sha", "commitSha", "id"]) or "unknown-sha"
            project = _pick(c, ["project", "repo", "repository"]) or "unknown-project"
            dep = _dep_from_case(c)
            case = BenchmarkCase(
                sha=sha,
                project=project,
                dependency=dep,
                compare_link=_pick(c, ["compareLink", "compareUrl"]),
                source_jar_old=_pick(c, ["oldSourceJar", "sourceJarOld", "oldSourceJarLink"]),
                source_jar_new=_pick(c, ["newSourceJar", "sourceJarNew", "newSourceJarLink"]),
                pre_cmd=_pick(c, ["preCommitReproductionCommand", "preCommand"]),
                post_cmd=_pick(c, ["breakingUpdateReproductionCommand", "postCommand"]),
                test_type_summary=tt.get(sha, {}),
                raw=c,
            )
            log_path = root / LOGS_DIR / f"{sha}.log"
            if log_path.exists():
                parsed = parse_log_file(log_path)
                case.raw["parsedLog"] = {
                    "failingTests": [x.full_name for x in parsed["failing_tests"]],
                    "surefire": parsed["surefire"].__dict__,
                    "stackFrames": parsed["stack_frames"],
                }
            out.append(case)
    return out


def write_normalized_index(cases: list[BenchmarkCase], output: str | Path) -> None:
    data = []
    for c in cases:
        data.append(
            {
                "sha": c.sha,
                "project": c.project,
                "updated_dependency": c.dependency.ga,
                "old_version": c.dependency.old_version,
                "new_version": c.dependency.new_version,
                "compare_link": c.compare_link,
                "source_jar_old": c.source_jar_old,
                "source_jar_new": c.source_jar_new,
                "pre_repro_cmd": c.pre_cmd,
                "post_repro_cmd": c.post_cmd,
                "test_type_summary": c.test_type_summary,
                "parsed_log": c.raw.get("parsedLog", {}),
            }
        )
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(data, indent=2))
