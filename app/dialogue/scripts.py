from app.utils.paths import resource_path


class ScriptLibrary:
    def __init__(self, idle_path: str = 'scripts/idle_lines_zh.txt', reply_path: str = 'scripts/reply_templates_zh.txt') -> None:
        self.idle_lines = self._load_lines(idle_path)
        self.reply_templates = self._load_reply_templates(reply_path)

    @staticmethod
    def _load_lines(path: str) -> list[str]:
        p = resource_path(path)
        if not p.exists():
            return ['欢迎来到直播间，我们正在准备中。']
        return [line.strip() for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]

    @staticmethod
    def _load_reply_templates(path: str) -> dict[str, str]:
        p = resource_path(path)
        defaults = {
            'greeting': '你好，欢迎来到数字人操作平台演示。',
            'price': '关于价格，我们有基础版和专业版，欢迎私信了解详细方案。',
            'feature': '当前支持评论接入、分类、状态机和TTS占位输出。',
            'other': '收到你的评论啦，我们会尽快回复你。',
        }
        if not p.exists():
            return defaults
        loaded = {}
        for line in p.read_text(encoding='utf-8').splitlines():
            if not line.strip() or '=' not in line:
                continue
            key, value = line.split('=', 1)
            loaded[key.strip()] = value.strip()
        return {**defaults, **loaded}

    def build_reply(self, category: str, user_text: str) -> str:
        template = self.reply_templates.get(category, self.reply_templates['other'])
        return template.replace('{user_text}', user_text)
