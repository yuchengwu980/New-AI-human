import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.dialogue.scripts import ScriptLibrary
from app.dialogue.state_machine import DialogueStateMachine
from app.models import Comment
from app.outputs.writer import OutputWriter
from app.pipeline.orchestrator import PipelineOrchestrator
from app.sources.mock_source import MockSource
from app.sources.platform_api import PlatformApiSource
from app.tts.silent_wav import SilentWavTTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()
mock_source = MockSource()
platform_source = PlatformApiSource(settings)
script_lib = ScriptLibrary()
state_machine = DialogueStateMachine(script_lib, cooldown_seconds=settings.cooldown_seconds)
writer = OutputWriter(settings.audio_dir, settings.events_dir, settings.last_event_file)
orchestrator = PipelineOrchestrator(settings, state_machine, SilentWavTTS(), writer)
idle_task: asyncio.Task | None = None

templates = Jinja2Templates(directory='app/ui/templates')


async def idle_loop() -> None:
    while True:
        await asyncio.sleep(settings.idle_interval_seconds)
        orchestrator.emit_idle_if_due()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global idle_task
    await mock_source.start(orchestrator.handle_comment)
    await platform_source.start(orchestrator.handle_comment)
    idle_task = asyncio.create_task(idle_loop())
    logger.info('Application started with source_type=%s', settings.source_type)
    yield
    if idle_task:
        idle_task.cancel()
    await mock_source.stop()
    await platform_source.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount('/static', StaticFiles(directory='app/ui/static'), name='static')


@app.get('/health')
def health() -> dict:
    return {'ok': True, 'app': settings.app_name, 'time': time.time()}


@app.post('/api/mock/push')
def push_mock(comment: Comment) -> dict:
    if comment.source != 'mock':
        comment.source = 'mock'
    decision = orchestrator.handle_comment(comment)
    return {
        'accepted': decision.accepted,
        'category': decision.category,
        'action': decision.action,
        'dedup_hit': decision.dedup_hit,
        'ratelimit_hit': decision.ratelimit_hit,
        'reason': decision.reason,
    }


@app.get('/api/ui/state')
def ui_state() -> dict:
    last_event_path = Path(settings.last_event_file)
    last_event = {}
    if last_event_path.exists():
        last_event = json.loads(last_event_path.read_text(encoding='utf-8'))
    return {
        'recent': list(orchestrator.recent),
        'last_event': last_event,
    }


@app.get('/ui', response_class=HTMLResponse)
def ui(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.host, port=settings.port, reload=False)
