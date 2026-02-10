from app.config import Settings
from app.dialogue.scripts import ScriptLibrary
from app.tts.base import TTSProvider
from app.tts.fallback_tts import FallbackTTSProvider
from app.tts.openai_tts import OpenAITTSProvider
from app.tts.silent_wav import SilentWavTTS


def build_script_library(settings: Settings) -> ScriptLibrary:
    return ScriptLibrary(
        llm_provider=settings.llm_provider,
        openai_api_key=settings.llm_openai_api_key,
        openai_model=settings.llm_openai_model,
        openai_timeout_seconds=settings.llm_openai_timeout_seconds,
    )


def build_tts_provider(settings: Settings) -> TTSProvider:
    fallback = SilentWavTTS()
    if settings.tts_provider == 'openai':
        primary = OpenAITTSProvider(
            api_key=settings.tts_openai_api_key,
            model=settings.tts_openai_model,
            voice=settings.tts_openai_voice,
            timeout_seconds=settings.tts_openai_timeout_seconds,
        )
        return FallbackTTSProvider(primary, fallback, primary_name='openai_tts', fallback_name='silent_wav')
    return FallbackTTSProvider(fallback, fallback, primary_name='silent_wav', fallback_name='silent_wav')
