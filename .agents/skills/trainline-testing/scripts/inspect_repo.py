"""Read-only Trainline repository and test-tier inventory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SENTINELS = (
    Path("backend/manage.py"),
    Path("frontend/package.json"),
    Path("docker-compose.yml"),
    Path("scripts/tasks.py"),
)


def locate_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if all((candidate / sentinel).is_file() for sentinel in SENTINELS):
            return candidate
    raise SystemExit("Trainline repository root was not found from the current directory.")


def main() -> None:
    root = locate_root(Path.cwd().resolve())
    backend_tests = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in (root / "backend/tests").glob("test_*.py")
    )
    frontend_tests = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in (root / "frontend/src").rglob("*.test.js")
    )
    inventory = {
        "repository_root": str(root),
        "sentinels": [str(path).replace("\\", "/") for path in SENTINELS],
        "backend_tests": backend_tests,
        "frontend_tests": frontend_tests,
        "postgres_test_service": (root / "docker-compose.test.yml").is_file(),
        "frontend_lockfile": (root / "frontend/package-lock.json").is_file(),
        "available_executables": {
            name: bool(shutil.which(name)) for name in ("python", "docker", "npm", "npm.cmd")
        },
        "commands": {
            "fast": "python scripts/tasks.py test",
            "postgres": "python scripts/tasks.py test-postgres",
            "coverage": "python scripts/tasks.py coverage",
            "frontend": "python scripts/tasks.py frontend-test",
            "complete_fast": "python scripts/tasks.py verify",
        },
    }
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
