# lindaailabs-skills

运维 Agent 的**动态 Skill 仓库**（独立于 `lindaailabs-ops-agent`）。

由 `ops-agent` 的 `SkillLoader` 扫描本目录，每个子目录即一个 Skill。

## Skill 规范
每个 Skill 目录必须包含：
- `SKILL.md`：YAML frontmatter（如下）+ Markdown 描述
- `executor.py`：暴露 `execute(state: dict) -> dict`

### SKILL.md frontmatter 字段
| 字段 | 说明 |
| --- | --- |
| `name` | Skill 唯一名（与目录名无关，但建议一致） |
| `risk` | `low` / `high`；`high` 触发人工审批中断 |
| `use_case` | 对应模型池的 `use_case`（如 `simple_task`） |
| `description` | 能力描述（作为 LLM 工具说明） |
| `trigger` | 触发条件描述 |

### executor.py 示例
```python
from src.executor import get_executor

def execute(state: dict) -> dict:
    host = (state.get("skill_args") or {}).get("host", "localhost")
    out = get_executor().run("df -h")
    return {"host": host, "stdout": out.get("stdout", ""), "returncode": out.get("returncode", -1)}
```

## 现有 Skill
- `check_disk_usage`（risk: low）：查看磁盘使用率。
- `disk_cleanup`（risk: high）：高危清理，演示期仅只读枚举，需审批后执行。
