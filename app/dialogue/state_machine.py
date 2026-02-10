import itertools
import time
from dataclasses import dataclass
from typing import Literal

from app.dialogue.scripts import ScriptLibrary

StateName = Literal['idle', 'engage', 'speak', 'cooldown']


@dataclass
class StateResult:
    state: StateName
    text: str | None = None
    event_type: Literal['idle_line', 'reply'] | None = None


class DialogueStateMachine:
    def __init__(self, script_library: ScriptLibrary, cooldown_seconds: int = 2) -> None:
        self._scripts = script_library
        self.state: StateName = 'idle'
        self.cooldown_seconds = cooldown_seconds
        self._cooldown_until = 0.0
        self._idle_cycle = itertools.cycle(self._scripts.idle_lines)

    def next_idle_line(self) -> StateResult:
        if self.state == 'cooldown' and time.time() < self._cooldown_until:
            return StateResult(state='cooldown')
        self.state = 'idle'
        return StateResult(state='speak', text=next(self._idle_cycle), event_type='idle_line')

    def on_comment(self, category: str, user_text: str) -> StateResult:
        self.state = 'engage'
        reply = self._scripts.build_reply(category, user_text)
        self.state = 'speak'
        return StateResult(state='speak', text=reply, event_type='reply')

    def enter_cooldown(self) -> None:
        self.state = 'cooldown'
        self._cooldown_until = time.time() + self.cooldown_seconds
