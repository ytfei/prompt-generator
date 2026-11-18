from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


def get_chat_model(temperature: float = 0.7) -> BaseChatModel | None:
    """按 .env 配置实例化 Chat 模型（OpenAI 兼容协议）。

    未配置 provider/model 时返回 None，Agent 各节点走本地规则/模板逻辑。
    """
    if settings.resolved_provider == "mock":
        return None
    return ChatOpenAICompat(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or None,
        temperature=temperature,
    )


def ChatOpenAICompat(**kwargs) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(**kwargs)
