import importlib
import sys
import types


class FakeComment:
    def __init__(self, user_id: str, text: str, ts: float, msg_id=None, source='mock', raw=None):
        self.user_id = user_id
        self.text = text
        self.ts = ts
        self.msg_id = msg_id
        self.source = source
        self.raw = raw


def _load_adapter_without_pydantic():
    """Load input_adapter with a lightweight fake app.models.Comment.

    This keeps the parser test runnable even when pydantic is unavailable in CI.
    Runtime still uses real app.models.Comment in normal environments.
    """
    fake_models = types.ModuleType('app.models')
    fake_models.Comment = FakeComment
    sys.modules['app.models'] = fake_models

    if 'app.integrations.input_adapter' in sys.modules:
        del sys.modules['app.integrations.input_adapter']

    return importlib.import_module('app.integrations.input_adapter')


def test_http_payload_mapping_with_msg_id():
    adapter = _load_adapter_without_pydantic()
    c = adapter.from_http_payload({'user_id': 'u1', 'text': '你好', 'msg_id': 'm1'})
    assert c.user_id == 'u1'
    assert c.text == '你好'
    assert c.msg_id == 'm1'


def test_file_line_json_mapping():
    adapter = _load_adapter_without_pydantic()
    c = adapter.from_file_line('{"user_id":"u2","text":"问价格","msg_id":"m2"}')
    assert c.user_id == 'u2'
    assert c.msg_id == 'm2'


def test_file_line_pipe_mapping():
    adapter = _load_adapter_without_pydantic()
    c = adapter.from_file_line('u3|问功能|1730000002|m3')
    assert c.user_id == 'u3'
    assert c.text == '问功能'
    assert c.msg_id == 'm3'
