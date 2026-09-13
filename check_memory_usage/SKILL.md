---
name: check_memory_usage
risk: low
use_case: simple_task
description: 分析目标主机的系统内存、Swap 和 Java 进程占用，按 RSS 排序并给出 JVM 排查建议（只读）
trigger: 当用户询问内存使用、内存不足、Swap、Java 进程占用、JVM 内存或多个 Java 服务谁占内存时触发
required_args: []
---
# check_memory_usage

通过同仓库 `_shared/linux_probe.py` 执行，只读，依赖 Linux / macOS（Darwin）与 psutil，不调用 `free` 或 GNU `ps`。采集系统内存、Swap 与按 RSS 排序的 Java 进程（含 -Xmx 等白名单 JVM 参数），重点关注 Java 进程 RSS、CPU、运行时长和 JVM 启动参数。

该 Skill 特别适合目标主机部署多个 Java 进程的场景：不要只看 JVM heap，要结合 RSS 判断 Metaspace、DirectBuffer、线程栈、JNI/native 内存和文件缓存带来的影响。

不输出完整命令行，仅保留 JAR/主类与白名单 JVM 参数。读取权限不足时标记数据缺失。

风险等级 `low`，不会重启进程、修改 JVM 参数或结束进程。默认 `LocalExecutor` 在本机执行。
