from typing import List, Dict, Optional, Any

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore

from app.config.config import PG_CONFIG
from app.data_source.full_text.base import BaseFullTextStore


class PGFullTextStore(BaseFullTextStore):
    """
    PostgreSQL 全文搜索实现，将PG作为全文搜索引擎使用
    注意：这里使用PG的全文搜索功能，结合向量搜索
    """

    def __init__(self, **kwargs):
        """
        初始化PostgreSQL全文搜索
        
        Args:
            **kwargs: 搜索引擎连接参数，会覆盖默认配置
        """
        super().__init__()

        # 合并配置
        self.config = {**PG_CONFIG, **kwargs}
        self.table_name = kwargs.get("table_name", self.config.get("table_name", "fulltext_store"))

        # 初始化PostgreSQL
        try:
            self.llama_store = PGVectorStore.from_params(
                database=self.config["database"],
                host=self.config["host"],
                password=self.config["password"],
                port=self.config["port"],
                user=self.config["user"],
                table_name=f"{self.table_name}_fulltext",

            )

            self.index = VectorStoreIndex.from_vector_store(self.llama_store)

            # 使表可用
            self.initialized = True
        except Exception as e:
            print(f"初始化PostgreSQL全文搜索引擎失败: {str(e)}")
            raise

    def search_by_text(
        self, 
        text: str, 
        top_k: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid_search: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        通过文本进行全文搜索
        
        Args:
            text: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件，根据元数据过滤
            use_hybrid_search: 是否使用混合搜索(结合向量搜索和全文搜索)
            
        Returns:
            搜索结果列表，每个结果包含id、text、metadata和score
        """
        if not self.initialized or not self.llama_store:
            raise ValueError("全文搜索引擎未初始化")
            
        # 转换过滤条件（如果有）
        metadata_filters = None
        if filters:
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)

        if use_hybrid_search and hasattr(self.llama_store, "hybrid_search"):
            # 使用PG的混合搜索功能(向量+全文)
            try:
                query_results = self.llama_store.hybrid_search(
                    query_str=text,
                    k=top_k,
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
            except Exception as e:
                print(f"混合搜索失败，回退到向量搜索: {e}")
                # 如果混合搜索失败，回退到向量搜索
                pass
        
        # 获取文本嵌入进行向量搜索
        embedding = self.embed_model.get_text_embedding(text)
            
        # 使用PG进行向量相似度搜索
        from llama_index.core.vector_stores import VectorStoreQuery
        query = VectorStoreQuery(
            query_embedding=embedding,
            similarity_top_k=top_k,
            filters=metadata_filters,
        )
        
        query_results = self.llama_store.query(query, **kwargs)
        
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