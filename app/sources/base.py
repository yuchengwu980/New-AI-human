from abc import ABC, abstractmethod
from collections.abc import Callable

from app.models import Comment

CommentCallback = Callable[[Comment], None]


class SourceAdapter(ABC):
    @abstractmethod
    async def start(self, on_comment: CommentCallback) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
