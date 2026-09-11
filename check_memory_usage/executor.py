"""check_memory_usage：只读采集系统内存与 Java 进程信息。"""
from src.executor import get_executor


_COMMAND = r"""command -v free >/dev/null 2>&1 || { echo 'free command not found' >&2; exit 127; }
command -v ps >/dev/null 2>&1 || { echo 'ps command not found' >&2; exit 127; }
free -b
printf '\n__JAVA_PROCESSES__\n'
ps -eo pid=,ppid=,user=,pmem=,pcpu=,rss=,vsz=,etime=,comm=,args= --sort=-pmem | awk '
  BEGIN { count = 0 }
  {
    line = tolower($0)
    if ($9 == "java" || $9 == "javaw" || line ~ /[[:space:]]java([[:space:]]|$)/) {
      print
      count++
      if (count >= 20) exit
    }
  }'
"""


def execute(state: dict) -> dict:
    host = (state.get("skill_args") or {}).get("host", "localhost")
    out = get_executor().run(_COMMAND)
    return {
        "skill": "check_memory_usage",
        "host": host,
        "stdout": out.get("stdout", ""),
        "stderr": out.get("stderr", ""),
        "returncode": out.get("returncode", -1),
    }
