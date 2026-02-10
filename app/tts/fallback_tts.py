from __future__ import annotations

import time

from app.tts.base import TTSProvider


class FallbackTTSProvider(TTSProvider):
    def __init__(self, primary: TTSProvider, fallback: TTSProvider, primary_name: str, fallback_name: str) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name
        self.last_status: dict = {
            'provider': fallback_name,
            'ok': True,
            'latency_ms': 0,
            'error': '',
            'fallback_used': False,
        }

    def synthesize(self, text: str, out_path: str) -> str:
        start = time.time()
        try:
            result = self.primary.synthesize(text, out_path)
            self.last_status = {
                'provider': self.primary_name,
                'ok': True,
                'latency_ms': int((time.time() - start) * 1000),
                'error': '',
                'fallback_used': False,
            }
            return result
        except Exception as exc:
            result = self.fallback.synthesize(text, out_path)
            self.last_status = {
                'provider': self.fallback_name,
                'ok': True,
                'latency_ms': int((time.time() - start) * 1000),
                'error': f'primary failed: {exc}',
                'fallback_used': True,
            }
            return result
