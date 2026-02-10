from functools import lru_cache
from pathlib import Path

from app.utils.paths import runtime_path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Digital Human Controller MVP'
    host: str = '0.0.0.0'
    port: int = 8000
    log_level: str = 'INFO'

    source_type: str = 'mock'
    dedup_ttl_seconds: int = 60
    user_rate_limit_seconds: int = 10
    global_rate_window_seconds: int = 1
    global_rate_max: int = 3
    idle_interval_seconds: int = 8
    cooldown_seconds: int = 2
    ui_recent_limit: int = 20

    output_dir: str = 'output'
    audio_dir: str = 'output/audio'
    events_dir: str = 'output/events'
    last_event_file: str = 'output/events/last_event.json'


    llm_provider: str = 'mock'
    llm_openai_api_key: str = ''
    llm_openai_model: str = 'gpt-4o-mini'
    llm_openai_timeout_seconds: int = 10

    tts_provider: str = 'silent'
    tts_openai_api_key: str = ''
    tts_openai_model: str = 'gpt-4o-mini-tts'
    tts_openai_voice: str = 'alloy'
    tts_openai_timeout_seconds: int = 10

    platform_api_enabled: bool = False
    platform_type: str = 'generic'
    platform_poll_interval: int = 2
    platform_base_url: str = ''
    platform_api_key: str = ''
    platform_token: str = ''
    platform_room_id: str = ''
    platform_stream_id: str = ''
    platform_use_websocket: bool = False

    def ensure_dirs(self) -> None:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.audio_dir).mkdir(parents=True, exist_ok=True)
        Path(self.events_dir).mkdir(parents=True, exist_ok=True)

    def resolve_runtime_paths(self) -> None:
        self.output_dir = str(runtime_path(self.output_dir))
        self.audio_dir = str(runtime_path(self.audio_dir))
        self.events_dir = str(runtime_path(self.events_dir))
        self.last_event_file = str(runtime_path(self.last_event_file))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.resolve_runtime_paths()
    settings.ensure_dirs()
    return settings
