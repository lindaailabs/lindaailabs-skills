---
name: disk_cleanup
risk: high
use_case: simple_task
description: 清理目标主机磁盘空间（高危，必须经人工审批后执行）
trigger: 当用户要求清理磁盘、删除日志、释放空间、清理临时文件时触发
required_args:
  - path
---
# disk_cleanup

高危操作示例：执行前必须经 `interrupt()` 人工审批。
注意：Phase 1 演示用执行器仅做只读枚举（`du -sh /tmp`），避免误删；
真实部署应将 run() 的命令替换为实际清理指令，并保留必要日志与回滚方案。
