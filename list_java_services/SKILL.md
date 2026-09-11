---
name: list_java_services
risk: low
use_case: simple_task
description: 列出本机 Java 服务清单，关联 JAR/主类、PID、运行时长、RSS 和监听端口（只读）。
trigger: 有哪些 Java 服务、哪个 JAR 对应哪个 PID、服务端口和启动时间
required_args: []
parameters:
  target:
    type: string
    description: 可选，筛选的 PID、JAR 文件名或主类；不填则检查全部
---
# list_java_services

通过同仓库 `_shared/linux_probe.py` 和 Agent 的 `run_local_probe` 执行，只读，依赖 Linux、Python 和 psutil>=6,<8。默认 LocalExecutor；远程 host 返回不支持，不会伪装成远程结果。

服务名来自 JAR 文件名或 Java 主类，是进程身份线索，不保证等于业务名称。仅保留身份和白名单 JVM 参数，不输出完整命令行或环境变量。

采集权限不足、进程退出、端口无法读取应标记数据缺失。结果仅覆盖当前可见 PID/网络命名空间；在容器内不代表整台宿主机。CPU 进程百分比以一个逻辑核为 100%，短窗口采样不能证明持续高负载或根因。不会重启、kill、dump 堆或修改服务。
