from app.dialogue.scripts import ScriptLibrary
from app.dialogue.state_machine import DialogueStateMachine


def test_state_machine_transition():
    s = ScriptLibrary()
    sm = DialogueStateMachine(s, cooldown_seconds=1)
    res = sm.on_comment('greeting', '你好')
    assert res.event_type == 'reply'
    assert res.text is not None
    sm.enter_cooldown()
    assert sm.state == 'cooldown'
