import wave
from array import array

from app.tts.base import TTSProvider


class SilentWavTTS(TTSProvider):
    def __init__(self, duration_seconds: float = 1.2, sample_rate: int = 16000) -> None:
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate

    def synthesize(self, text: str, out_path: str) -> str:
        nframes = int(self.duration_seconds * self.sample_rate)
        samples = array('h', [0] * nframes)
        with wave.open(out_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(samples.tobytes())
        return out_path
