import json
from pathlib import Path

from tbcl.bump_loader import load_bump_cases


def test_load_bump_cases_filters_test_failure(tmp_path: Path):
    (tmp_path / "data/benchmark").mkdir(parents=True)
    (tmp_path / "RQData").mkdir(parents=True)
    (tmp_path / "reproductionLogs/successfulReproductionLogs").mkdir(parents=True)

    row1 = {
        "sha": "a1",
        "project": "p",
        "failureCategory": "TEST_FAILURE",
        "groupId": "g",
        "artifactId": "a",
        "oldVersion": "1.0.0",
        "newVersion": "1.0.1",
    }
    row2 = {"sha": "a2", "failureCategory": "COMPILATION_FAILURE"}
    (tmp_path / "data/benchmark/cases.json").write_text(json.dumps([row1, row2]))
    (tmp_path / "RQData/test-types.json").write_text(json.dumps({"a1": {"type": "failure"}}))

    cases = load_bump_cases(tmp_path)
    assert len(cases) == 1
    assert cases[0].sha == "a1"
    assert cases[0].dependency.ga == "g:a"
