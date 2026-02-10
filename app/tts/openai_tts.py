from __future__ import annotations

import time
from pathlib import Path

from app.tts.base import TTSProvider


class OpenAITTSProvider(TTSProvider):
    def __init__(self, api_key: str, model: str = 'gpt-4o-mini-tts', voice: str = 'alloy', timeout_seconds: int = 10) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.timeout_seconds = timeout_seconds
        self.last_status: dict = {'provider': 'openai_tts', 'ok': False, 'latency_ms': 0, 'error': 'not_called'}

    def synthesize(self, text: str, out_path: str) -> str:
        start = time.time()
        import requests

        if not self.api_key:
            raise RuntimeError('openai tts api_key is empty')

        url = 'https://api.openai.com/v1/audio/speech'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'voice': self.voice,
            'input': text or '你好',
            'format': 'wav',
        }
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        if response.status_code >= 400:
            raise RuntimeError(f'openai tts http {response.status_code}: {response.text[:200]}')

        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(response.content)
        self.last_status = {
            'provider': 'openai_tts',
            'ok': True,
            'latency_ms': int((time.time() - start) * 1000),
            'error': '',
        }
        return out_path
