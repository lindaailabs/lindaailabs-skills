"""check_disk_usage：只读查看磁盘使用率。"""
from src.executor import get_executor


def execute(state: dict) -> dict:
    host = (state.get("skill_args") or {}).get("host", "localhost")
    out = get_executor().run("df -h")
    return {
        "host": host,
        "stdout": out.get("stdout", ""),
        "stderr": out.get("stderr", ""),
        "returncode": out.get("returncode", -1),
    }
