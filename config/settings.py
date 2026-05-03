from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "MUP"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    SYMBOLS: List[str] = ["510300"]
    BASE_SYMBOL: str = "510300"
    
    TRADING_HOURS: dict = {
        "morning": {"start": "09:30", "end": "11:30"},
        "afternoon": {"start": "13:00", "end": "15:00"}
    }
    
    DATABASE_URL: str = "sqlite:///data/mup.db"
    
    TUSHARE_TOKEN: str = ""
    
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    DOUBAO_MODEL: str = ""
    
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    JQ_ACCOUNT: str = ""
    JQ_PASSWORD: str = ""
    
    INITIAL_CAPITAL: float = 10000.0
    
    LLM_PROVIDER: str = "doubao"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
