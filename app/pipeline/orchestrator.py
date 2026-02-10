import logging
import time
import uuid
from collections import deque
from pathlib import Path

from app.config import Settings
from app.dialogue.state_machine import DialogueStateMachine
from app.models import Comment, CommentDecision, Event
from app.outputs.writer import OutputWriter
from app.pipeline.classify import RuleClassifier
from app.pipeline.dedup import Deduplicator
from app.pipeline.ratelimit import RateLimiter
from app.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(
        self,
        settings: Settings,
        state_machine: DialogueStateMachine,
        tts: TTSProvider,
        writer: OutputWriter,
    ) -> None:
        self.settings = settings
        self.state_machine = state_machine
        self.tts = tts
        self.writer = writer
        self.dedup = Deduplicator(settings.dedup_ttl_seconds)
        self.ratelimiter = RateLimiter(
            user_window_seconds=settings.user_rate_limit_seconds,
            global_window_seconds=settings.global_rate_window_seconds,
            global_max=settings.global_rate_max,
        )
        self.classifier = RuleClassifier()
        self.recent: deque[dict] = deque(maxlen=settings.ui_recent_limit)

    def handle_comment(self, comment: Comment) -> CommentDecision:
        dedup_hit = self.dedup.hit(comment.user_id, comment.text)
        if dedup_hit:
            decision = CommentDecision(accepted=False, dedup_hit=True, action='drop', reason='duplicate')
            self._record_ui(comment, decision, None)
            return decision

        ratelimit_hit = self.ratelimiter.hit(comment.user_id)
        if ratelimit_hit:
            decision = CommentDecision(accepted=False, ratelimit_hit=True, action='drop', reason='rate_limited')
            self._record_ui(comment, decision, None)
            return decision

        category = self.classifier.classify(comment.text)
        state_result = self.state_machine.on_comment(category, comment.text)
        audio_path = self._speak(state_result.text or '', event_type='reply', source=comment.source, user_id=comment.user_id, category=category, dedup_hit=False, ratelimit_hit=False, raw=comment.raw)
        self.state_machine.enter_cooldown()
        decision = CommentDecision(accepted=True, category=category, action='reply_generated')
        self._record_ui(comment, decision, {'text': state_result.text, 'audio_path': audio_path})
        return decision

    def emit_idle_if_due(self) -> Event | None:
        state_result = self.state_machine.next_idle_line()
        if not state_result.text:
            return None
        self._speak(state_result.text, event_type='idle_line', source='mock', user_id=None, category='idle', dedup_hit=False, ratelimit_hit=False, raw=None)
        self.state_machine.enter_cooldown()
        return self.last_event()

    def _speak(self, text: str, event_type: str, source: str, user_id: str | None, category: str, dedup_hit: bool, ratelimit_hit: bool, raw: dict | None) -> str:
        filename = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}.wav"
        audio_path = str(Path(self.settings.audio_dir) / filename)
        self.tts.synthesize(text, audio_path)
        event = Event(
            event_id=uuid.uuid4().hex,
            ts=time.time(),
            type=event_type,
            text=text,
            audio_path=audio_path,
            source=source,
            meta={
                'user_id': user_id,
                'category': category,
                'dedup_hit': dedup_hit,
                'ratelimit_hit': ratelimit_hit,
                'raw': raw,
            },
        )
        self.writer.write_event(event)
        logger.info('Event generated: %s', event.model_dump())
        return audio_path

    def last_event(self) -> dict | None:
        path = Path(self.settings.last_event_file)
        if not path.exists():
            return None
        import json

        return json.loads(path.read_text(encoding='utf-8'))

    def _record_ui(self, comment: Comment, decision: CommentDecision, output: dict | None) -> None:
        self.recent.appendleft(
            {
                'comment': comment.model_dump(),
                'decision': decision.model_dump(),
                'output': output,
                'ts': time.time(),
            }
        )
