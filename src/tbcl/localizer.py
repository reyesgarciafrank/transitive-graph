from __future__ import annotations

from tbcl.diff_analyzer import changed_methods_from_jars
from tbcl.log_parser import parse_log_file
from tbcl.models import BenchmarkCase, ChangedMethod, LocalizationResult


def _package_prefix(name: str) -> str:
    parts = name.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else name


def _score_method(m: ChangedMethod, failing_tests: list[str], stack_classes: set[str]) -> ChangedMethod:
    score = 0.1
    evidence: list[str] = ["changed_method_same_signature_diff_body"]
    m_pkg = _package_prefix(m.class_name)

    for t in failing_tests:
        t_pkg = _package_prefix(t.split("#")[0])
        if t_pkg and m_pkg.startswith(t_pkg[: min(len(t_pkg), 10)]):
            score += 0.25
            evidence.append(f"package_proximity:{t_pkg}")
            break

    if m.class_name in stack_classes:
        score += 0.5
        evidence.append("stacktrace_class_match")

    method_name = m.signature.split("(")[0].split()[-1]
    if any(method_name.lower() in t.lower() for t in failing_tests):
        score += 0.2
        evidence.append("name_overlap_with_failed_test")

    m.score = min(score, 1.0)
    m.evidence = sorted(set(evidence))
    return m


def _classify_direct_transitive(case: BenchmarkCase, changed_count: int) -> tuple[str, list[str]]:
    hint = (case.dependency.directness_hint or "").lower()
    ev = []
    if "transitive" in hint:
        return "transitive", ["directness_hint_from_benchmark:transitive"]
    if "direct" in hint:
        return "direct", ["directness_hint_from_benchmark:direct"]
    if changed_count == 0:
        return "unknown", ["no_changed_methods_detected"]
    return "unknown", ["insufficient_dependency_resolution_data"]


def localize_case(case: BenchmarkCase, bump_root: str | None = None) -> LocalizationResult:
    failing_tests = []
    stack_classes = set()
    surefire = None
    if bump_root:
        import pathlib

        lp = pathlib.Path(bump_root) / "reproductionLogs" / "successfulReproductionLogs" / f"{case.sha}.log"
        if lp.exists():
            parsed = parse_log_file(lp)
            failing_tests = [x.full_name for x in parsed["failing_tests"]]
            stack_classes = {x["class"] for x in parsed["stack_frames"]}
            surefire = parsed["surefire"]

    changed = changed_methods_from_jars(case.source_jar_old, case.source_jar_new)
    scored = sorted([_score_method(m, failing_tests, stack_classes) for m in changed], key=lambda x: x.score, reverse=True)
    root_level, root_ev = _classify_direct_transitive(case, len(scored))

    evidence = [
        f"updated_dependency:{case.dependency.ga}:{case.dependency.old_version}->{case.dependency.new_version}",
        f"failing_tests_count:{len(failing_tests)}",
        f"changed_methods_detected:{len(scored)}",
        *root_ev,
    ]
    if surefire:
        evidence.append(
            f"surefire_summary:run={surefire.tests_run},failures={surefire.failures},errors={surefire.errors},skipped={surefire.skipped}"
        )

    top = [
        {
            "class": m.class_name,
            "signature": m.signature,
            "score": round(m.score, 3),
            "evidence": m.evidence,
        }
        for m in scored[:10]
    ]

    conf = 0.2
    if top:
        conf = min(0.95, 0.35 + top[0]["score"] * 0.6)

    limitations = []
    if not failing_tests:
        limitations.append("no_failing_tests_parsed_from_log")
    if not top:
        limitations.append("no_changed_methods_found_from_source_jars")
    if root_level == "unknown":
        limitations.append("direct_vs_transitive_not_resolved_without_dependency_tree")

    return LocalizationResult(
        case_sha=case.sha,
        root_cause_level=root_level,
        suspect_dependency=case.dependency.ga,
        suspect_versions={"old": case.dependency.old_version, "new": case.dependency.new_version},
        top_changed_methods=top,
        failing_tests=failing_tests,
        evidence=evidence,
        confidence=round(conf, 3),
        limitations=limitations,
    )
