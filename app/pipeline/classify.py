
class RuleClassifier:
    CATEGORY_RULES = {
        'greeting': ['你好', 'hello', 'hi', '在吗', '哈喽'],
        'price': ['多少钱', '价格', '费用', '套餐', '报价'],
        'feature': ['功能', '支持', '怎么用', '可以', '能否'],
    }

    def classify(self, text: str) -> str:
        lower = text.lower()
        for category, keywords in self.CATEGORY_RULES.items():
            if any(kw in lower for kw in keywords):
                return category
        return 'other'
