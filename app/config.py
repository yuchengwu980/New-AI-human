from functools import lru_cache
from pathlib import Path

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
