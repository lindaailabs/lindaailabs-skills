"""list_java_services: read-only Linux probe entrypoint."""
from pathlib import Path

from src.executor.python_probe import run_local_probe


def execute(state: dict) -> dict:
    script = Path(__file__).resolve().parent.parent / "_shared" / "linux_probe.py"
    return run_local_probe(script, "list_java_services", state)
