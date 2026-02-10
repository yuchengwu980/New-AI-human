import json
from datetime import datetime
from pathlib import Path

from app.models import Event


class OutputWriter:
    def __init__(self, audio_dir: str, events_dir: str, last_event_file: str) -> None:
        self.audio_dir = Path(audio_dir)
        self.events_dir = Path(events_dir)
        self.last_event_file = Path(last_event_file)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)

    def write_event(self, event: Event) -> None:
        payload = event.model_dump()
        self.last_event_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        history_file = self.events_dir / f"history_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with history_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
