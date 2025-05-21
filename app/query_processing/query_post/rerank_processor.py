from typing import List
from llama_index.core.schema import NodeWithScore, QueryBundle
from app.model.rerank_model import get_rerank_model
from app.query_processing.query_post.base_processor import BaseProcessor


class RerankProcessor(BaseProcessor):
    """
    使用重排模型（本地或阿里云）对候选节点进行排序
    """

    def __init__(self):
        self.reranker = get_rerank_model()

    def apply(self, nodes: List[NodeWithScore], query_bundle: QueryBundle) -> List[NodeWithScore]:
        return self.reranker.postprocess_nodes(nodes, query_bundle)
