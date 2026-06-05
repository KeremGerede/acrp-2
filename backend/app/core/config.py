from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./agentic_devops.db"
    FRONTEND_URL: str = "http://localhost:5173"

    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    DEFAULT_WEBHOOK_SECRET: str = "change-me"
    GITHUB_TOKEN: str = ""
    # create_revert_pr | create_and_merge_revert_pr | disabled
    AUTO_REVERT_MODE: str = "create_and_merge_revert_pr"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
