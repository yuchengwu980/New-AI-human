import logging

from app.models import Comment
from app.sources.base import CommentCallback, SourceAdapter

logger = logging.getLogger(__name__)


class MockSource(SourceAdapter):
    def __init__(self) -> None:
        self._callback: CommentCallback | None = None

    async def start(self, on_comment: CommentCallback) -> None:
        self._callback = on_comment
        logger.info('MockSource started.')

    async def stop(self) -> None:
        logger.info('MockSource stopped.')

    def push_comment(self, comment: Comment) -> None:
        if self._callback:
            self._callback(comment)
