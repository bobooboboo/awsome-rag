from app.model.chat_model import get_chat_model
from app.query_processing.query_pre.base_processor import BasePreQueryProcessor


class QuestionOptimizerProcessor(BasePreQueryProcessor):
    def __init__(self, system_prompt: str = None):
        self.system_prompt = system_prompt or (
            "请将用户的问题改写为更完整、更具体、更适合知识库检索的问题，只返回改写后的问句，不要添加说明。"
        )

    def run(self, query: str) -> str:
        try:
            chat_model = get_chat_model()
            prompt = f"{self.system_prompt}\n\n用户问题：{query}"
            result = chat_model.generate(prompt)
            return result.strip()
        except Exception as e:
            print(f"[QuestionOptimizer] 生成失败: {e}")
            return query