from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class DynamicRunResult:
    available: bool
    pre_output: str = ""
    post_output: str = ""
    error: str | None = None


def run_dynamic_if_available(pre_cmd: str | None, post_cmd: str | None, cwd: str) -> DynamicRunResult:
    if not pre_cmd or not post_cmd:
        return DynamicRunResult(available=False, error="missing_reproduction_commands")
    try:
        pre = subprocess.run(pre_cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=900)
        post = subprocess.run(post_cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=900)
        return DynamicRunResult(
            available=True,
            pre_output=(pre.stdout + "\n" + pre.stderr)[:50000],
            post_output=(post.stdout + "\n" + post.stderr)[:50000],
        )
    except FileNotFoundError:
        return DynamicRunResult(available=False, error="docker_or_runtime_not_available")
    except Exception as exc:
        return DynamicRunResult(available=False, error=str(exc))
