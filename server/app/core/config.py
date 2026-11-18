from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = ""  # 留空 → mock 模式
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/prompt_studio.db"

    @property
    def resolved_provider(self) -> str:
        """provider 与 model 均配置才算真实接入，否则回落 mock。"""
        if self.llm_provider and self.llm_provider != "mock" and self.llm_model:
            return self.llm_provider
        return "mock"


settings = Settings()
