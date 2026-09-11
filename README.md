# lindaailabs-skills

运维 Agent 的动态 Skill 仓库，由 ops-agent 的 SkillLoader 扫描加载。

## Skill 规范

每个 Skill 目录包含 `SKILL.md`（YAML frontmatter + 描述）和 `executor.py`（暴露 `execute(state: dict) -> dict`）。

| 字段 | 说明 |
| --- | --- |
| `name` | Skill 唯一名，建议与目录一致 |
| `risk` | low / high；high 在 automated 模式触发人工审批 |
| `use_case` | 对应模型池的 use_case |
| `description` | 提供给规划器的能力描述 |
| `trigger` | 触发条件 |
| `required_args` | 执行前必须补齐的参数 |
| `parameters` | 可选字符串参数 schema，含 type: string 和 description |

```python
from src.executor import get_executor

def execute(state: dict) -> dict:
    host = (state.get("skill_args") or {}).get("host", "localhost")
    out = get_executor().run("df -h")
    return {"host": host, "stdout": out.get("stdout", ""), "returncode": out.get("returncode", -1)}
```

## 现有 Skill

- `check_disk_usage`（low）：查看磁盘使用率。
- `check_memory_usage`（low）：系统内存、Swap、Java RSS/JVM 启动参数检查。
- `disk_cleanup`（high）：清理前 dry-run，只读占用统计；自动触发需审批。
- `list_java_services`（low）：JAR/主类、PID、运行时长、RSS 和监听端口清单。
- `check_cpu_usage`（low）：约 1 秒 CPU 采样、系统负载、I/O wait 与高占用进程；可按 PID/JAR 筛选。
- `check_service_health`（low）：按 PID/JAR 检查进程、TCP 与用户提供的健康接口；多实例先选择 PID。

## 部署与执行

新增三个服务 Skill 共用 `_shared/linux_probe.py`，依赖 Agent 的 `src.executor.python_probe` 和 `psutil>=6,<8`。需要同步更新两个仓库，在 Agent 虚拟环境安装 requirements 后重启。使用项目 SkillLoader 校验；Codex 通用 Skill 校验器不识别本项目自定义 frontmatter。

`list_java_services`、`check_cpu_usage` 可选参数 `target`；`check_service_health` 必填 `target`（PID、JAR 文件名或主类），可选 `health_url`。健康 URL 必须由用户提供，并匹配选中 PID 的本机监听地址/端口；不带凭证/查询参数，不跟随重定向，不使用代理。未提供 URL 时只检查进程和 TCP，不猜路径。

所有实际采集面向 Linux。新增三个采集器拒绝远程 host，仅覆盖本机当前可见 PID/网络命名空间。此前的磁盘/内存 Skill 中 host 仍只是标识，LocalExecutor 在本机运行，尚未接入 SSH 路由。

## 可用性约定

- executor 自行校验关键参数；缺参时不默认选择清理路径。Shell 参数必须转义。
- 当前清理保持 dry-run；真实删除需另行确认审批、日志及回滚方案。
- JAR/主类是进程身份线索，不保证等于业务服务名；TCP 可连接不证明业务健康。
- CPU 是短时间采样，进程 100% 表示一个逻辑核。权限不足或进程变化时报告数据缺失，不据此断定根因或泄漏。
- 新增三个服务采集器只输出身份和白名单 JVM 参数，不输出完整启动命令行。
