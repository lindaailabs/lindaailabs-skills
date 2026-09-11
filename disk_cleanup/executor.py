"""disk_cleanup：高危清理（演示期仅做只读枚举，需审批后执行）。"""
import shlex

from src.executor import get_executor


def execute(state: dict) -> dict:
    # 演示期：只读枚举，避免 Phase 1 误删数据。
    # 真实环境此处应替换为实际清理命令，并确保有回滚/备份策略。
    args = state.get("skill_args") or {}
    path = args.get("path")
    if not path:
        return {
            "action": "disk_cleanup(dry-run)",
            "error": "缺少必填参数 path，未执行任何命令。",
            "returncode": 2,
        }

    safe_path = shlex.quote(str(path))
    out = get_executor().run(f"du -sh {safe_path} 2>/dev/null || echo 'no {safe_path}'")
    return {
        "action": "disk_cleanup(dry-run)",
        "path": path,
        "stdout": out.get("stdout", ""),
        "stderr": out.get("stderr", ""),
        "returncode": out.get("returncode", -1),
    }
