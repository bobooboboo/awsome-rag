from typing import Dict, Optional

from llama_index.core.indices.query.query_transform.base import BaseQueryTransform
from llama_index.core.prompts.mixin import PromptDictType
from llama_index.core.schema import QueryBundle

from app.query_processing.query_pre.pre_query_chain import PreQueryProcessorChain
from app.query_processing.query_pre.question_optimization_processor import QuestionOptimizerProcessor
from app.query_processing.query_pre.sensitive_word_processor import SensitiveWordProcessor


class LlamaIndexQueryTransformAdapter(BaseQueryTransform):
    """
    将 query_pre 的链式处理器适配为 LlamaIndex 的 QueryTransform
    """

    def __init__(self):
        self.chain = PreQueryProcessorChain(processors=[
            SensitiveWordProcessor(),
            QuestionOptimizerProcessor()
            # 更多前处理器可加入此处
        ])

    def _run(self, query_bundle: QueryBundle, metadata: Optional[Dict] = None) -> QueryBundle:
        original_query = query_bundle.query_str
        processed_query = self.chain.run(original_query)
        return QueryBundle(query_str=processed_query)

    def _get_prompts(self) -> PromptDictType:
        """无需使用 prompt，因此返回空 dict"""
        return {}

    def _update_prompts(self, prompts_dict: PromptDictType) -> None:
        """无需更新 prompt，直接忽略"""
        pass


if __name__ == '__main__':
    # 查询前置处理
    optimized_query = LlamaIndexQueryTransformAdapter().chain.run("敏感词中国汽车品牌")

    print(optimized_query)

    # 构建query_bundle
    # query_bundle = QueryBundle(query_str=optimized_query)

    # # 检索召回节点
    # nodes = get_retriever().retrieve(query_bundle)
    #
    # # 4. 查询后置处理
    # processed_nodes = post_chain.run(nodes, optimized_query)
    #
    # # 5. 返回结构化结果
    # return {
    #     "original_query": raw_query,
    #     "optimized_query": optimized_query,
    #     "results": [
    #         {
    #             "text": n.node.get_content(),
    #             "score": n.score,
    #             "ref_doc_id": n.node.ref_doc_id,  # 如果有
    #             "metadata": n.node.metadata
    #         } for n in processed_nodes
    #     ]
    # }
