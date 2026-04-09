from tbcl.localizer import _classify_direct_transitive
from tbcl.models import BenchmarkCase, DependencyRef


def test_classify_direct_from_hint():
    case = BenchmarkCase(
        sha="x",
        project="p",
        dependency=DependencyRef("g", "a", "1", "2", directness_hint="direct"),
    )
    lvl, _ = _classify_direct_transitive(case, changed_count=1)
    assert lvl == "direct"
