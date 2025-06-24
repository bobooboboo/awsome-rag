from abc import ABC
from typing import List, Dict, Optional, Any

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import BaseNode, NodeWithScore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, FilterOperator
from llama_index.core.vector_stores.types import VectorStoreQueryMode


class BaseVectorStore(ABC):
    """
    向量存储基类，定义向量数据库的接口
    此基类设计完全基于llama-index的概念，使用Node对象作为基本操作单位
    """

    def __init__(self):
        """初始化基类属性"""
        # 子类需要初始化这些属性
        self.vector_store_index: Optional[VectorStoreIndex] = None  # llama-index的向量索引
        self.initialized: bool = False  # 初始化状态标志

    @staticmethod
    def _convert_filter_dict_to_metadata_filters(filter_dict: Dict[str, Any]) -> MetadataFilters:
        """
        将字典类型的过滤条件转换为MetadataFilters对象
        
        Args:
            filter_dict: 字典类型的过滤条件
            
        Returns:
            MetadataFilters对象
        """
        filters = []

        for key, value in filter_dict.items():
            # 根据值类型选择合适的操作符
            if isinstance(value, list):
                # 列表类型使用IN操作符
                filters.append(ExactMatchFilter(key=key, value=value, operator=FilterOperator.IN))
            elif isinstance(value, str) and value.startswith("%") and value.endswith("%"):
                # 包含模式使用CONTAINS操作符
                # 移除前后的%通配符
                clean_value = value[1:-1]
                filters.append(ExactMatchFilter(key=key, value=clean_value, operator=FilterOperator.CONTAINS))
            elif value is None:
                # 空值使用IS_EMPTY操作符
                filters.append(ExactMatchFilter(key=key, value=None, operator=FilterOperator.IS_EMPTY))
            else:
                # 默认使用相等操作符
                filters.append(ExactMatchFilter(key=key, value=value, operator=FilterOperator.EQ))

        return MetadataFilters(filters=filters)

    def add_data(
            self,
            nodes: List[BaseNode],
            **kwargs
    ) -> None:
        """
        添加数据到向量存储
        
        Args:
            nodes: llama-index的Node对象列表
            
        Returns:
            添加的文档节点ID列表
        """
        if not self.initialized or not self.vector_store_index:
            raise ValueError("向量存储未初始化")

        self.vector_store_index.insert_nodes(nodes, **kwargs)

    def get_data(
            self,
            node_ids: Optional[List[str]] = None,
            filters: Optional[Dict[str, Any]] = None,
    ) -> List[BaseNode]:
        """
        获取存储的数据
        
        Args:
            node_ids: 要获取的节点ID列表
            filters: 过滤条件，用于在没有指定node_ids时按条件获取节点
            
        Returns:
            llama-index的Node对象列表
        """
        if not self.initialized or not self.vector_store_index:
            raise ValueError("向量存储未初始化")

        # 使用llama-index的get_nodes方法批量获取节点
        try:
            # 如果有过滤条件，将其转换为MetadataFilters
            if filters:
                metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
                return [node_with_score.node for node_with_score in
                        self.vector_store_index.as_retriever(filters=metadata_filters).retrieve(str_or_query_bundle="")]

            # 调用get_nodes方法
            return [node_with_score.node for node_with_score in
                    self.vector_store_index.as_retriever(node_ids=node_ids).retrieve(str_or_query_bundle="")]
        except Exception as e:
            print(f"获取节点失败: {e}")
            return []

    def delete_data(
            self,
            node_ids: Optional[List[str]] = None,
            filters: Optional[Dict[str, Any]] = None,
            **kwargs
    ) -> None:
        """
        删除向量存储中的数据
        
        Args:
            node_ids: 要删除的节点ID列表
            filters: 过滤条件，根据元数据过滤。例如：
                   - 精确匹配: {"doc_id": "doc1"}
                   - 列表匹配: {"doc_id": ["doc1", "doc2"]}
                   - 包含匹配: {"content": "%关键词%"}
                   - 空值匹配: {"tag": None}
        """
        if not self.initialized or not self.vector_store_index:
            raise ValueError("向量存储未初始化")

        # 使用llama-index提供的删除方法
        if node_ids:
            # 通过节点ID删除
            self.vector_store_index.delete_nodes(node_ids=node_ids, **kwargs)
        elif filters:
            # 将字典转换为MetadataFilters
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
            # 通过过滤条件删除
            self.vector_store_index.delete_nodes(node_ids=[], filters=metadata_filters, **kwargs)
        else:
            # 删除所有
            # 注意：向量存储可能不支持删除所有，需要通过重建集合/表实现
            print("警告: 删除所有数据操作可能不完全支持")

    def search_by_text(
            self,
            text: str,
            top_k: int = 5,
            filters: Optional[Dict[str, Any]] = None,
            mode: str = "vector",  # 支持各种检索模式
            **kwargs
    ) -> List[NodeWithScore]:
        """
        通过文本搜索，支持多种检索模式
        
        Args:
            text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，根据元数据过滤
            mode: 检索模式，支持以下模式：
                - vector: 向量检索 (DEFAULT)
                - text: 全文检索 (TEXT_SEARCH)
                - hybrid: 混合检索 (HYBRID)
                - sparse: 稀疏向量检索 (SPARSE)
                - semantic_hybrid: 语义混合检索 (SEMANTIC_HYBRID)
            **kwargs: 额外参数，例如混合检索的alpha参数
            
        Returns:
            包含节点和相似度分数的NodeWithScore对象列表
        """
        if not self.initialized or not self.vector_store_index:
            raise ValueError("向量存储未初始化")

        # 构建查询参数
        if filters:
            # 将字典转换为MetadataFilters
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
        else:
            metadata_filters = None

        # 模式映射
        mode_mapping = {
            "vector": VectorStoreQueryMode.DEFAULT,
            "text": VectorStoreQueryMode.TEXT_SEARCH,
            "hybrid": VectorStoreQueryMode.HYBRID,
            "sparse": VectorStoreQueryMode.SPARSE,
            "semantic_hybrid": VectorStoreQueryMode.SEMANTIC_HYBRID
        }

        # 获取查询模式
        query_mode = mode_mapping.get(mode.lower(), VectorStoreQueryMode.DEFAULT)

        retriever = self.vector_store_index.as_retriever(vector_store_query_mode=query_mode, filters=metadata_filters,
                                                         alpha=kwargs.get("alpha",
                                                                          0.5) if query_mode == VectorStoreQueryMode.HYBRID else None,
                                                         similarity_top_k=top_k)
        return retriever.retrieve(text)
