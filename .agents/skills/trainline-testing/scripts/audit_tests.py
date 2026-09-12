"""Report test smells that need human review without modifying tests."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from inspect_repo import locate_root


def python_findings(path: Path) -> list[str]:
    findings: list[str] = []
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            assertions = [child for child in ast.walk(node) if isinstance(child, ast.Assert)]
            expected_exception_calls = [
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr in {"raises", "fail"}
            ]
            if not assertions and not expected_exception_calls:
                findings.append(f"{path}:{node.lineno}: assertion-free test {node.name}")

    patterns = {
        r"pytest\.skip|@pytest\.mark\.skip": "skipped test",
        r"time\.sleep|asyncio\.sleep": "sleep-based synchronization",
        r"\b(requests|httpx|urllib\.request|socket)\b": "possible live network dependency",
        r"assert\s+(True|False)\b": "placeholder boolean assertion",
    }
    for pattern, label in patterns.items():
        for match in re.finditer(pattern, source):
            line = source.count("\n", 0, match.start()) + 1
            findings.append(f"{path}:{line}: {label}")
    return findings


def javascript_findings(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    findings: list[str] = []
    patterns = {
        r"\b(it|test)\.skip\s*\(": "skipped test",
        r"setTimeout\s*\(": "timer-based synchronization",
        r"expect\s*\(\s*(true|false)\s*\)": "placeholder boolean assertion",
    }
    for pattern, label in patterns.items():
        for match in re.finditer(pattern, source):
            line = source.count("\n", 0, match.start()) + 1
            findings.append(f"{path}:{line}: {label}")
    return findings


def main() -> None:
    root = locate_root(Path.cwd().resolve())
    findings: list[str] = []
    for path in sorted((root / "backend/tests").glob("test_*.py")):
        findings.extend(python_findings(path))
    for path in sorted((root / "frontend/src").rglob("*.test.js")):
        findings.extend(javascript_findings(path))

    if findings:
        print("Review these test-quality candidates:")
        for finding in findings:
            print(f"- {finding}")
    else:
        print("No static test-quality candidates detected.")


if __name__ == "__main__":
    main()
