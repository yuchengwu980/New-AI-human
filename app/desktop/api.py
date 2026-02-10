import json
import time
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.dialogue.scripts import ScriptLibrary
from app.dialogue.state_machine import DialogueStateMachine
from app.models import Comment
from app.outputs.writer import OutputWriter
from app.pipeline.orchestrator import PipelineOrchestrator
from app.tts.silent_wav import SilentWavTTS


class DesktopController:
    """Desktop-facing local API (no HTTP)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        script_lib = ScriptLibrary()
        self.state_machine = DialogueStateMachine(script_lib, cooldown_seconds=self.settings.cooldown_seconds)
        writer = OutputWriter(self.settings.audio_dir, self.settings.events_dir, self.settings.last_event_file)
        self.orchestrator = PipelineOrchestrator(self.settings, self.state_machine, SilentWavTTS(), writer)

    @property
    def mode(self) -> str:
        if self.settings.platform_api_enabled:
            return f'PlatformApi({self.settings.platform_type})'
        return 'Mock'

    def process_comment(self, user_id: str, text: str) -> dict[str, Any]:
        comment = Comment(user_id=user_id, text=text, ts=time.time(), source='mock')
        decision = self.orchestrator.handle_comment(comment)
        latest = self.orchestrator.recent[0] if self.orchestrator.recent else {}
        return self._build_result(decision=latest.get('decision', {}), output=latest.get('output', {}), fallback_category=decision.category)

    def generate_idle_line(self) -> dict[str, Any]:
        self.orchestrator.emit_idle_if_due()
        event_json = self._read_last_event()
        return {
            'category': event_json.get('meta', {}).get('category', 'idle'),
            'dedup_hit': False,
            'ratelimit_hit': False,
            'reply_text': event_json.get('text', ''),
            'audio_path': event_json.get('audio_path', ''),
            'event_json': event_json,
            'event_id': event_json.get('event_id', ''),
            'type': event_json.get('type', ''),
        }

    def get_log_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in self.orchestrator.recent:
            comment = row.get('comment', {})
            decision = row.get('decision', {})
            output = row.get('output', {}) or {}
            records.append(
                {
                    'time': row.get('ts', 0),
                    'user_id': comment.get('user_id', ''),
                    'text': comment.get('text', ''),
                    'category': decision.get('category', 'other'),
                    'dedup_hit': decision.get('dedup_hit', False),
                    'ratelimit_hit': decision.get('ratelimit_hit', False),
                    'reply_text': output.get('text', ''),
                    'audio_path': output.get('audio_path', ''),
                    'decision': decision,
                    'comment': comment,
                }
            )
        return records

    def get_event_json(self) -> dict[str, Any]:
        return self._read_last_event()

    def _build_result(self, decision: dict[str, Any], output: dict[str, Any], fallback_category: str) -> dict[str, Any]:
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
        }

    def _read_last_event(self) -> dict[str, Any]:
        path = Path(self.settings.last_event_file)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding='utf-8'))
