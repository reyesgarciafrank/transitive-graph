from __future__ import annotations

import hashlib
import re
import tempfile
import zipfile
from pathlib import Path

from urllib.request import urlopen, Request

from tbcl.models import ChangedMethod

METHOD_RE = re.compile(
    r"(?P<sig>(public|protected|private)?\s*(static\s+)?[\w<>,\[\]\s?]+\s+[\w$]+\s*\([^)]*\))\s*\{",
    re.MULTILINE,
)
PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
CLASS_RE = re.compile(r"\bclass\s+([\w$]+)")


def _download(url: str, to: Path) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "tbcl/0.1"})
        with urlopen(req, timeout=30) as resp:
            to.write_bytes(resp.read())
        return True
    except Exception:
        return False


def _extract_methods(java_src: str) -> dict[str, str]:
    methods: dict[str, str] = {}
    pkg = PACKAGE_RE.search(java_src)
    pkg_name = pkg.group(1) if pkg else ""
    cls = CLASS_RE.search(java_src)
    cls_name = cls.group(1) if cls else "Unknown"
    prefix = f"{pkg_name}.{cls_name}" if pkg_name else cls_name

    for m in METHOD_RE.finditer(java_src):
        sig = " ".join(m.group("sig").split())
        start = m.end() - 1
        depth = 0
        end = start
        for i, ch in enumerate(java_src[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body = java_src[start : end + 1]
        methods[f"{prefix}::{sig}"] = hashlib.sha256(body.encode()).hexdigest()
    return methods


def _methods_from_source_jar(path: Path) -> dict[str, str]:
    methods: dict[str, str] = {}
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.endswith(".java"):
                continue
            try:
                text = zf.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            methods.update(_extract_methods(text))
    return methods


def changed_methods_from_jars(old_url: str | None, new_url: str | None) -> list[ChangedMethod]:
    if not old_url or not new_url:
        return []
    with tempfile.TemporaryDirectory() as td:
        old_path = Path(td) / "old-sources.jar"
        new_path = Path(td) / "new-sources.jar"
        if not (_download(old_url, old_path) and _download(new_url, new_path)):
            return []
        old_methods = _methods_from_source_jar(old_path)
        new_methods = _methods_from_source_jar(new_path)
        changed: list[ChangedMethod] = []
        for sig, new_hash in new_methods.items():
            old_hash = old_methods.get(sig)
            if old_hash and old_hash != new_hash:
                class_name, method_sig = sig.split("::", 1)
                changed.append(
                    ChangedMethod(
                        class_name=class_name,
                        signature=method_sig,
                        old_hash=old_hash,
                        new_hash=new_hash,
                    )
                )
        return changed
