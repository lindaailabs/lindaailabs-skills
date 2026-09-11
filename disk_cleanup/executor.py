"""disk_cleanup：高危清理（演示期仅做只读枚举，需审批后执行）。"""
from src.executor import get_executor


def execute(state: dict) -> dict:
    # 演示期：只读枚举，避免 Phase 1 误删数据。
    # 真实环境此处应替换为实际清理命令，并确保有回滚/备份策略。
    out = get_executor().run("du -sh /tmp 2>/dev/null || echo 'no /tmp'")
    return {
        "action": "disk_cleanup(dry-run)",
        "stdout": out.get("stdout", ""),
        "stderr": out.get("stderr", ""),
        "returncode": out.get("returncode", -1),
    }
