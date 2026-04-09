from __future__ import annotations

import re
from pathlib import Path

from tbcl.models import FailingTest, SurefireSummary

FAIL_RE = re.compile(r"^\[ERROR\]\s+([\w.$]+)\.([\w$<>\[\]-]+):(?:\d+)?")
FAIL_ALT_RE = re.compile(r"^\[ERROR\]\s+([\w.$]+)\s*>\s*([\w$<>\[\]-]+)")
SUREFIRE_RE = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
)
STACK_RE = re.compile(r"\bat\s+([\w.$]+)\.([\w$<>]+)\(([^)]*)\)")


def clean_log_bytes(content: bytes) -> str:
    return content.replace(b"\x00", b"").decode("utf-8", errors="replace")


def parse_log_file(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    text = clean_log_bytes(raw)
    return parse_log_text(text)


def parse_log_text(text: str) -> dict:
    failing_tests: list[FailingTest] = []
    stack_frames: list[dict[str, str]] = []
    surefire = SurefireSummary()

    for line in text.splitlines():
        m = FAIL_RE.match(line.strip())
        if m:
            failing_tests.append(FailingTest(class_name=m.group(1), method_name=m.group(2)))
            continue
        m2 = FAIL_ALT_RE.match(line.strip())
        if m2:
            failing_tests.append(FailingTest(class_name=m2.group(1), method_name=m2.group(2)))
            continue
        sm = SUREFIRE_RE.search(line)
        if sm:
            surefire = SurefireSummary(
                tests_run=int(sm.group(1)),
                failures=int(sm.group(2)),
                errors=int(sm.group(3)),
                skipped=int(sm.group(4)),
            )
        sf = STACK_RE.search(line)
        if sf:
            stack_frames.append({"class": sf.group(1), "method": sf.group(2), "location": sf.group(3)})

    dedup = []
    seen = set()
    for ft in failing_tests:
        if ft.full_name in seen:
            continue
        dedup.append(ft)
        seen.add(ft.full_name)

    return {
        "failing_tests": dedup,
        "surefire": surefire,
        "stack_frames": stack_frames,
    }
