import contextlib
import asyncio
import logging

from app.config import Settings
from app.models import Comment
from app.sources.base import CommentCallback, SourceAdapter

logger = logging.getLogger(__name__)


class PlatformApiSource(SourceAdapter):
    """Skeleton adapter for future platform integration.

    TODO:
    1) Implement connect() for websocket/long-poll mode.
    2) Implement fetch_comments() for polling mode.
    3) Implement parse_response() to normalize platform payload.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._callback: CommentCallback | None = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self, on_comment: CommentCallback) -> None:
        self._callback = on_comment
        if not self.settings.platform_api_enabled:
            logger.info('PlatformApiSource disabled (platform_api_enabled=false).')
            return
        if not self._has_required_config():
            logger.error(
                'PlatformApiSource enabled but missing config. Need base_url and one of room_id/stream_id plus token/api_key.'
            )
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info('PlatformApiSource started in %s mode.', 'websocket' if self.settings.platform_use_websocket else 'polling')

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info('PlatformApiSource stopped.')

    async def _run_loop(self) -> None:
        while self._running:
            try:
                if self.settings.platform_use_websocket:
                    await self.connect()
                else:
                    payload = await self.fetch_comments()
                    comments = self.parse_response(payload)
                    for c in comments:
                        if self._callback:
                            self._callback(c)
            except Exception as exc:
                logger.exception('PlatformApiSource polling failed: %s', exc)
            await asyncio.sleep(self.settings.platform_poll_interval)

    def _has_required_config(self) -> bool:
        has_auth = bool(self.settings.platform_token or self.settings.platform_api_key)
        has_stream = bool(self.settings.platform_room_id or self.settings.platform_stream_id)
        return bool(self.settings.platform_base_url) and has_auth and has_stream

    async def fetch_comments(self) -> list[dict]:
        logger.info('TODO: implement fetch_comments() for platform type: %s', self.settings.platform_type)
        return []

    async def connect(self) -> None:
        logger.info('TODO: implement connect() websocket/long-poll for platform type: %s', self.settings.platform_type)

    def parse_response(self, payload: list[dict]) -> list[Comment]:
        normalized: list[Comment] = []
        for item in payload:
            normalized.append(
                Comment(
                    user_id=str(item.get('user_id', 'unknown')),
                    text=str(item.get('text', '')),
                    ts=float(item.get('ts', 0)),
                    source='platform_api',
                    raw=item,
                )
            )
        return normalized
