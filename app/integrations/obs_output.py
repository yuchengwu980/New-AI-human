from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class OBSConfig:
    host: str = '127.0.0.1'
    port: int = 4455
    password: str = ''
    subtitle_source: str = '字幕'
    audio_source: str = 'TTS音频'
    enabled: bool = False


class OBSOutputter:
    def __init__(self, client_factory: Callable[..., Any] | None = None) -> None:
        self._client_factory = client_factory
        self._client: Any | None = None
        self._config = OBSConfig()

    @property
    def config(self) -> OBSConfig:
        return self._config

    @property
    def connected(self) -> bool:
        return self._client is not None

    def set_config(self, config: OBSConfig) -> None:
        self._config = config

    def connect(self) -> tuple[bool, str]:
        if not self._config.enabled:
            self._client = None
            return False, 'OBS 输出未启用（enabled=false）'

        try:
            factory = self._client_factory or self._load_default_factory()
            self._client = factory(
                host=self._config.host,
                port=self._config.port,
                password=self._config.password,
                timeout=3,
            )
            return True, f'OBS 已连接: {self._config.host}:{self._config.port}'
        except Exception as exc:
            self._client = None
            logger.exception('OBS connect failed: %s', exc)
            return False, f'OBS 连接失败: {exc}'

    def test(self) -> tuple[bool, str]:
        if not self.connected:
            return False, 'OBS 未连接'
        try:
            if hasattr(self._client, 'get_version'):
                version = self._client.get_version()
                return True, f'OBS 连通成功: {version}'
            return True, 'OBS 连通成功'
        except Exception as exc:
            logger.exception('OBS test failed: %s', exc)
            return False, f'OBS 测试失败: {exc}'

    def push_event(self, text: str, audio_path: str) -> tuple[bool, str]:
        if not self._config.enabled:
            return False, 'OBS 未启用，已跳过推送'
        if not self.connected:
            return False, 'OBS 未连接，已跳过推送'

        messages: list[str] = []
        ok = True

        subtitle_ok, subtitle_msg = self._update_subtitle(text)
        ok = ok and subtitle_ok
        messages.append(subtitle_msg)

        audio_ok, audio_msg = self._play_audio(audio_path)
        ok = ok and audio_ok
        messages.append(audio_msg)

        return ok, ' | '.join(messages)

    def _update_subtitle(self, text: str) -> tuple[bool, str]:
        if not self._config.subtitle_source:
            return False, '未配置字幕源'
        try:
            self._client.set_input_settings(self._config.subtitle_source, {'text': text}, True)
            return True, f'字幕已更新: {self._config.subtitle_source}'
        except Exception as exc:
            logger.exception('OBS subtitle update failed: %s', exc)
            return False, f'字幕更新失败: {exc}'

    def _play_audio(self, audio_path: str) -> tuple[bool, str]:
        if not self._config.audio_source:
            return False, '未配置音频源'

        path = Path(audio_path)
        if not path.exists():
            return False, f'音频文件不存在: {audio_path}'

        try:
            self._client.set_input_settings(self._config.audio_source, {'local_file': str(path.resolve())}, True)
            # OBS websocket media action enum value
            self._client.trigger_media_input_action(
                self._config.audio_source,
                'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART',
            )
            return True, f'音频已触发: {self._config.audio_source}'
        except Exception as exc:
            logger.exception('OBS audio play failed: %s', exc)
            return False, f'音频触发失败: {exc}'

    @staticmethod
    def _load_default_factory() -> Callable[..., Any]:
        try:
            from obsws_python import ReqClient
        except Exception as exc:  # pragma: no cover
            raise RuntimeError('缺少 obsws-python 依赖，请先安装 requirements.txt') from exc
        return ReqClient
