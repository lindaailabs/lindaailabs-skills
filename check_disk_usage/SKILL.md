---
name: check_disk_usage
risk: low
use_case: simple_task
description: 检查目标主机的磁盘使用率（执行 df -h 并汇总）
trigger: 当用户询问磁盘空间、磁盘使用率、剩余空间、哪个分区快满时触发
required_args: []
---
# check_disk_usage

通过同仓库 `_shared/linux_probe.py` 执行，只读，依赖 Linux / macOS 与 psutil，不执行 `df`。返回各挂载点使用率，并自动跳过容量为 0 的伪挂载（如 devfs），避免误报 100%。
风险等级 `low`，无需人工审批，直接执行。
