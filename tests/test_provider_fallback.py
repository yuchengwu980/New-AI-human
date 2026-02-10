from app.dialogue.scripts import ScriptLibrary
from app.tts.fallback_tts import FallbackTTSProvider
from app.tts.silent_wav import SilentWavTTS


class BrokenTTS:
    def synthesize(self, text: str, out_path: str) -> str:
        raise RuntimeError('boom')


def test_llm_fallback_to_mock_when_no_key():
    s = ScriptLibrary(llm_provider='openai', openai_api_key='')
    text = s.build_reply('greeting', '你好')
    assert text
    assert s.last_llm_status['fallback_used'] is True


def test_tts_fallback_provider(tmp_path):
    out = tmp_path / 'x.wav'
    provider = FallbackTTSProvider(BrokenTTS(), SilentWavTTS(), primary_name='broken', fallback_name='silent_wav')
    provider.synthesize('hello', str(out))
    assert out.exists()
    assert provider.last_status['fallback_used'] is True
