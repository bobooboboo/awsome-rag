from typing import List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle

from app.model.rerank_model import get_rerank_model


class RerankProcessor(BaseNodePostprocessor):
    """
    使用重排模型（本地或阿里云）对候选节点进行排序
    """

    def __init__(self):
        super().__init__()
        self._reranker = None

    @property 
    def reranker(self):
        """延迟初始化重排模型"""
        if self._reranker is None:
            self._reranker = get_rerank_model()
        return self._reranker

    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None) -> List[
        NodeWithScore]:
        return self.reranker.postprocess_nodes(nodes, query_bundle)
