from typing import Optional

from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore as LlamaIndexMilvusStore

from app.config.config import MILVUS_CONFIG, VECTOR_STORE_CONFIG
from app.data_source.vector.base import BaseVectorStore
from app.model.embedding_model import get_embedding_model


class MilvusVectorStore(BaseVectorStore):
    """
    Milvus 向量数据库实现，使用llama-index提供的集成
    """

    def __init__(self, embed_model: Optional[BaseEmbedding] = None, **kwargs):
        """
        初始化Milvus向量数据库
        
        Args:
            embed_model: 嵌入模型实例，如果为None则使用默认模型
            **kwargs: 数据库连接参数，会覆盖默认配置
        """
        super().__init__()

        # 合并配置
        self.config = {**MILVUS_CONFIG, **kwargs}
        self.embed_dim = kwargs.get("embed_dim", VECTOR_STORE_CONFIG["embed_dim"])

        # 设置嵌入模型
        self.embeddings = embed_model or kwargs.get("embed_model") or get_embedding_model()

        # 构建URI，如果有用户名和密码则嵌入到URI中
        host = self.config["host"]
        port = self.config["port"]
        username = self.config.get("username", "")
        password = self.config.get("password", "")

        # 如果有用户名和密码，将它们嵌入到URI中
        if username and password:
            uri = f"http://{username}:{password}@{host}:{port}"
        else:
            uri = f"http://{host}:{port}"

        self.llama_vector_store = LlamaIndexMilvusStore(
            uri=uri,
            collection_name=self.config["collection"],
            dim=self.embed_dim,
            overwrite=self.config.get("overwrite", False),
            embed_model=self.embeddings,
            doc_id_field="doc_id",

        )

        # 使集合可用
        self.initialized = True
