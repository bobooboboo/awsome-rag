from app.query_processing.query_pre.base_processor import BasePreQueryProcessor


class SensitiveWordProcessor(BasePreQueryProcessor):
    def run(self, query: str) -> str:
        sensitive_words = ["非法词", "敏感词"]
        for word in sensitive_words:
            query = query.replace(word, "")
        return query
