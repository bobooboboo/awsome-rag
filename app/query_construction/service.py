from typing import Dict, Any, List, Optional

from llama_index.core.schema import NodeWithScore

from app.config.config import DEFAULT_SEARCH_MODE
from app.data_source.vector.factory import VectorStoreFactory
from app.query_construction.routing import QueryRouter


class QueryService:
    """
    查询服务，整合路由和检索功能
    """
    
    def __init__(self, search_mode: Optional[str] = None):
        """
        初始化查询服务
        
        Args:
            search_mode: 检索方式
        """
        self.search_mode = search_mode or DEFAULT_SEARCH_MODE
        # 创建向量存储实例
        self.vector_store = VectorStoreFactory.create()
        # 创建路由器
        self.router = QueryRouter(self.search_mode)
        
    def query(
        self, 
        query_text: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> List[NodeWithScore]:
        """
        执行查询
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件
            params: 其他参数，包括可能的检索模式和特定检索参数
            
        Returns:
            包含节点和相似度分数的NodeWithScore对象列表
        """
        params = params or {}
        
        # 确定检索模式
        mode = self.router.determine_mode(params)
        
        # 合并top_k参数
        if "top_k" in params:
            top_k = int(params["top_k"])
            
        # 提取特定检索模式的参数
        mode_params = {}
        
        # 混合检索的特定参数
        if mode == "hybrid" and "alpha" in params:
            mode_params["alpha"] = float(params["alpha"])
        
        # 执行查询
        results = self.vector_store.search_by_text(
            text=query_text,
            top_k=top_k,
            filters=filters,
            mode=mode,
            **mode_params
        )
        
        return results