from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "adhd-coach-api"
    debug: bool = True

    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    # Required for POST /internal/reminders/fire in production; stub allows missing for local dev
    internal_api_key: str | None = None

    # MongoDB Atlas — mongodb+srv://... (include DB name in path when you wire persistence)
    mongodb_uri: str | None = None

    # Google Gen AI (Gemini) — used by google-genai SDK; optional until routes call the model
    gemini_api_key: str | None = None

    # Twilio WhatsApp (T3 coordinates console; values live on server env in prod)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


def cors_origin_list() -> list[str]:
    return [o.strip() for o in get_settings().cors_origins.split(",") if o.strip()]
