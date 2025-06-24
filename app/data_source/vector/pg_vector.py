import os
from typing import Optional, Dict, Any, List

from fsspec.implementations.local import LocalFileSystem
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.core.schema import NodeWithScore
from llama_index.core.storage.docstore.types import DEFAULT_PERSIST_FNAME
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.vector_stores.postgres import PGVectorStore as LlamaIndexPGVectorStore

from app.config.config import PG_CONFIG, VECTOR_STORE_CONFIG, STORING_CONFIG
from app.data_source.vector.base import BaseVectorStore
from app.model.chat_model import get_chat_model
from app.model.embedding_model import get_embedding_model


class PGVectorStore(BaseVectorStore):
    """
    PostgreSQL 向量数据库实现，使用llama-index提供的集成
    """

    def __init__(self, embed_model: Optional[BaseEmbedding] = None, **kwargs):
        """
        初始化PostgreSQL向量数据库
        
        Args:
            embed_model: 嵌入模型实例，如果为None则使用默认模型
            **kwargs: 数据库连接参数，会覆盖默认配置
        """
        super().__init__()

        # 合并配置
        self.db_config = {**PG_CONFIG, **kwargs}
        self.table_name = kwargs.get("table_name", self.db_config.get("table_name"))
        self.embed_dim = kwargs.get("embed_dim", VECTOR_STORE_CONFIG["embed_dim"])

        # 设置嵌入模型
        self.embed_model = embed_model or kwargs.get("embed_model") or get_embedding_model()

        # 初始化LlamaIndex的PGVectorStore
        self.llama_vector_store = LlamaIndexPGVectorStore.from_params(
            database=self.db_config["database"],
            host=self.db_config["host"],
            password=self.db_config["password"],
            port=self.db_config["port"],
            user=self.db_config["user"],
            table_name=self.table_name,
            embed_dim=self.embed_dim,
            text_search_config="english",
            hybrid_search=True,
        )

        persist_dir_ = STORING_CONFIG["persist_dir"]

        doc_store_path = os.path.join(persist_dir_, DEFAULT_PERSIST_FNAME)

        if os.path.exists(doc_store_path):
            self.storage_context = StorageContext.from_defaults(vector_store=self.llama_vector_store,
                                                                persist_dir=persist_dir_, fs=LocalFileSystem())

            self.vector_store_index = VectorStoreIndex(nodes=[], storage_context=self.storage_context,
                                                       embed_model=self.embed_model,
                                                       show_progress=True)

        else:
            self.storage_context = StorageContext.from_defaults(vector_store=self.llama_vector_store,
                                                                fs=LocalFileSystem())

            self.vector_store_index = VectorStoreIndex(nodes=[], storage_context=self.storage_context,
                                                       embed_model=self.embed_model,
                                                       show_progress=True)

            # 首次创建后保存
            self.storage_context.persist(persist_dir_)

        self.llm = get_chat_model().llm

        # 使集合/表格可用
        self.initialized = True

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

        if not mode == "hybrid":
            return super().search_by_text(text, top_k=top_k, filters=filters, mode=mode, **kwargs)

        if not self.initialized or not self.vector_store_index:
            raise ValueError("向量存储未初始化")

        # 构建查询参数
        if filters:
            # 将字典转换为MetadataFilters
            metadata_filters = self._convert_filter_dict_to_metadata_filters(filters)
        else:
            metadata_filters = None

        vector_retriever = self.vector_store_index.as_retriever(
            vector_store_query_mode=VectorStoreQueryMode.DEFAULT,
            similarity_top_k=top_k,
            filters=metadata_filters,
        )

        text_retriever = self.vector_store_index.as_retriever(
            vector_store_query_mode=VectorStoreQueryMode.SPARSE,
            similarity_top_k=top_k,
            filters=metadata_filters,
        )

        retriever = QueryFusionRetriever(
            [vector_retriever, text_retriever],
            similarity_top_k=5,
            num_queries=1,
            mode=FUSION_MODES.RECIPROCAL_RANK,
            use_async=False,
            llm=self.llm
        )

        return retriever.retrieve(text)
