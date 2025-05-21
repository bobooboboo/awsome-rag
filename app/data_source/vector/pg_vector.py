from typing import Optional

from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.postgres import PGVectorStore as LlamaIndexPGVectorStore

from app.config.config import PG_CONFIG, VECTOR_STORE_CONFIG
from app.data_source.vector.base import BaseVectorStore
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
        )

        # 使集合/表格可用
        self.initialized = True