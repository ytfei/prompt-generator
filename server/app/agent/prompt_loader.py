from pathlib import Path
from string import Template

_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **variables: str) -> str:
    """加载 agent/prompts/{name}.md 并渲染 ${var} 占位符。

    提示词与代码分离，便于凭出图效果持续调优（见 ARCHITECTURE §5.3）。
    """
    tpl = Template((_DIR / f"{name}.md").read_text(encoding="utf-8"))
    return tpl.substitute(**variables) if variables else tpl.template
