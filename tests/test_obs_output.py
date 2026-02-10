from app.integrations.obs_output import OBSConfig, OBSOutputter


class FakeOBSClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []

    def get_version(self):
        return {'obsVersion': 'fake'}

    def set_input_settings(self, source, settings, overlay):
        self.calls.append(('set_input_settings', source, settings, overlay))

    def trigger_media_input_action(self, source, action):
        self.calls.append(('trigger_media_input_action', source, action))


def test_obs_connect_and_test():
    outputter = OBSOutputter(client_factory=lambda **kwargs: FakeOBSClient(**kwargs))
    outputter.set_config(OBSConfig(enabled=True))

    ok, _ = outputter.connect()
    assert ok is True

    ok, msg = outputter.test()
    assert ok is True
    assert '连通成功' in msg


def test_obs_push_skips_when_disabled(tmp_path):
    outputter = OBSOutputter(client_factory=lambda **kwargs: FakeOBSClient(**kwargs))
    outputter.set_config(OBSConfig(enabled=False))
    ok, msg = outputter.push_event('hello', str(tmp_path / 'x.wav'))
    assert ok is False
    assert '未启用' in msg
