from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = Field(min_length=32)
    token_minutes: int = Field(default=30, ge=1, le=1440)
    group_name: str = 'Grupo Scout Horizonte'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
