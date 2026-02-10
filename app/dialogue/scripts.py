import logging
import time

from app.utils.paths import resource_path

logger = logging.getLogger(__name__)


class ScriptLibrary:
    def __init__(
        self,
        idle_path: str = 'scripts/idle_lines_zh.txt',
        reply_path: str = 'scripts/reply_templates_zh.txt',
        llm_provider: str = 'mock',
        openai_api_key: str = '',
        openai_model: str = 'gpt-4o-mini',
        openai_timeout_seconds: int = 10,
    ) -> None:
        self.idle_lines = self._load_lines(idle_path)
        self.reply_templates = self._load_reply_templates(reply_path)
        self.llm_provider = llm_provider
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.openai_timeout_seconds = openai_timeout_seconds
        self.last_llm_status: dict = {
            'provider': llm_provider,
            'ok': True,
            'latency_ms': 0,
            'error': '',
            'fallback_used': False,
        }

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

    def set_llm_provider(self, provider: str, api_key: str, model: str, timeout_seconds: int) -> None:
        self.llm_provider = provider
        self.openai_api_key = api_key
        self.openai_model = model
        self.openai_timeout_seconds = timeout_seconds

    def build_reply(self, category: str, user_text: str) -> str:
        fallback = self._build_template_reply(category, user_text)
        if self.llm_provider != 'openai':
            self.last_llm_status = {'provider': 'mock', 'ok': True, 'latency_ms': 0, 'error': '', 'fallback_used': False}
            return fallback

        if not self.openai_api_key:
            self.last_llm_status = {
                'provider': 'openai',
                'ok': False,
                'latency_ms': 0,
                'error': 'missing api_key, fallback to mock',
                'fallback_used': True,
            }
            return fallback

        start = time.time()
        try:
            import requests

            prompt = (
                '你是直播间数字人助手，请根据分类和用户评论，给出一句自然、简短、中文回复。'
                f' 分类: {category}; 用户评论: {user_text}'
            )
            url = 'https://api.openai.com/v1/chat/completions'
            headers = {'Authorization': f'Bearer {self.openai_api_key}', 'Content-Type': 'application/json'}
            payload = {
                'model': self.openai_model,
                'messages': [
                    {'role': 'system', 'content': '请输出简洁中文口播文案，不超过60字。'},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0.7,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=self.openai_timeout_seconds)
            if resp.status_code >= 400:
                raise RuntimeError(f'openai http {resp.status_code}: {resp.text[:200]}')
            data = resp.json()
            text = data['choices'][0]['message']['content'].strip()
            if not text:
                raise RuntimeError('empty llm response')
            self.last_llm_status = {
                'provider': 'openai',
                'ok': True,
                'latency_ms': int((time.time() - start) * 1000),
                'error': '',
                'fallback_used': False,
            }
            return text
        except Exception as exc:
            logger.exception('OpenAI LLM failed, fallback mock: %s', exc)
            self.last_llm_status = {
                'provider': 'openai',
                'ok': False,
                'latency_ms': int((time.time() - start) * 1000),
                'error': str(exc),
                'fallback_used': True,
            }
            return fallback

    def _build_template_reply(self, category: str, user_text: str) -> str:
        template = self.reply_templates.get(category, self.reply_templates['other'])
        return template.replace('{user_text}', user_text)
