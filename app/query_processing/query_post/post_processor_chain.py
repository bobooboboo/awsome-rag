from typing import List

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore


class PostProcessorChain:
    """
    多个后处理器串联执行的容器
    """

    def __init__(self, processors: List[BaseNodePostprocessor]):
        self.processors = processors

    def postprocess_nodes(self, nodes: List[NodeWithScore], query: str) -> List[NodeWithScore]:
        for processor in self.processors:
            nodes = processor.postprocess_nodes(nodes, query_str=query)
        return nodes
