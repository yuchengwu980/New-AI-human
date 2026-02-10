import json
import logging
import time
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.dialogue.state_machine import DialogueStateMachine
from app.integrations.obs_output import OBSConfig, OBSOutputter
from app.models import Comment
from app.outputs.writer import OutputWriter
from app.pipeline.orchestrator import PipelineOrchestrator
from app.providers.factory import build_script_library, build_tts_provider

logger = logging.getLogger(__name__)


class DesktopController:
    """Desktop-facing local API (no HTTP)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.script_lib = build_script_library(self.settings)
        self.state_machine = DialogueStateMachine(self.script_lib, cooldown_seconds=self.settings.cooldown_seconds)
        writer = OutputWriter(self.settings.audio_dir, self.settings.events_dir, self.settings.last_event_file)
        self.tts_provider = build_tts_provider(self.settings)
        self.orchestrator = PipelineOrchestrator(self.settings, self.state_machine, self.tts_provider, writer)
        self.obs = OBSOutputter()

    @property
    def mode(self) -> str:
        if self.settings.platform_api_enabled:
            return f'PlatformApi({self.settings.platform_type})'
        return 'Mock'

    def set_provider_config(
        self,
        llm_provider: str,
        llm_api_key: str,
        llm_model: str,
        llm_timeout: int,
        tts_provider: str,
        tts_api_key: str,
        tts_model: str,
        tts_voice: str,
        tts_timeout: int,
    ) -> None:
        self.settings.llm_provider = llm_provider
        self.settings.llm_openai_api_key = llm_api_key
        self.settings.llm_openai_model = llm_model
        self.settings.llm_openai_timeout_seconds = llm_timeout

        self.settings.tts_provider = tts_provider
        self.settings.tts_openai_api_key = tts_api_key
        self.settings.tts_openai_model = tts_model
        self.settings.tts_openai_voice = tts_voice
        self.settings.tts_openai_timeout_seconds = tts_timeout

        self.script_lib.set_llm_provider(
            provider=llm_provider,
            api_key=llm_api_key,
            model=llm_model,
            timeout_seconds=llm_timeout,
        )
        self.tts_provider = build_tts_provider(self.settings)
        self.orchestrator.tts = self.tts_provider

    def get_provider_status(self) -> dict[str, Any]:
        tts_status = getattr(self.tts_provider, 'last_status', {'provider': 'unknown', 'ok': False, 'error': 'no_status'})
        llm_status = getattr(self.script_lib, 'last_llm_status', {'provider': 'unknown', 'ok': False, 'error': 'no_status'})
        return {'llm': llm_status, 'tts': tts_status}

    def set_obs_config(self, host: str, port: int, password: str, subtitle_source: str, audio_source: str, enabled: bool) -> None:
        self.obs.set_config(
            OBSConfig(
                host=host,
                port=port,
                password=password,
                subtitle_source=subtitle_source,
                audio_source=audio_source,
                enabled=enabled,
            )
        )

    def connect_obs(self) -> tuple[bool, str]:
        ok, msg = self.obs.connect()
        logger.info('OBS connect result: %s - %s', ok, msg)
        return ok, msg

    def test_obs(self) -> tuple[bool, str]:
        ok, msg = self.obs.test()
        logger.info('OBS test result: %s - %s', ok, msg)
        return ok, msg

    def process_comment(self, user_id: str, text: str) -> dict[str, Any]:
        comment = Comment(user_id=user_id, text=text, ts=time.time(), source='mock')
        return self.process_external_comment(comment)

    def process_external_comment(self, comment: Comment) -> dict[str, Any]:
        decision = self.orchestrator.handle_comment(comment)
        latest = self.orchestrator.recent[0] if self.orchestrator.recent else {}
        result = self._build_result(
            decision=latest.get('decision', {}),
            output=latest.get('output', {}),
            fallback_category=decision.category,
            msg_id=comment.msg_id,
        )
        self._sync_to_obs(result)
        return result

    def generate_idle_line(self) -> dict[str, Any]:
        self.orchestrator.emit_idle_if_due()
        event_json = self._read_last_event()
        result = {
            'category': event_json.get('meta', {}).get('category', 'idle'),
            'dedup_hit': False,
            'ratelimit_hit': False,
            'reply_text': event_json.get('text', ''),
            'audio_path': event_json.get('audio_path', ''),
            'event_json': event_json,
            'event_id': event_json.get('event_id', ''),
            'type': event_json.get('type', ''),
            'msg_id': None,
            'obs_result': '',
            'provider_status': self.get_provider_status(),
        }
        self._sync_to_obs(result)
        return result

    def get_event_json(self) -> dict[str, Any]:
        return self._read_last_event()

    def _build_result(self, decision: dict[str, Any], output: dict[str, Any], fallback_category: str, msg_id: str | None) -> dict[str, Any]:
        event_json = self._read_last_event()
        return {
            'category': decision.get('category', fallback_category),
            'dedup_hit': decision.get('dedup_hit', False),
            'ratelimit_hit': decision.get('ratelimit_hit', False),
            'reply_text': output.get('text', ''),
            'audio_path': output.get('audio_path', ''),
            'event_json': event_json,
            'event_id': event_json.get('event_id', ''),
            'type': event_json.get('type', ''),
            'msg_id': msg_id,
            'obs_result': '',
            'provider_status': self.get_provider_status(),
        }

    def _sync_to_obs(self, result: dict[str, Any]) -> None:
        try:
            ok, msg = self.obs.push_event(result.get('reply_text', ''), result.get('audio_path', ''))
            result['obs_result'] = msg
            logger.info('OBS sync result: %s - %s', ok, msg)
        except Exception as exc:  # safety net, should never crash UI
            logger.exception('OBS sync crashed: %s', exc)
            result['obs_result'] = f'OBS同步异常: {exc}'

    def _read_last_event(self) -> dict[str, Any]:
        path = Path(self.settings.last_event_file)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding='utf-8'))
