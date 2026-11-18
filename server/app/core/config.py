from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = ""  # 留空 → mock 模式
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""  # 默认模型
    llm_model_nano: str = ""  # 快档（未配置回落默认）
    llm_model_mid: str = ""  # 中档（未配置回落默认）
    llm_model_pro: str = ""  # 强档（未配置回落默认）
    database_url: str = "sqlite+aiosqlite:///./data/prompt_studio.db"

    @property
    def resolved_provider(self) -> str:
        """provider 与 model 均配置才算真实接入，否则回落 mock。"""
        if self.llm_provider and self.llm_provider != "mock" and self.llm_model:
            return self.llm_provider
        return "mock"

    def model_for_tier(self, tier: str) -> str:
        """按档位取模型：未配置该档时回落默认模型。"""
        mapping = {
            "nano": self.llm_model_nano,
            "mid": self.llm_model_mid,
            "pro": self.llm_model_pro,
        }
        return mapping.get(tier) or self.llm_model

    def tier_configured(self, tier: str) -> bool:
        if tier == "default":
            return True
        return bool(self.model_for_tier(tier) and self.model_for_tier(tier) != self.llm_model)


settings = Settings()
