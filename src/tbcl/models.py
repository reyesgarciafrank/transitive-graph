from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DependencyRef:
    group_id: str
    artifact_id: str
    old_version: str | None = None
    new_version: str | None = None
    directness_hint: str | None = None

    @property
    def ga(self) -> str:
        return f"{self.group_id}:{self.artifact_id}"


@dataclass
class FailingTest:
    class_name: str
    method_name: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.class_name}#{self.method_name}" if self.method_name else self.class_name


@dataclass
class SurefireSummary:
    tests_run: int = 0
    failures: int = 0
    errors: int = 0
    skipped: int = 0


@dataclass
class BenchmarkCase:
    sha: str
    project: str
    dependency: DependencyRef
    compare_link: str | None = None
    source_jar_old: str | None = None
    source_jar_new: str | None = None
    pre_cmd: str | None = None
    post_cmd: str | None = None
    test_type_summary: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangedMethod:
    class_name: str
    signature: str
    old_hash: str
    new_hash: str
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)


@dataclass
class LocalizationResult:
    case_sha: str
    root_cause_level: str
    suspect_dependency: str
    suspect_versions: dict[str, str | None]
    top_changed_methods: list[dict[str, Any]]
    failing_tests: list[str]
    evidence: list[str]
    confidence: float
    limitations: list[str]
