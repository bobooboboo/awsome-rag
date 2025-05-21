from typing import List
from llama_index.core.schema import NodeWithScore, QueryBundle

from app.query_processing.query_post.base_processor import BaseProcessor


class PostProcessorChain:
    """
    多个后处理器串联执行的容器
    """

    def __init__(self, processors: List[BaseProcessor]):
        self.processors = processors

    def run(self, nodes: List[NodeWithScore], query: str) -> List[NodeWithScore]:
        bundle = QueryBundle(query_str=query)
        for processor in self.processors:
            nodes = processor.apply(nodes, bundle)
        return nodes
