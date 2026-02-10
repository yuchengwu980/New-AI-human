from typing import Any, Literal

from pydantic import BaseModel, Field


class Comment(BaseModel):
    user_id: str
    text: str
    ts: float
    source: Literal['mock', 'platform_api'] = 'mock'
    msg_id: str | None = None
    raw: dict[str, Any] | None = None


class CommentDecision(BaseModel):
    accepted: bool
    dedup_hit: bool = False
    ratelimit_hit: bool = False
    category: str = 'other'
    action: str = 'drop'
    reason: str | None = None


class Event(BaseModel):
    event_id: str
    ts: float
    type: Literal['idle_line', 'reply']
    text: str
    audio_path: str
    source: Literal['mock', 'platform_api']
    meta: dict[str, Any] = Field(default_factory=dict)
