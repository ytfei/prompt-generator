from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings

TIERS = ("default", "nano", "mid", "pro")


def get_chat_model(temperature: float = 0.7, tier: str = "default") -> BaseChatModel | None:
    """按 .env 配置实例化 Chat 模型（OpenAI 兼容协议）。

    tier: nano/mid/pro 档位，未配置该档时回落默认模型；
    provider 未配置时返回 None，Agent 各节点走本地规则/模板逻辑。
    """
    if settings.resolved_provider == "mock":
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.model_for_tier(tier if tier in TIERS else "default"),
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or None,
        temperature=temperature,
    )
