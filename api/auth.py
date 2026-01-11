from fastapi import Header, HTTPException
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = "change-me"
    allow_no_auth: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def require_api_key(x_api_key: str | None = Header(default=None)):
    if settings.allow_no_auth:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
