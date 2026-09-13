"""check_memory_usage：只读采集系统内存与 Java 进程信息（跨平台，纯 psutil）。"""
from pathlib import Path

from src.executor.python_probe import run_local_probe


def execute(state: dict) -> dict:
    script = Path(__file__).resolve().parent.parent / "_shared" / "linux_probe.py"
    return run_local_probe(script, "check_memory_usage", state)
