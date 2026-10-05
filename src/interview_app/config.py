from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # "openrouter" for real calls, "fake" for a scripted interviewer/judge (no key, no network)
    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    llm_model: str = "google/gemma-4-31b-it:free"
    jev_model: str = "typesafe/jev-1.13"
    # Guard 1: the cheap model that checks every Answer for being off-topic, whatever the Interviewer Model
    off_topic_model: str = "openai/gpt-5-nano"
    # Guard 2: dollars a day; once OpenRouter counts this much spent today, no new Interview starts
    daily_budget: float = 2.0
    # Voice Interviews: an audio chat model for both directions (ADR-0005)
    stt_model: str = "openai/gpt-audio-mini"
    tts_model: str = "openai/gpt-audio-mini"
    image_model: str = "google/gemini-2.5-flash-image"
    database_url: str = "sqlite:///./interview.db"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
