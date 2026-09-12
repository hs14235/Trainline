"""Cross-platform repository task runner.

Run ``python scripts/tasks.py --list`` for the supported commands. The script
does not install dependencies or perform destructive database/Git operations.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
NPM = "npm.cmd" if os.name == "nt" else "npm"


def run(command: Sequence[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    printable = subprocess.list2cmdline(list(command))
    print(f"\n> {printable}", flush=True)
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def manage(*arguments: str, settings: str | None = None) -> None:
    command = [sys.executable, "manage.py", *arguments]
    if settings:
        command.append(f"--settings={settings}")
    run(command, cwd=BACKEND)


def check() -> None:
    manage("check")
    manage("makemigrations", "--check", "--dry-run")


def migrate() -> None:
    manage("migrate")


def test_fast() -> None:
    run([sys.executable, "-m", "pytest", "-m", "not postgres"])


def test_postgres() -> None:
    environment = os.environ.copy()
    database_url = environment.get(
        "TEST_DATABASE_URL",
        "postgresql://trainline_test_user:trainline_test_password@127.0.0.1:5433/trainline_test",
    )
    if not database_url.startswith(("postgres://", "postgresql://")):
        raise SystemExit(
            "TEST_DATABASE_URL must point to an isolated PostgreSQL database for this tier."
        )
    parsed_database_url = urlparse(database_url)
    if "test" not in parsed_database_url.path.lower():
        raise SystemExit("Refusing a PostgreSQL URL whose database name does not contain 'test'.")

    environment["TEST_DATABASE_URL"] = database_url
    use_managed_service = "TEST_DATABASE_URL" not in os.environ
    started_service = False

    if use_managed_service:
        status_command = [
            "docker",
            "compose",
            "-f",
            "docker-compose.test.yml",
            "ps",
            "--status",
            "running",
            "--quiet",
            "test-db",
        ]
        status_result = subprocess.run(
            status_command,
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        if not status_result.stdout.strip():
            run(
                [
                    "docker",
                    "compose",
                    "-f",
                    "docker-compose.test.yml",
                    "up",
                    "--detach",
                    "--wait",
                    "test-db",
                ]
            )
            started_service = True

    try:
        run([sys.executable, "-m", "pytest", "-m", "postgres"], env=environment)
    finally:
        if started_service:
            run(["docker", "compose", "-f", "docker-compose.test.yml", "down"])


def coverage() -> None:
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not postgres",
            "--cov=core",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=90",
        ]
    )


def lint_backend() -> None:
    run([sys.executable, "-m", "flake8", "backend", "scripts"])


def format_check() -> None:
    run([sys.executable, "-m", "black", "--check", "backend", "scripts"])
    run([sys.executable, "-m", "isort", "--check-only", "backend", "scripts"])


def format_code() -> None:
    run([sys.executable, "-m", "black", "backend", "scripts"])
    run([sys.executable, "-m", "isort", "backend", "scripts"])


def frontend_test() -> None:
    env = os.environ.copy()
    env["CI"] = "true"
    run([NPM, "test", "--", "--watchAll=false"], cwd=FRONTEND, env=env)


def frontend_lint() -> None:
    run([NPM, "run", "lint"], cwd=FRONTEND)


def frontend_build() -> None:
    run([NPM, "run", "build"], cwd=FRONTEND)


def compose_up() -> None:
    run(["docker", "compose", "up", "--build", "--detach"])


def compose_down() -> None:
    run(["docker", "compose", "down"])


def compose_status() -> None:
    run(["docker", "compose", "ps"])


def seed_demo() -> None:
    manage("seed_demo")


def verify() -> None:
    check()
    lint_backend()
    format_check()
    test_fast()
    coverage()
    frontend_lint()
    frontend_test()
    frontend_build()


TASKS: dict[str, tuple[Callable[[], None], str]] = {
    "check": (check, "Run Django checks and detect missing migrations."),
    "migrate": (migrate, "Apply native-development database migrations."),
    "test": (test_fast, "Run the fast SQLite-backed test suite."),
    "test-postgres": (test_postgres, "Run PostgreSQL-marked integration tests."),
    "coverage": (coverage, "Run fast tests with branch coverage."),
    "lint-backend": (lint_backend, "Run flake8 over backend and task scripts."),
    "format-check": (format_check, "Check Black and isort formatting."),
    "format": (format_code, "Apply Black and isort formatting."),
    "frontend-test": (frontend_test, "Run frontend tests once in CI mode."),
    "frontend-lint": (frontend_lint, "Run the frontend ESLint configuration."),
    "frontend-build": (frontend_build, "Create a production frontend build."),
    "compose-up": (compose_up, "Build and start the development stack."),
    "compose-down": (compose_down, "Stop the development stack without deleting data."),
    "compose-status": (compose_status, "Show development service health."),
    "seed-demo": (seed_demo, "Idempotently create local demo data."),
    "verify": (verify, "Run the complete fast local verification sequence."),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", choices=sorted(TASKS))
    parser.add_argument("--list", action="store_true", help="List available tasks.")
    arguments = parser.parse_args()

    if arguments.list or not arguments.task:
        for name, (_, description) in TASKS.items():
            print(f"{name:16} {description}")
        return

    TASKS[arguments.task][0]()


if __name__ == "__main__":
    main()
