from abc import ABC
from typing import List, Dict, Optional, Any

from llama_index.core.schema import BaseNode
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, FilterOperator


class BaseFullTextStore(ABC):
    """
    全文搜索存储基类，定义全文搜索数据库的接口
    此基类设计完全基于llama-index的概念，使用Node对象作为基本操作单位
    """
    
    def __init__(self):
        """初始化基类属性"""
        # 子类需要初始化这些属性
        self.llama_store = None  # llama-index的存储实例
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
    ) -> List[str]:
        """
        添加数据到全文存储
        
        Args:
            nodes: llama-index的Node对象列表
            
        Returns:
            添加的文档节点ID列表
        """
        if not self.initialized or not self.llama_store:
            raise ValueError("全文存储未初始化")
            
        return self.llama_store.add(nodes=nodes, **kwargs)
    
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
        if not self.initialized or not self.llama_store:
            raise ValueError("全文存储未初始化")

        # 使用llama-index的get_nodes方法批量获取节点
        try:
            # 如果有过滤条件，将其转换为MetadataFilters
            if filters:
                metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
                return self.llama_store.get_nodes(filters=metadata_filters)
                
            # 调用get_nodes方法
            return self.llama_store.get_nodes(node_ids=node_ids)
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
        删除全文存储中的数据
        
        Args:
            node_ids: 要删除的节点ID列表
            filters: 过滤条件，根据元数据过滤。例如：
                   - 精确匹配: {"doc_id": "doc1"}
                   - 列表匹配: {"doc_id": ["doc1", "doc2"]}
                   - 包含匹配: {"content": "%关键词%"}
                   - 空值匹配: {"tag": None}
        """
        if not self.initialized or not self.llama_store:
            raise ValueError("全文存储未初始化")
            
        # 使用llama-index提供的删除方法
        if node_ids:
            # 通过节点ID删除
            self.llama_store.delete_nodes(node_ids=node_ids)
        elif filters:
            # 将字典转换为MetadataFilters
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
            # 通过过滤条件删除
            self.llama_store.delete_nodes(filters=metadata_filters, **kwargs)
        else:
            # 删除所有
            # 注意：存储可能不支持删除所有，需要通过重建集合/表实现
            print("警告: 删除所有数据操作可能不完全支持")
    
    def search_by_text(
        self, 
        text: str, 
        top_k: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        通过文本进行全文搜索
        
        Args:
            text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，根据元数据过滤。例如：
                   - 精确匹配: {"doc_id": "doc1"}
                   - 列表匹配: {"doc_id": ["doc1", "doc2"]}
                   - 包含匹配: {"content": "%关键词%"}
                   - 空值匹配: {"tag": None}
            
        Returns:
            搜索结果列表，每个结果包含id、text、metadata和score
        """
        raise NotImplementedError("子类必须实现search_by_text方法") 