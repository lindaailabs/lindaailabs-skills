---
name: check_service_health
risk: low
use_case: simple_task
description: 检查一个 Java 服务的进程状态、监听端口 TCP 连接和用户提供的 HTTP 健康接口（只读）；target 必填，多候选需指定 PID。
trigger: 检查某个 Java 服务是否存活、端口是否可连接、健康接口是否正常
required_args: [target]
parameters:
  target:
    type: string
    description: 要检查的 Java 服务 PID、JAR 文件名或主类；多个匹配时请指定 PID
  health_url:
    type: string
    description: 可选，用户明确提供的 HTTP(S) 健康检查地址；必须对应此 PID 的本机监听端口，不猜接口路径
---
# check_service_health

通过同仓库 `_shared/linux_probe.py` 和 Agent 的 `run_local_probe` 执行，只读，依赖 Linux、Python 和 psutil>=6,<8。默认 LocalExecutor；远程 host 返回不支持，不会伪装成远程结果。

先按 PID 或服务身份匹配；多个候选只返回候选，不能自行选一个。分别报告进程、TCP 和 HTTP 结果：端口连通不能证明业务健康。未提供 health_url 时不探测猜测的路径。HTTP 不跟随重定向、不使用代理、保持 TLS 校验，不返回响应正文。

采集权限不足、进程退出、端口无法读取应标记数据缺失。结果仅覆盖当前可见 PID/网络命名空间；在容器内不代表整台宿主机。CPU 进程百分比以一个逻辑核为 100%，短窗口采样不能证明持续高负载或根因。不会重启、kill、dump 堆或修改服务。
