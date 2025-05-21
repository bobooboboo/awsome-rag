from abc import ABC, abstractmethod
from typing import List
from llama_index.core.schema import NodeWithScore, QueryBundle


class BaseProcessor(ABC):
    """
    后置处理器通用接口
    """

    @abstractmethod
    def apply(self, nodes: List[NodeWithScore], query_bundle: QueryBundle) -> List[NodeWithScore]:
        pass