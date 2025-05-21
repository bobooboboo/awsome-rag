from typing import List, Dict, Optional, Any

from elasticsearch.helpers.vectorstore import AsyncBM25Strategy
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from app.config.config import ES_CONFIG
from app.data_source.full_text.base import BaseFullTextStore


class ESFullTextStore(BaseFullTextStore):
    """
    Elasticsearch 全文搜索实现，使用llama-index提供的集成
    """

    def __init__(self, **kwargs):
        """
        初始化Elasticsearch全文搜索
        
        Args:
            **kwargs: 搜索引擎连接参数，会覆盖默认配置
        """
        super().__init__()

        # 合并配置
        self.config = {**ES_CONFIG, **kwargs}
        self.index_name = kwargs.get("index_name", self.config.get("index_name"))

        # 初始化LlamaIndex的ElasticsearchStore
        try:
            # 初始化ElasticsearchStore
            self.llama_store = ElasticsearchStore(
                index_name=self.index_name,
                es_url=f"{self.config.get('scheme', 'http')}://{self.config['host']}:{self.config['port']}",
                es_user=self.config.get("username"),
                es_password=self.config.get("password"),
                retrieval_strategy=AsyncBM25Strategy()
            )

            # 使索引可用
            self.initialized = True
        except Exception as e:
            print(f"初始化ES全文搜索引擎失败: {str(e)}")
            raise

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
            filters: 过滤条件，根据元数据过滤
            
        Returns:
            搜索结果列表，每个结果包含id、text、metadata和score
        """
        if not self.initialized or not self.llama_store:
            raise ValueError("全文搜索引擎未初始化")
            
        # 转换过滤条件（如果有）
        metadata_filters = None
        if filters:
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
            
        # 使用ES进行全文搜索
        query_results = self.llama_store.query(
            query_str=text,
            similarity_top_k=top_k,
            filters=metadata_filters,
            **kwargs
        )
        
        # 格式化结果
        formatted_results = []
        for node, score in zip(query_results.nodes, query_results.similarities):
            formatted_results.append({
                "id": node.node_id,
                "text": node.get_content(),
                "metadata": node.metadata,
                "score": score
            })
        
        return formatted_results 