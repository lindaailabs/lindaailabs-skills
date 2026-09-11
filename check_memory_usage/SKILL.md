---
name: check_memory_usage
risk: low
use_case: simple_task
description: 分析目标主机的系统内存、Swap 和 Java 进程占用，按 RSS 排序并给出 JVM 排查建议（只读）
trigger: 当用户询问内存使用、内存不足、Swap、Java 进程占用、JVM 内存或多个 Java 服务谁占内存时触发
required_args: []
---
# check_memory_usage

只读分析：在目标 Linux 主机采集 `free -b` 和 Java 进程列表，重点关注系统内存、Swap、Java 进程 RSS、CPU、运行时长和 JVM 启动参数。

该 Skill 特别适合目标主机部署多个 Java 进程的场景：不要只看 JVM heap，要结合 RSS 判断 Metaspace、DirectBuffer、线程栈、JNI/native 内存和文件缓存带来的影响。

风险等级 `low`，不会重启进程、修改 JVM 参数或结束进程。目标主机当前由执行后端决定；Phase 1 的 `LocalExecutor` 在本机执行 Linux 命令。
