---
name: disk_cleanup
risk: high
use_case: simple_task
description: 评估目标路径的磁盘占用并作为清理前 dry-run（高危清理意图，自动触发必须经人工审批）
trigger: 当用户要求清理磁盘、删除日志、释放空间、清理临时文件时触发
required_args:
  - path
---
# disk_cleanup

高危清理意图：自动触发时必须经 `interrupt()` 人工审批。

当前 Phase 1 执行器只做清理前 dry-run：对用户指定的 `path` 执行只读占用统计（`du -sh <path>`），避免误删。
`path` 是必填参数，缺失时 executor 会拒绝执行任何命令。

真实部署如替换为实际清理指令，应保留 dry-run、日志、回滚或备份方案，并避免把未转义的用户输入直接拼进 shell。
