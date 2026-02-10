from pathlib import Path

from app.config import Settings
from app.desktop.api import DesktopController


def test_desktop_process_comment_writes_event(tmp_path):
    out = tmp_path / 'output'
    settings = Settings(
        output_dir=str(out),
        audio_dir=str(out / 'audio'),
        events_dir=str(out / 'events'),
        last_event_file=str(out / 'events' / 'last_event.json'),
    )
    settings.ensure_dirs()
    controller = DesktopController(settings=settings)

    result = controller.process_comment(user_id='u1', text='你好')

    assert result['category'] in {'greeting', 'price', 'feature', 'other'}
    assert Path(result['audio_path']).exists()
    assert Path(settings.last_event_file).exists()
    assert 'event_json' in result


def test_desktop_generate_idle_line(tmp_path):
    out = tmp_path / 'output'
    settings = Settings(
        output_dir=str(out),
        audio_dir=str(out / 'audio'),
        events_dir=str(out / 'events'),
        last_event_file=str(out / 'events' / 'last_event.json'),
        cooldown_seconds=0,
    )
    settings.ensure_dirs()
    controller = DesktopController(settings=settings)

    result = controller.generate_idle_line()

    assert result['type'] in {'idle_line', 'reply', ''}
    assert Path(settings.last_event_file).exists()
