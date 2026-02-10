from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.models import Comment


def from_http_payload(payload: dict[str, Any]) -> Comment:
    user_id = str(payload.get('user_id', '')).strip()
    text = str(payload.get('text', '')).strip()
    if not user_id or not text:
        raise ValueError('missing user_id/text')

    ts_raw = payload.get('ts')
    ts = float(ts_raw) if ts_raw is not None else time.time()
    msg_id = str(payload.get('msg_id')) if payload.get('msg_id') is not None else None
    source = 'platform_api' if payload.get('source') == 'platform_api' else 'mock'

    return Comment(
        user_id=user_id,
        text=text,
        ts=ts,
        msg_id=msg_id,
        source=source,
        raw=payload,
    )


def from_file_line(line: str, default_source: str = 'mock') -> Comment:
    """Parse a file-appended line into internal Comment.

    Accepted formats:
    1) JSON object line: {"user_id":"u1","text":"你好","ts":...,"msg_id":"m1"}
    2) Pipe format: user_id|text|ts|msg_id
    """
    line = line.strip()
    if not line:
        raise ValueError('empty line')

    try:
        obj: dict[str, Any] = json.loads(line)
        if 'source' not in obj:
            obj['source'] = default_source
        return from_http_payload(obj)
    except json.JSONDecodeError:
        parts = line.split('|')
        if len(parts) < 2:
            raise ValueError('invalid line format')
        payload: dict[str, Any] = {
            'user_id': parts[0].strip(),
            'text': parts[1].strip(),
            'source': default_source,
        }
        if len(parts) >= 3 and parts[2].strip():
            payload['ts'] = float(parts[2])
        if len(parts) >= 4 and parts[3].strip():
            payload['msg_id'] = parts[3].strip()
        comment = from_http_payload(payload)
        comment.raw = {'line': line}
        return comment


def read_appended_lines(file_path: Path, offset: int) -> tuple[list[str], int]:
    if not file_path.exists():
        return [], offset
    with file_path.open('r', encoding='utf-8') as f:
        f.seek(offset)
        lines = f.readlines()
        new_offset = f.tell()
    return lines, new_offset
