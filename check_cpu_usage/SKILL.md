---
name: check_cpu_usage
risk: low
use_case: simple_task
description: 分析本机 CPU、1/5/15 分钟负载、I/O wait 和 CPU 高占用进程，识别 Java 服务；可指定 target（只读）。
trigger: 服务器慢、CPU 高、系统负载高、哪个服务消耗 CPU
required_args: []
parameters:
  target:
    type: string
    description: 可选，筛选的 PID、JAR 文件名或主类；不填则检查全部
---
# check_cpu_usage

通过同仓库 `_shared/linux_probe.py` 和 Agent 的 `run_local_probe` 执行，只读，依赖 Linux / macOS（Darwin）、Python 和 psutil>=6,<8；跨平台实现，不调用任何 Linux 专属命令。默认 LocalExecutor；远程 host 返回不支持，不会伪装成远程结果。

服务名来自 JAR 文件名或 Java 主类，是进程身份线索，不保证等于业务名称。仅保留身份和白名单 JVM 参数，不输出完整命令行或环境变量。

采集权限不足、进程退出、端口无法读取应标记数据缺失。结果仅覆盖当前可见 PID/网络命名空间；在容器内不代表整台宿主机。CPU 进程百分比以一个逻辑核为 100%，短窗口采样不能证明持续高负载或根因。不会重启、kill、dump 堆或修改服务。
